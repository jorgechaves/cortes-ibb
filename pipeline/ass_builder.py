from __future__ import annotations

import os
from pathlib import Path

from .transcribe import Word


ASS_HEADER_TEMPLATE = """[Script Info]
ScriptType: v4.00+
PlayResX: {play_x}
PlayResY: {play_y}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,1,0,2,10,10,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _chunk_words_two(words: list[Word]) -> list[tuple[float, float, str]]:
    chunks: list[tuple[float, float, str]] = []
    i = 0
    while i < len(words):
        pair = words[i:i + 2]
        if not pair:
            break
        start = pair[0].start
        end = pair[-1].end
        # Extend display until next chunk starts (or +0.3s if last)
        text = " ".join(w.text for w in pair).upper()
        # Clean up trailing punctuation that breaks line balance
        text = text.strip()
        chunks.append((start, end, text))
        i += 2

    # Stretch each chunk to start at previous end so no gap, ending at next start - 0.02
    adjusted: list[tuple[float, float, str]] = []
    for idx, (s, e, t) in enumerate(chunks):
        nxt_start = chunks[idx + 1][0] if idx + 1 < len(chunks) else e + 0.3
        adjusted.append((s, max(e, nxt_start - 0.02), t))
    return adjusted


def build_ass(
    cut_words: list[Word],
    cut_start: float,
    out_path: str,
    *,
    width: int,
    height: int,
    font: str | None = None,
    size: int = 14,
) -> None:
    """Build an ASS file with subtitles relative to t=0 (cut_start subtracted)."""
    font = font or os.environ.get("CORTES_FONT", "Antique Olive Std")

    # Rebase timestamps to start of cut
    rebased: list[Word] = []
    for w in cut_words:
        s = max(0.0, w.start - cut_start)
        e = max(s + 0.01, w.end - cut_start)
        rebased.append(Word(start=s, end=e, text=w.text))

    chunks = _chunk_words_two(rebased)

    header = ASS_HEADER_TEMPLATE.format(
        play_x=width, play_y=height, font=font, size=size,
    )
    lines = [header]
    for start, end, text in chunks:
        # Escape ASS special characters
        safe = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        lines.append(f"Dialogue: 0,{_fmt_ts(start)},{_fmt_ts(end)},Default,,0,0,0,,{safe}\n")

    Path(out_path).write_text("".join(lines), encoding="utf-8")
