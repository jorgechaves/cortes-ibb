"""Re-envia para o Google Drive os 6 cortes de um job já renderizado.

Uso:
    python3 reupload.py output/<job-id> [--with-captions]

Útil quando o pipeline travou na etapa Drive (ex.: OAuth não completou na
primeira vez). Os MP4 `corte-*.mp4` da pasta são enviados para a subpasta
`videos-ibb/[YYYY-MM-DD]` no Drive autenticado.

Com --with-captions, inclui `instagram.md` + `corte-XX-instagram.txt` no
upload (gera essas legendas via OpenAI se ainda não existirem).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from pipeline import drive
from pipeline import instagram as _instagram
from pipeline.transcribe import Word


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

    mp4s = sorted(p for p in job_dir.glob("corte-*.mp4") if not p.name.endswith("-content.mp4"))
    if len(mp4s) != 6:
        print(f"Esperava 6 MP4s em {job_dir}, encontrei {len(mp4s)}", file=sys.stderr)
        for p in mp4s:
            print(f"  - {p.name}")
        return 2

    upload_list: list = [(str(p), p.name) for p in mp4s]

    if with_captions:
        ig_md = job_dir / "instagram.md"
        txts = sorted(job_dir.glob("corte-*-instagram.txt"))
        if not ig_md.exists() or len(txts) != 6:
            print("Gerando legendas Instagram (faltam arquivos)...")
            cuts_path = job_dir / "cuts.json"
            transcript_path = job_dir / "transcript.json"
            if not cuts_path.exists() or not transcript_path.exists():
                print("Faltando cuts.json ou transcript.json — não dá pra gerar legendas.", file=sys.stderr)
                return 2
            raw_words = json.loads(transcript_path.read_text())
            words = [Word(start=w["start"], end=w["end"], text=w["text"]) for w in raw_words]
            cuts = json.loads(cuts_path.read_text())["cuts"]
            ig_input = [
                {
                    "idx": c["idx"],
                    "title": c.get("title"),
                    "rationale": c.get("rationale"),
                    "text": " ".join(w.text for w in words if w.start >= c["start"] - 0.01 and w.end <= c["end"] + 0.5),
                }
                for c in cuts
            ]
            posts = _instagram.generate(ig_input, lambda ev: print(f"  [ig] {ev.get('message')}") if ev.get("type") == "log" else None)
            if posts is None:
                print("Falha gerando legendas — sigo sem elas.", file=sys.stderr)
            else:
                _instagram.write_files(posts, ig_input, str(job_dir))
                ig_md = job_dir / "instagram.md"
                txts = sorted(job_dir.glob("corte-*-instagram.txt"))

        if ig_md.exists():
            upload_list.append((str(ig_md), ig_md.name))
        for t in txts:
            upload_list.append((str(t), t.name))

    print(f"Job: {job_dir}")
    print(f"Vou enviar {len(upload_list)} arquivos para o Drive (videos-ibb/[YYYY-MM-DD]).")
    print()
    print("ATENÇÃO: se for sua primeira vez, o navegador vai abrir pedindo")
    print("consentimento para acessar o Google Drive. Clique em 'Permitir'.")
    print()

    def on_event(ev: dict) -> None:
        t = ev.get("type")
        if t == "log":
            print(f"[{ev.get('stage')}] {ev.get('message')}")
        elif t == "progress":
            sub = ev.get("sub_fraction")
            idx = ev.get("file_idx")
            total = ev.get("file_total")
            if idx and total and sub is not None:
                print(f"  → arquivo {idx}/{total}: {sub * 100:5.1f}%", end="\r")

    try:
        results = drive.upload_all(upload_list, str(job_dir), on_event)
    except drive.DriveSetupError as e:
        print()
        print(f"\nFalha na configuração do Drive: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print()
        print(f"\nErro inesperado: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print()
    print(f"\n✓ Upload concluído ({len(results)} arquivos):")
    for r in results:
        print(f"  - {r['name']} → {r['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
