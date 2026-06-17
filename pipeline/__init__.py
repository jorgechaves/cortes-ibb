from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import traceback
import unicodedata
from dataclasses import asdict
from pathlib import Path
from typing import Callable


def slugify(text: str, max_len: int = 40) -> str:
    """Return a filesystem-safe slug from text (NFD, lowercase, hyphens, max_len)."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_len].rstrip("-")

from . import probe as _probe
from . import transcribe as _transcribe
from . import selector as _selector
from . import semantic_selector as _semantic
from . import ass_builder as _ass
from . import outro as _outro
from . import render as _render
from . import concat as _concat
from . import drive as _drive
from . import instagram as _instagram


# Stage weights (must sum to ~100). Used by app.py for global progress bar.
STAGE_WEIGHTS = {
    "upload": 5,
    "probe": 2,
    "transcribe": 25,
    "select": 3,
    "ass": 5,
    "outro": 5,
    "render": 35,
    "concat": 5,
    "instagram": 5,
    "drive": 10,
}

TRANSCRIPT_STAGE_WEIGHTS = {
    "upload": 5,
    "probe": 10,
    "transcribe": 75,
    "drive": 10,
}


def _stage_offset(stage: str) -> int:
    """Cumulative percent at the *start* of `stage`."""
    total = 0
    for s, w in STAGE_WEIGHTS.items():
        if s == stage:
            return total
        total += w
    return total


def _emit_global(on_event: Callable[[dict], None], event: dict) -> None:
    """Convert a stage-local event to a global percent and forward."""
    stage = event.get("stage")
    if stage and stage in STAGE_WEIGHTS:
        off = _stage_offset(stage)
        w = STAGE_WEIGHTS[stage]
        if event.get("type") == "progress":
            frac = max(0.0, min(1.0, event.get("fraction", 0.0)))
            event["percent"] = round(off + w * frac, 1)
        elif event.get("type") == "stage":
            event["percent"] = round(off, 1)
    on_event(event)


def run(
    source: str,
    icon: str,
    logo: str,
    out_dir: str,
    on_event: Callable[[dict], None],
    *,
    with_subtitles: bool = True,
) -> dict:
    """Execute the full pipeline. Returns a result dict with metadata."""
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    titulo_txt = out_dir_p / "titulo.txt"
    titulo_slug = slugify(titulo_txt.read_text(encoding="utf-8")) if titulo_txt.exists() else ""

    def emit(ev: dict) -> None:
        _emit_global(on_event, ev)

    emit({"type": "stage", "stage": "probe", "message": "Inspecionando vídeo"})
    info = _probe.probe(source)
    emit({"type": "log", "stage": "probe", "message": f"{info.width}x{info.height} @ {info.fps:.2f}fps, {info.duration:.0f}s"})
    emit({"type": "progress", "stage": "probe", "fraction": 1.0})

    emit({"type": "stage", "stage": "transcribe", "message": "Transcrevendo áudio"})
    words = _transcribe.transcribe(source, out_dir, info.duration, emit)
    emit({"type": "progress", "stage": "transcribe", "fraction": 1.0})

    emit({"type": "stage", "stage": "select", "message": "Selecionando 10 cortes"})
    candidates = _selector.gather_candidates(words)
    if len(candidates) < 10:
        emit({"type": "log", "stage": "select", "message": f"Apenas {len(candidates)} candidatos com 60s mín; tentando com 45s"})
        candidates = _selector.gather_candidates(words, target_min=45.0)
    emit({"type": "log", "stage": "select", "message": f"{len(candidates)} candidatos gerados"})

    selection_mode = "semantic"
    fallback_reason: str | None = None
    model_used: str | None = None
    cuts: list[_selector.HeuristicCut]
    try:
        cuts = _semantic.choose(candidates, emit)
        model_used = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    except _semantic.SemanticSelectionFailure as e:
        selection_mode = "heuristic"
        fallback_reason = str(e)
        emit({"type": "log", "stage": "select", "message": f"Fallback heurístico: {e}"})
        cuts = _selector.pick_n_heuristic(candidates)

    if len(cuts) == 0:
        emit({"type": "error", "stage": "select", "message": "Nenhum corte encontrado. Vídeo inválido ou sem fala."})
        raise RuntimeError("no cuts available")
    if len(cuts) < 10:
        emit({"type": "log", "stage": "select", "message": f"Aviso: apenas {len(cuts)} cortes encontrados (vídeo curto ou poucas pausas). Continuando com {len(cuts)}."})


    cuts_json = {
        "selection_mode": selection_mode,
        "model": model_used,
        "fallback_reason": fallback_reason,
        "cuts": [
            {
                "idx": c.idx,
                "start": round(c.start, 3),
                "end": round(c.end, 3),
                "slug": c.slug,
                "title": c.title,
                "rationale": c.rationale,
                "selection_mode": selection_mode,
            }
            for c in cuts
        ],
    }
    (out_dir_p / "cuts.json").write_text(json.dumps(cuts_json, ensure_ascii=False, indent=2))
    emit({"type": "progress", "stage": "select", "fraction": 1.0})

    emit({"type": "stage", "stage": "ass", "message": "Gerando legendas ASS"})
    ass_paths: list[Path | None] = []
    if with_subtitles:
        for i, c in enumerate(cuts):
            ass_path = out_dir_p / f"corte-{c.idx:02d}.ass"
            cut_words = [w for w in words if w.start >= c.start - 0.01 and w.end <= c.end + 0.5]
            _ass.build_ass(cut_words, c.start, str(ass_path), width=info.width, height=info.height)
            ass_paths.append(ass_path)
            emit({"type": "progress", "stage": "ass", "fraction": (i + 1) / len(cuts)})
    else:
        ass_paths = [None] * len(cuts)
        emit({"type": "log", "stage": "ass", "message": "Legendas desativadas pelo usuário"})
    emit({"type": "progress", "stage": "ass", "fraction": 1.0})

    emit({"type": "stage", "stage": "outro", "message": "Renderizando cartão final com logo"})
    outro_path = out_dir_p / "outro.mp4"
    _outro.build_outro(logo, str(outro_path), width=info.width, height=info.height, fps=info.fps)
    emit({"type": "progress", "stage": "outro", "fraction": 1.0})

    emit({"type": "stage", "stage": "render", "message": f"Renderizando os {len(cuts)} cortes"})
    content_paths: list[Path] = []
    for i, c in enumerate(cuts):
        content_path = out_dir_p / f"corte-{c.idx:02d}-content.mp4"
        emit({"type": "log", "stage": "render", "message": f"Corte {c.idx}/{len(cuts)} — {c.title}"})
        _render.render_cut(
            source, str(ass_paths[i]) if ass_paths[i] is not None else None, icon, str(content_path),
            start=c.start, end=c.end, width=info.width, height=info.height, fps=info.fps,
            on_event=emit, cut_idx=i, cut_total=len(cuts),
        )
        content_paths.append(content_path)
    emit({"type": "progress", "stage": "render", "fraction": 1.0})

    emit({"type": "stage", "stage": "concat", "message": "Anexando cartão final"})
    final_paths: list[tuple[Path, str]] = []  # (path, drive_name)
    for i, c in enumerate(cuts):
        prefix = f"{titulo_slug}-" if titulo_slug else ""
        final_path = out_dir_p / f"{prefix}corte-{c.idx:02d}-{c.slug}.mp4"
        _concat.concat(str(content_paths[i]), str(outro_path), str(final_path))
        final_paths.append((final_path, final_path.name))
        emit({"type": "progress", "stage": "concat", "fraction": (i + 1) / len(cuts)})

    # cleanup intermediates
    for p in content_paths:
        try:
            p.unlink()
        except OSError:
            pass
    emit({"type": "progress", "stage": "concat", "fraction": 1.0})

    # ---- Instagram captions ----
    emit({"type": "stage", "stage": "instagram", "message": "Gerando legendas Instagram"})
    ig_cuts_input = [
        {
            "idx": c.idx,
            "title": c.title,
            "rationale": c.rationale,
            "text": " ".join(w.text for w in words if w.start >= c.start - 0.01 and w.end <= c.end + 0.5),
        }
        for c in cuts
    ]
    ig_posts = _instagram.generate(ig_cuts_input, emit)
    instagram_skipped = ig_posts is None
    instagram_skip_reason: str | None = None
    if instagram_skipped:
        if not os.environ.get("OPENAI_API_KEY"):
            instagram_skip_reason = "missing_api_key"
        elif os.environ.get("DISABLE_INSTAGRAM"):
            instagram_skip_reason = "disabled_by_env"
        else:
            instagram_skip_reason = "api_or_validation_failure"
    else:
        _instagram.write_files(ig_posts, ig_cuts_input, out_dir)
    emit({"type": "progress", "stage": "instagram", "fraction": 1.0})

    emit({"type": "stage", "stage": "drive", "message": "Enviando para Google Drive"})
    upload_list: list[tuple[str, str]] = [(str(p), name) for p, name in final_paths]
    transcript_txt_path = out_dir_p / "transcript.txt"
    if transcript_txt_path.exists():
        upload_list.append((str(transcript_txt_path), "transcript.txt"))
    if not instagram_skipped:
        upload_list.append((str(out_dir_p / "instagram.md"), "instagram.md"))
        for p in ig_posts:
            fname = f"corte-{p.idx:02d}-instagram.txt"
            upload_list.append((str(out_dir_p / fname), fname))

    drive_results: list[dict] = []
    drive_error: str | None = None
    try:
        drive_results = _drive.upload_all(upload_list, out_dir, emit)
    except _drive.DriveSetupError as e:
        drive_error = str(e)
        emit({"type": "log", "stage": "drive", "message": f"Drive desativado: {e}"})
    except Exception as e:
        drive_error = f"{type(e).__name__}: {e}"
        emit({"type": "log", "stage": "drive", "message": f"Upload falhou: {drive_error}"})
    emit({"type": "progress", "stage": "drive", "fraction": 1.0})

    # Build final result + report
    drive_by_name = {r["name"]: r for r in drive_results}
    ig_by_idx = {p.idx: p for p in (ig_posts or [])}
    final = []
    for c, (p, name) in zip(cuts, final_paths):
        drive = drive_by_name.get(name)
        ig = ig_by_idx.get(c.idx)
        final.append({
            "idx": c.idx,
            "title": c.title,
            "rationale": c.rationale,
            "slug": c.slug,
            "file": name,
            "local_path": str(p),
            "duration": round(c.end - c.start + 2.0, 2),  # +2s outro
            "drive_id": drive["id"] if drive else None,
            "drive_url": drive["url"] if drive else None,
            "instagram": _instagram.post_to_dict(ig) if ig else None,
        })

    transcript_drive = drive_by_name.get("transcript.txt")
    result = {
        "job_id": out_dir_p.name,
        "selection_mode": selection_mode,
        "fallback_reason": fallback_reason,
        "model": model_used,
        "drive_error": drive_error,
        "instagram_skipped": instagram_skipped,
        "instagram_skip_reason": instagram_skip_reason,
        "out_dir": str(out_dir_p),
        "transcript_local_path": str(transcript_txt_path) if transcript_txt_path.exists() else None,
        "transcript_drive_url": transcript_drive["url"] if transcript_drive else None,
        "cuts": final,
    }

    # Overwrite cuts.json with the full payload (selection + instagram).
    (out_dir_p / "cuts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    _write_report(out_dir_p, result)
    emit({"type": "done", "stage": "done", "percent": 100.0, "data": result})
    return result


def _write_report(out_dir: Path, result: dict) -> None:
    lines = [f"# Relatório do job\n", f"- Pasta: `{out_dir}`\n"]
    lines.append(f"- Modo de seleção: **{result['selection_mode']}**")
    if result["model"]:
        lines.append(f"- Modelo: `{result['model']}`")
    if result["fallback_reason"]:
        lines.append(f"- Motivo do fallback: {result['fallback_reason']}")
    if result["drive_error"]:
        lines.append(f"- Erro no upload Drive: {result['drive_error']}")
    if result.get("instagram_skipped"):
        lines.append(f"- Legendas Instagram puladas: {result.get('instagram_skip_reason')}")
    if result.get("transcript_drive_url"):
        lines.append(f"- Transcrição: <{result['transcript_drive_url']}>")
    elif result.get("transcript_local_path"):
        lines.append(f"- Transcrição local: `{result['transcript_local_path']}`")
    lines.append("\n## Cortes\n")
    for c in result["cuts"]:
        lines.append(f"### {c['idx']}. {c['title']}")
        if c.get("rationale"):
            lines.append(f"_{c['rationale']}_\n")
        lines.append(f"- Arquivo: `{c['file']}` ({c['duration']}s)")
        if c.get("drive_url"):
            lines.append(f"- Drive: <{c['drive_url']}>")
        ig = c.get("instagram")
        if ig:
            lines.append(f"- **Instagram**")
            lines.append(f"  - HOOK: {ig['hook']}")
            lines.append(f"  - CAPTION: {ig['caption']}")
            lines.append(f"  - CTA: {ig['cta']}")
            lines.append(f"  - HASHTAGS: `{' '.join(ig['hashtags'])}`")
        lines.append("")
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run_transcript_only(
    source: str,
    out_dir: str,
    on_event: Callable[[dict], None],
) -> dict:
    """Execute only probe + transcribe + drive. Returns a result dict with transcript paths."""
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    def emit(ev: dict) -> None:
        stage = ev.get("stage")
        if stage and stage in TRANSCRIPT_STAGE_WEIGHTS:
            off = 0
            for s, w in TRANSCRIPT_STAGE_WEIGHTS.items():
                if s == stage:
                    break
                off += w
            w = TRANSCRIPT_STAGE_WEIGHTS[stage]
            if ev.get("type") == "progress":
                frac = max(0.0, min(1.0, ev.get("fraction", 0.0)))
                ev["percent"] = round(off + w * frac, 1)
            elif ev.get("type") == "stage":
                ev["percent"] = round(off, 1)
        on_event(ev)

    emit({"type": "stage", "stage": "probe", "message": "Inspecionando vídeo"})
    info = _probe.probe(source)
    emit({"type": "log", "stage": "probe", "message": f"{info.width}x{info.height} @ {info.fps:.2f}fps, {info.duration:.0f}s"})
    emit({"type": "progress", "stage": "probe", "fraction": 1.0})

    emit({"type": "stage", "stage": "transcribe", "message": "Transcrevendo áudio"})
    _transcribe.transcribe(source, out_dir, info.duration, emit)
    emit({"type": "progress", "stage": "transcribe", "fraction": 1.0})

    transcript_txt_path = out_dir_p / "transcript.txt"

    emit({"type": "stage", "stage": "drive", "message": "Enviando para Google Drive"})
    upload_list: list[tuple[str, str]] = []
    if transcript_txt_path.exists():
        upload_list.append((str(transcript_txt_path), "transcript.txt"))

    drive_results: list[dict] = []
    drive_error: str | None = None
    try:
        drive_results = _drive.upload_all(upload_list, out_dir, emit)
    except _drive.DriveSetupError as e:
        drive_error = str(e)
        emit({"type": "log", "stage": "drive", "message": f"Drive desativado: {e}"})
    except Exception as e:
        drive_error = f"{type(e).__name__}: {e}"
        emit({"type": "log", "stage": "drive", "message": f"Upload falhou: {drive_error}"})
    emit({"type": "progress", "stage": "drive", "fraction": 1.0})

    drive_by_name = {r["name"]: r for r in drive_results}
    transcript_drive = drive_by_name.get("transcript.txt")

    result = {
        "job_id": out_dir_p.name,
        "mode": "transcript",
        "drive_error": drive_error,
        "out_dir": str(out_dir_p),
        "transcript_local_path": str(transcript_txt_path) if transcript_txt_path.exists() else None,
        "transcript_drive_url": transcript_drive["url"] if transcript_drive else None,
        "cuts": [],
    }

    emit({"type": "done", "stage": "done", "percent": 100.0, "data": result})
    return result


def check_environment() -> list[str]:
    """Return list of error messages (empty if OK). Used by app.py at startup."""
    errors: list[str] = []
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg não encontrado no PATH (instale: brew install ffmpeg)")
    if not shutil.which("ffprobe"):
        errors.append("ffprobe não encontrado no PATH")
    return errors


def warnings() -> list[str]:
    """Soft warnings shown in the UI banner."""
    warns: list[str] = []
    if not os.environ.get("OPENAI_API_KEY"):
        warns.append("OPENAI_API_KEY não definida — seleção semântica desativada (fallback heurístico)")
    try:
        out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
        if "antique olive" not in out.lower():
            warns.append("Fonte 'Antique Olive' não encontrada — legendas usarão Arial Black")
    except FileNotFoundError:
        pass
    return warns
