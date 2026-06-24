from __future__ import annotations

import argparse
import base64
import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

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


def make_cover(path: Path, title: str, artist: str):
    encoded = (ROOT / "assets/mina-neon-stage.jpg.b64").read_text(encoding="ascii")
    portrait = Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")
    image = portrait.resize((1280, 720), Image.Resampling.LANCZOS)
    image = ImageEnhance.Color(image).enhance(1.15)

    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(shade)
    for x in range(780):
        alpha = max(0, 205 - int(x * 0.20))
        shade_draw.line((x, 0, x, 720), fill=(12, 0, 28, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), shade)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((55, 48, 385, 115), radius=18, fill=(255, 232, 0, 245), outline=(255, 40, 145, 255), width=5)
    draw.text((84, 58), "B급 감성 트롯", font=font(38, True), fill=(30, 0, 36), stroke_width=1)

    title_font = font(78 if len(title) <= 8 else 66, True)
    draw.text((62, 178), title, font=title_font, fill=(255, 255, 255), stroke_width=8, stroke_fill=(135, 0, 83))

    korean_artist = artist.split(" Mina")[0]
    draw.text((65, 340), korean_artist, font=font(62, True), fill=(255, 225, 35), stroke_width=7, stroke_fill=(90, 0, 55))
    draw.text((68, 435), "웃기게 진심인 8090 뉴트로", font=font(31, True), fill=(255, 255, 255), stroke_width=4, stroke_fill=(20, 0, 35))

    draw.rounded_rectangle((55, 590, 535, 670), radius=22, fill=(235, 0, 115, 225), outline=(255, 230, 40, 255), width=5)
    draw.text((82, 605), "한 번 들으면 계속 쿵짝!", font=font(33, True), fill="white", stroke_width=2, stroke_fill=(75, 0, 45))
    image.convert("RGB").save(path, quality=95)


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
    make_cover(cover, request["title"], config["artist_name"])
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
