from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable


def _icon_height(video_h: int) -> int:
    """Icon height around 80–96 px scaled with video; conservative for 1080p."""
    target = max(80, min(96, int(round(video_h * 0.08))))
    return target


def render_cut(
    source: str,
    ass_path: str,
    icon_path: str,
    out_path: str,
    *,
    start: float,
    end: float,
    width: int,
    height: int,
    fps: float,
    on_event: Callable[[dict], None] | None = None,
    cut_idx: int = 0,
    cut_total: int = 6,
) -> None:
    duration = max(0.01, end - start)
    fps_int = max(1, round(fps))
    icon_h = _icon_height(height)

    # Compose: subtitles first, then overlay icon at x=36,y=36
    # NOTE: subtitles filter needs a path; we escape special chars.
    safe_ass = ass_path.replace(":", "\\:").replace("'", "\\'")
    filter_complex = (
        f"[0:v]subtitles=filename='{safe_ass}'[v0];"
        f"[1:v]scale=-1:{icon_h}[ic];"
        f"[v0][ic]overlay=x=36:y=36[vfinal]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-to", f"{end:.3f}",
        "-i", source,
        "-i", icon_path,
        "-filter_complex", filter_complex,
        "-map", "[vfinal]",
        "-map", "0:a?",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-r", str(fps_int),
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        "-nostats",
        out_path,
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out_time_re = re.compile(r"out_time_ms=(\d+)")
    assert proc.stdout is not None
    for line in proc.stdout:
        m = out_time_re.search(line)
        if not m:
            continue
        elapsed = int(m.group(1)) / 1_000_000.0
        frac = min(1.0, elapsed / duration)
        if on_event:
            on_event({
                "type": "progress",
                "stage": "render",
                "fraction": (cut_idx + frac) / cut_total,
                "cut_idx": cut_idx + 1,
                "cut_total": cut_total,
                "sub_fraction": frac,
            })

    rc = proc.wait()
    if rc != 0:
        err = proc.stderr.read() if proc.stderr else ""
        raise RuntimeError(f"ffmpeg render failed (rc={rc}): {err[-500:]}")
