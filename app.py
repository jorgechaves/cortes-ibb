"""Cortes IBB — local FastAPI app to slice a video into 6 social-media cuts."""
from __future__ import annotations

import json
import os
import queue
import secrets
import shutil
import socket
import sys
import threading
import time
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()  # read .env in cwd before importing pipeline

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import pipeline as pipeline_mod


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
OUTPUT_DIR = ROOT / "output"
ICON_PATH = ROOT / "icone.png"
LOGO_PATH = ROOT / "logo.png"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB


class JobState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.job_id: Optional[str] = None
        self.queue: "queue.Queue[dict]" = queue.Queue()
        self.status: str = "idle"  # idle | running | done | error

    def start(self, job_id: str) -> None:
        self.job_id = job_id
        self.queue = queue.Queue()
        self.status = "running"

    def finish(self, status: str) -> None:
        self.status = status


state = JobState()
app = FastAPI(title="Cortes IBB")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/status")
def api_status() -> JSONResponse:
    return JSONResponse({
        "status": state.status,
        "job_id": state.job_id,
        "warnings": pipeline_mod.warnings(),
    })


@app.post("/upload")
async def upload(video: UploadFile = File(...), subtitle: str = Form("true")) -> JSONResponse:
    with_subtitles = subtitle.lower() == "true"
    with state.lock:
        if state.status == "running":
            raise HTTPException(status_code=409, detail="job in progress")
        if not (video.content_type or "").startswith("video/"):
            raise HTTPException(status_code=400, detail="not a video file")

        job_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        source_path = job_dir / "source.mp4"

        # Stream upload to disk with size guard
        size = 0
        with source_path.open("wb") as f:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    f.close()
                    source_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="file exceeds 5 GB")
                f.write(chunk)

        state.start(job_id)
        # Emit initial upload event so the UI sees progress immediately
        state.queue.put({
            "type": "progress",
            "stage": "upload",
            "fraction": 1.0,
            "percent": 5.0,
            "message": f"{size / 1_000_000:.1f} MB recebidos",
        })
        state.queue.put({"type": "stage", "stage": "probe", "message": "Inspecionando vídeo", "percent": 5.0})

        thread = threading.Thread(
            target=_run_pipeline,
            args=(str(source_path), str(job_dir), with_subtitles),
            daemon=True,
        )
        thread.start()

    return JSONResponse({"jobId": job_id, "stream": "/events"})


def _run_pipeline(source: str, job_dir: str, with_subtitles: bool = True) -> None:
    def on_event(ev: dict) -> None:
        state.queue.put(ev)

    try:
        if not ICON_PATH.exists() or not LOGO_PATH.exists():
            raise RuntimeError(f"icone.png ou logo.png ausente em {ROOT}")
        result = pipeline_mod.run(source, str(ICON_PATH), str(LOGO_PATH), job_dir, on_event, with_subtitles=with_subtitles)
        state.queue.put({"type": "done", "stage": "done", "percent": 100.0, "data": result})
        state.finish("done")
    except Exception as e:
        state.queue.put({
            "type": "error",
            "stage": "pipeline",
            "message": f"{type(e).__name__}: {e}",
            "trace": traceback.format_exc(),
        })
        state.finish("error")


@app.get("/events")
async def events(request: Request) -> StreamingResponse:
    def gen():
        # Send a hello so EventSource opens cleanly
        yield "event: hello\ndata: {}\n\n"
        while True:
            try:
                ev = state.queue.get(timeout=15.0)
            except queue.Empty:
                yield ": keepalive\n\n"
                continue
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            if ev.get("type") in ("done", "error"):
                break

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/shutdown")
def shutdown() -> JSONResponse:
    def _bye():
        time.sleep(0.2)
        os._exit(0)
    threading.Thread(target=_bye, daemon=True).start()
    return JSONResponse({"ok": True})


# Serve files for "Open local folder" / direct download
@app.get("/files/{job_id}/{name}")
def file(job_id: str, name: str) -> FileResponse:
    path = OUTPUT_DIR / job_id / name
    if not path.exists():
        raise HTTPException(status_code=404)
    return FileResponse(path)


def pick_port(start: int = 7860, end: int = 7870) -> int:
    for p in range(start, end + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", p))
            s.close()
            return p
        except OSError:
            continue
    raise RuntimeError(f"no free port in {start}-{end}")


def main() -> None:
    errors = pipeline_mod.check_environment()
    if errors:
        print("Erros de ambiente:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(2)
    WEB_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    if not (WEB_DIR / "index.html").exists():
        print(f"web/index.html ausente em {WEB_DIR}", file=sys.stderr)
        sys.exit(2)

    port = pick_port()
    url = f"http://127.0.0.1:{port}/"
    print(f"\n→ Cortes IBB rodando em {url}\n  (Ctrl+C para encerrar)\n")

    # Open browser shortly after server starts
    def _open():
        time.sleep(0.5)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
