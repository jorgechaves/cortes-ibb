from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass
class ProbeResult:
    width: int
    height: int
    fps: float
    duration: float
    vcodec: str
    acodec: str


def probe(path: str) -> ProbeResult:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    num, den = (int(x) for x in video.get("r_frame_rate", "30/1").split("/"))
    fps = num / den if den else 30.0
    return ProbeResult(
        width=int(video["width"]),
        height=int(video["height"]),
        fps=fps,
        duration=float(data["format"]["duration"]),
        vcodec=video["codec_name"],
        acodec=audio["codec_name"] if audio else "",
    )
