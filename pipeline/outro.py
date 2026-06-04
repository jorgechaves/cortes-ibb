from __future__ import annotations

import subprocess


def build_outro(
    logo_path: str,
    out_path: str,
    *,
    width: int,
    height: int,
    fps: float,
) -> None:
    """Render a 2-second outro: logo centered on white background, silent audio."""
    fps_int = max(1, round(fps))
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:white,"
        f"format=yuv420p,fps={fps_int}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "2", "-i", logo_path,
        "-f", "lavfi", "-t", "2", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart",
        out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
