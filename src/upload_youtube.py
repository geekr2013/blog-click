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
        "#B급감성 #트로트 #뉴트로", "",
        f"🎤 {metadata['title']} — {metadata['artist']}",
        "웃기게 시작했지만 노래에는 진심인 8090 B급 감성 뉴트로 트롯입니다.",
        "복고 무대, 중독성 있는 쿵짝 리듬, 미나 네온의 유쾌한 한 곡을 즐겨주세요.", "",
        config["persona"], "",
        "🎵 가사", *metadata["lyrics"], "",
        f"시리즈: {config['series_name']}",
        "재미있게 들으셨다면 구독과 좋아요, 댓글로 다음 무대를 응원해 주세요.", "",
        config["disclosure"],
    ])
    tags = list(dict.fromkeys(["B급 감성 트롯", "B급 트로트", "코믹 트로트", "8090 감성"] + config["tags"]))
    body = {
        "snippet": {
            "title": f"[B급 감성 트롯] {metadata['title']} | {metadata['artist']}",
            "description": description,
            "tags": tags,
            "categoryId": config["category_id"],
            "defaultLanguage": config["language"],
            "defaultAudioLanguage": config["language"],
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
    print(f"PUBLISHED_VIDEO=https://youtu.be/{response['id']}")


if __name__ == "__main__":
    main()
