from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable


SCOPES = ["https://www.googleapis.com/auth/drive"]
CONFIG_DIR = Path(os.path.expanduser("~/.config/cortes-ibb"))
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"
TOKEN_PATH = CONFIG_DIR / "token.json"
TARGET_FOLDER = "videos-ibb"


class DriveSetupError(Exception):
    pass


def _build_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not CREDENTIALS_PATH.exists():
        raise DriveSetupError(
            f"credentials.json não encontrado em {CREDENTIALS_PATH}. "
            f"Crie um OAuth client Desktop no console.cloud.google.com e baixe o JSON."
        )

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        creds = flow.run_local_server(port=0)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_folder_id(service, name: str, parent_id: str | None = None) -> str | None:
    safe = name.replace("'", "\\'")
    q = (
        f"name='{safe}' "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = service.files().list(q=q, spaces="drive", fields="files(id,name)").execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None


def get_or_create_folder(service, name: str, parent_id: str) -> str:
    existing = find_folder_id(service, name, parent_id)
    if existing:
        return existing
    body = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=body, fields="id").execute()
    return folder["id"]


EXT_TO_MIME = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".m4v": "video/x-m4v",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".json": "application/json",
}


def _infer_mime(name: str) -> str:
    ext = Path(name).suffix.lower()
    return EXT_TO_MIME.get(ext, "application/octet-stream")


def upload_file(
    service,
    folder_id: str,
    local_path: str,
    name: str,
    on_event: Callable[[dict], None] | None,
    file_idx: int,
    file_total: int,
    mime: str | None = None,
):
    from googleapiclient.http import MediaFileUpload

    mime = mime or _infer_mime(name)
    media = MediaFileUpload(local_path, mimetype=mime, resumable=True, chunksize=4 * 1024 * 1024)
    request = service.files().create(
        body={"name": name, "parents": [folder_id], "mimeType": mime},
        media_body=media,
        fields="id,name,webViewLink",
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and on_event:
            sub = status.progress()
            on_event({
                "type": "progress",
                "stage": "drive",
                "fraction": (file_idx + sub) / file_total,
                "file_idx": file_idx + 1,
                "file_total": file_total,
                "sub_fraction": sub,
            })
    return response


def upload_all(
    cuts: list,  # list of (local_path, name) or (local_path, name, mime)
    out_dir: str,
    on_event: Callable[[dict], None],
) -> list[dict]:
    service = _build_service()
    parent_id = find_folder_id(service, TARGET_FOLDER)
    if not parent_id:
        raise DriveSetupError(
            f"Pasta '{TARGET_FOLDER}' não encontrada no Drive. Crie a pasta e compartilhe com sua conta."
        )

    subfolder_name = f"[{datetime.now().strftime('%Y-%m-%d')}]"
    folder_id = get_or_create_folder(service, subfolder_name, parent_id)
    on_event({"type": "log", "stage": "drive", "message": f"Pasta destino: {TARGET_FOLDER}/{subfolder_name}"})

    results: list[dict] = []
    total = len(cuts)
    for i, entry in enumerate(cuts):
        if len(entry) == 3:
            path, name, mime = entry
        else:
            path, name = entry
            mime = None
        on_event({"type": "log", "stage": "drive", "message": f"Enviando {name}..."})
        resp = upload_file(service, folder_id, path, name, on_event, i, total, mime=mime)
        results.append({
            "name": resp.get("name"),
            "id": resp.get("id"),
            "folder": subfolder_name,
            "url": f"https://drive.google.com/file/d/{resp.get('id')}/view",
        })
    Path(out_dir, "drive-ids.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2)
    )
    return results
