"""Regera os 6 cortes de um job (ASS + render + concat) e re-envia ao Drive.

Uso:
    python3 rebuild.py output/<job-id> [--with-captions]

Aproveita transcript.json + cuts.json + source.mp4 já existentes na pasta,
então pula a transcrição (custosa). Útil para refazer cortes após mudar
estilo de legenda, fonte, tamanho, etc.

Com --with-captions, gera (ou regenera) as legendas de Instagram via OpenAI
e inclui `instagram.md` + `corte-XX-instagram.txt` no upload.

Substitui os arquivos antigos no Drive (apaga IDs registrados em
drive-ids.json antes do novo upload).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from pipeline import probe as _probe
from pipeline import ass_builder as _ass
from pipeline import outro as _outro
from pipeline import render as _render
from pipeline import concat as _concat
from pipeline import drive as _drive
from pipeline import instagram as _instagram
from pipeline.transcribe import Word


ROOT = Path(__file__).resolve().parent
ICON_PATH = ROOT / "icone.png"
LOGO_PATH = ROOT / "logo.png"


def _log(stage: str, msg: str) -> None:
    print(f"[{stage}] {msg}")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    with_captions = "--with-captions" in flags
    job_dir = Path(args[0]).resolve()
    if not job_dir.is_dir():
        print(f"Diretório não encontrado: {job_dir}", file=sys.stderr)
        return 2

    source = job_dir / "source.mp4"
    transcript_path = job_dir / "transcript.json"
    cuts_path = job_dir / "cuts.json"
    for p in (source, transcript_path, cuts_path):
        if not p.exists():
            print(f"Faltando: {p}", file=sys.stderr)
            return 2

    info = _probe.probe(str(source))
    _log("probe", f"{info.width}x{info.height} @ {info.fps:.2f}fps")

    raw_words = json.loads(transcript_path.read_text())
    words = [Word(start=w["start"], end=w["end"], text=w["text"]) for w in raw_words]
    cuts_payload = json.loads(cuts_path.read_text())
    cuts = cuts_payload["cuts"]

    # 1. Rebuild ASS
    ass_paths: list[Path] = []
    for c in cuts:
        ass_path = job_dir / f"corte-{c['idx']:02d}.ass"
        cut_words = [w for w in words if w.start >= c["start"] - 0.01 and w.end <= c["end"] + 0.5]
        _ass.build_ass(cut_words, c["start"], str(ass_path), width=info.width, height=info.height)
        ass_paths.append(ass_path)
        _log("ass", f"corte-{c['idx']:02d}.ass ({len(cut_words)} palavras)")

    # 2. Outro
    outro_path = job_dir / "outro.mp4"
    _log("outro", "Regerando outro.mp4")
    _outro.build_outro(str(LOGO_PATH), str(outro_path), width=info.width, height=info.height, fps=info.fps)

    # 3. Render + 4. Concat
    final_paths: list[Path] = []
    for i, c in enumerate(cuts):
        content_path = job_dir / f"corte-{c['idx']:02d}-content.mp4"
        final_path = job_dir / f"corte-{c['idx']:02d}-{c['slug']}.mp4"
        _log("render", f"corte {c['idx']}/6: {c['title']}")
        _render.render_cut(
            str(source), str(ass_paths[i]), str(ICON_PATH), str(content_path),
            start=c["start"], end=c["end"], width=info.width, height=info.height, fps=info.fps,
            on_event=None, cut_idx=i, cut_total=len(cuts),
        )
        _log("concat", f"corte-{c['idx']:02d}-{c['slug']}.mp4")
        _concat.concat(str(content_path), str(outro_path), str(final_path))
        content_path.unlink(missing_ok=True)
        final_paths.append(final_path)

    # 4.5 Instagram captions (opt-in)
    ig_posts = None
    if with_captions:
        _log("instagram", "Gerando legendas Instagram")
        ig_input = [
            {
                "idx": c["idx"],
                "title": c.get("title"),
                "rationale": c.get("rationale"),
                "text": " ".join(w.text for w in words if w.start >= c["start"] - 0.01 and w.end <= c["end"] + 0.5),
            }
            for c in cuts
        ]
        ig_posts = _instagram.generate(ig_input, lambda ev: _log(ev.get("stage", ""), ev.get("message", "")) if ev.get("type") == "log" else None)
        if ig_posts is None:
            _log("instagram", "Falha — legendas não geradas (sigo sem elas)")
        else:
            _instagram.write_files(ig_posts, ig_input, str(job_dir))
            _log("instagram", "instagram.md + 6 corte-XX-instagram.txt gerados")

    # 5. Delete old Drive files (if drive-ids.json present)
    drive_ids_path = job_dir / "drive-ids.json"
    if drive_ids_path.exists():
        try:
            old_ids = json.loads(drive_ids_path.read_text())
            service = _drive._build_service()
            for entry in old_ids:
                fid = entry.get("id")
                if not fid:
                    continue
                try:
                    service.files().delete(fileId=fid).execute()
                    _log("drive", f"deletado antigo: {entry.get('name')} ({fid})")
                except Exception as e:
                    _log("drive", f"falha ao deletar {fid}: {e}")
        except Exception as e:
            _log("drive", f"falha lendo drive-ids.json: {e}")

    # 6. Re-upload
    def on_event(ev: dict) -> None:
        t = ev.get("type")
        if t == "log":
            _log(ev.get("stage", ""), ev.get("message", ""))
        elif t == "progress":
            sub = ev.get("sub_fraction")
            idx = ev.get("file_idx")
            total = ev.get("file_total")
            if idx and total and sub is not None:
                print(f"  → arquivo {idx}/{total}: {sub * 100:5.1f}%", end="\r")

    upload_list: list = [(str(p), p.name) for p in final_paths]
    if with_captions and ig_posts is not None:
        ig_md = job_dir / "instagram.md"
        if ig_md.exists():
            upload_list.append((str(ig_md), ig_md.name))
        for p in ig_posts:
            fname = f"corte-{p.idx:02d}-instagram.txt"
            local = job_dir / fname
            if local.exists():
                upload_list.append((str(local), fname))

    try:
        results = _drive.upload_all(upload_list, str(job_dir), on_event)
    except _drive.DriveSetupError as e:
        print(f"\nFalha Drive: {e}", file=sys.stderr)
        return 1

    print()
    print(f"\n✓ Rebuild + upload concluído ({len(results)} arquivos):")
    for r in results:
        print(f"  - {r['name']} → {r['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
