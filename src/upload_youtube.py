from __future__ import annotations

import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parents[1]


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing GitHub Secret: {name}")
    return value


def main():
    config = json.loads((ROOT / "config/channel.json").read_text(encoding="utf-8"))
    metadata = json.loads((ROOT / "build/metadata.json").read_text(encoding="utf-8"))
    credentials = Credentials(
        token=None,
        refresh_token=required("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=required("YOUTUBE_CLIENT_ID"),
        client_secret=required("YOUTUBE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    description = "\n".join([
        config["persona"], "",
        "This is a fully original daily single: original title, lyrics, melody and arrangement.",
        config["disclosure"], "", "Lyrics:", *metadata["lyrics"], "", f"Series: {config['series_name']}",
    ])
    body = {
        "snippet": {
            "title": f"{metadata['title']} — {metadata['artist']} | Original K-Trot",
            "description": description,
            "tags": config["tags"],
            "categoryId": config["category_id"],
            "defaultLanguage": config["language"],
        },
        "status": {
            "privacyStatus": config["privacy_status"],
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    request = youtube.videos().insert(
        part="snippet,status", body=body,
        media_body=MediaFileUpload(metadata["video"], chunksize=-1, resumable=True),
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    youtube.thumbnails().set(
        videoId=response["id"], media_body=MediaFileUpload(metadata["cover"], mimetype="image/png")
    ).execute()
    print(f"https://youtu.be/{response['id']}")


if __name__ == "__main__":
    main()
