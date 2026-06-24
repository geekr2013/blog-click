from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from package_quality_song import make_cover

ROOT = Path(__file__).resolve().parents[1]


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing GitHub Secret: {name}")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--hook", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    config = json.loads((ROOT / "config/channel.json").read_text(encoding="utf-8"))
    build_dir = ROOT / "build"
    build_dir.mkdir(exist_ok=True)
    cover = build_dir / "cover-refresh.png"
    make_cover(cover, args.title, config["artist_name"], args.date, args.hook)

    credentials = Credentials(
        token=None,
        refresh_token=required("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=required("YOUTUBE_CLIENT_ID"),
        client_secret=required("YOUTUBE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    youtube.thumbnails().set(
        videoId=args.video_id,
        media_body=MediaFileUpload(cover, mimetype="image/png"),
    ).execute()
    print(f"UPDATED_VIDEO=https://youtu.be/{args.video_id}")


if __name__ == "__main__":
    main()
