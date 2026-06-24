from __future__ import annotations

import argparse
import json
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SONG_SECONDS = 180


def font(size: int, bold: bool = False):
    names = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def make_cover(path: Path, title: str, artist: str, run_date: str):
    rng = random.Random(int(run_date.replace("-", "")))
    palettes = [
        ((25, 5, 58), (0, 255, 220), (255, 235, 85)),
        ((52, 7, 25), (255, 135, 40), (255, 225, 120)),
        ((5, 32, 60), (80, 210, 255), (255, 105, 190)),
        ((38, 12, 62), (210, 120, 255), (80, 255, 175)),
    ]
    background, neon, headline = rng.choice(palettes)
    image = Image.new("RGB", (1280, 720), background)
    draw = ImageDraw.Draw(image)
    for y in range(720):
        color = tuple(min(255, value + y // divisor) for value, divisor in zip(background, (15, 45, 10)))
        draw.line((0, y, 1280, y), fill=color)
    draw.rounded_rectangle((60, 60, 1220, 660), radius=42, outline=neon, width=8)
    draw.ellipse((865, 145, 1115, 395), fill=(240, 75, 185), outline=(255, 220, 75), width=12)
    draw.ellipse((920, 200, 1060, 340), fill=(36, 5, 65))
    draw.text((105, 130), "ORIGINAL K-NEWTRO TROT", font=font(34, True), fill=neon)
    draw.text((100, 235), title, font=font(60, True), fill=headline)
    draw.text((105, 360), artist, font=font(46), fill="white")
    draw.text((105, 555), f"NEW SINGLE  •  {run_date}", font=font(28), fill=(240, 175, 255))
    image.save(path, quality=95)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    config = json.loads((ROOT / "config/channel.json").read_text(encoding="utf-8"))
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    cover, mastered, video = build / "cover.png", build / "song.m4a", build / "video.mp4"
    make_cover(cover, request["title"], config["artist_name"], request["date"])
    subprocess.run([
        "ffmpeg", "-y", "-i", args.audio, "-t", str(SONG_SECONDS),
        "-af", "highpass=f=28,lowpass=f=18000,loudnorm=I=-14:TP=-1.2:LRA=9,alimiter=limit=0.95",
        "-c:a", "aac", "-b:a", "320k", str(mastered),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-i", str(cover), "-i", str(mastered),
        "-map", "0:v:0", "-map", "1:a:0", "-t", str(SONG_SECONDS),
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-crf", "20", "-r", "24",
        "-c:a", "copy", "-pix_fmt", "yuv420p", "-shortest", "-movflags", "+faststart", str(video),
    ], check=True)
    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(video)
    ], text=True).strip())
    if not 175 <= duration <= 181:
        raise SystemExit(f"Unexpected video duration: {duration:.2f}s")
    metadata = {
        "date": request["date"], "title": request["title"], "artist": config["artist_name"],
        "lyrics": [line for line in request["lyrics"].splitlines() if line and not line.startswith("[")],
        "video": str(video), "cover": str(cover), "generator": "ACE-Step 1.5",
    }
    (build / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
