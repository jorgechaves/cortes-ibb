from __future__ import annotations

import subprocess
from pathlib import Path


def concat(content_path: str, outro_path: str, out_path: str) -> None:
    """Concat content + outro. Try -c copy first, fall back to reencode."""
    list_path = Path(out_path).with_suffix(".concat.txt")
    list_path.write_text(
        f"file '{Path(content_path).resolve()}'\n"
        f"file '{Path(outro_path).resolve()}'\n"
    )

    copy_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c", "copy",
        "-movflags", "+faststart",
        out_path,
    ]
    res = subprocess.run(copy_cmd, capture_output=True, text=True)
    if res.returncode == 0:
        list_path.unlink(missing_ok=True)
        return

    # Reencode fallback
    reencode_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        out_path,
    ]
    res2 = subprocess.run(reencode_cmd, capture_output=True, text=True)
    list_path.unlink(missing_ok=True)
    if res2.returncode != 0:
        raise RuntimeError(f"concat failed: {res2.stderr[-500:]}")
