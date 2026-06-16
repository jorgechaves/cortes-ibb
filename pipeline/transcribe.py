from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Iterable


@dataclass
class Word:
    start: float
    end: float
    text: str


def _words_to_text(words: list["Word"], pause_threshold: float = 1.5) -> str:
    if not words:
        return ""
    parts: list[str] = []
    current_block: list[str] = [words[0].text]
    for prev, curr in zip(words, words[1:]):
        if curr.start - prev.end > pause_threshold:
            parts.append(" ".join(current_block))
            current_block = [curr.text]
        else:
            current_block.append(curr.text)
    parts.append(" ".join(current_block))
    return "\n\n".join(parts)


def transcribe(
    source: str,
    out_dir: str,
    duration: float,
    on_event: Callable[[dict], None],
    model_name: str | None = None,
) -> list[Word]:
    from faster_whisper import WhisperModel  # lazy import — heavy

    model_name = model_name or os.environ.get("WHISPER_MODEL", "small")
    on_event({"type": "log", "stage": "transcribe", "message": f"Carregando modelo Whisper '{model_name}' (a 1ª vez baixa do HF)"})
    model = WhisperModel(model_name, device="auto", compute_type="auto")

    on_event({"type": "log", "stage": "transcribe", "message": "Transcrevendo áudio (palavra-a-palavra)"})
    segments, info = model.transcribe(
        source,
        language="pt",
        word_timestamps=True,
        vad_filter=True,
        beam_size=1,
    )

    words: list[Word] = []
    total = max(duration, 0.1)
    for seg in segments:
        for w in (seg.words or []):
            words.append(Word(start=float(w.start), end=float(w.end), text=w.word.strip()))
        pct = min(1.0, seg.end / total) if seg.end else 0.0
        on_event({"type": "progress", "stage": "transcribe", "fraction": pct})

    out_path = Path(out_dir) / "transcript.json"
    out_path.write_text(json.dumps([asdict(w) for w in words], ensure_ascii=False, indent=2))
    (Path(out_dir) / "transcript.txt").write_text(_words_to_text(words), encoding="utf-8")
    on_event({"type": "log", "stage": "transcribe", "message": f"{len(words)} palavras transcritas"})
    return words
