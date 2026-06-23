from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import wave
from array import array
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 44_100
TEMPO = 124
BEAT = 60 / TEMPO
TOTAL_BEATS = 128
ADJECTIVES = ["Neon", "Midnight", "Velvet", "Electric", "Golden", "Dancing", "Starlight"]
NOUNS = ["Promise", "Taxi", "Heartbeat", "Postcard", "Highway", "Moonlight", "Telephone"]
PLACES = ["Seoul", "the riverside", "a glowing arcade", "the last bus", "a rooftop"]
MEMORIES = ["your red umbrella", "our summer cassette", "that borrowed jacket", "your secret smile"]
CHORDS = [(48, 52, 55), (45, 48, 52), (53, 57, 60), (55, 59, 62), (48, 52, 55), (57, 60, 64), (53, 57, 60), (55, 59, 62)]


def midi_hz(note: int) -> float:
    return 440.0 * (2 ** ((note - 69) / 12))


def add_tone(samples: array, start: float, duration: float, frequency: float, volume: float, kind: str = "sine"):
    first = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), len(samples) - first)
    attack = max(1, int(0.015 * SAMPLE_RATE))
    release = max(1, int(0.08 * SAMPLE_RATE))
    for i in range(max(0, count)):
        t = i / SAMPLE_RATE
        phase = 2 * math.pi * frequency * t
        if kind == "square":
            value = 1.0 if math.sin(phase) >= 0 else -1.0
        elif kind == "saw":
            value = 2 * ((frequency * t) % 1) - 1
        else:
            value = math.sin(phase)
        envelope = min(1.0, i / attack, (count - i) / release)
        samples[first + i] += int(32767 * volume * envelope * value)


def add_noise(samples: array, rng: random.Random, start: float, duration: float, volume: float):
    first = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), len(samples) - first)
    for i in range(max(0, count)):
        envelope = max(0.0, 1 - i / max(1, count))
        samples[first + i] += int(32767 * volume * envelope * rng.uniform(-1, 1))


def write_instrumental(path: Path, rng: random.Random):
    duration = TOTAL_BEATS * BEAT
    mix = array("i", [0]) * int((duration + 2) * SAMPLE_RATE)
    melody_scale = [60, 62, 64, 67, 69, 72]
    for beat in range(TOTAL_BEATS):
        t = beat * BEAT
        chord = CHORDS[(beat // 4) % len(CHORDS)]
        if beat % 4 == 0:
            for note in chord:
                add_tone(mix, t, BEAT * 3.8, midi_hz(note), 0.035, "saw")
        bass_note = chord[0] - 12 if beat % 2 == 0 else chord[2] - 12
        add_tone(mix, t, BEAT * 0.75, midi_hz(bass_note), 0.13, "square")
        add_tone(mix, t, 0.11, 58, 0.24)
        if beat % 2 == 1:
            add_noise(mix, rng, t, 0.13, 0.12)
        for eighth in (0, 0.5):
            add_noise(mix, rng, t + eighth * BEAT, 0.035, 0.035)
        if beat >= 8:
            note = melody_scale[(beat + rng.randrange(3)) % len(melody_scale)]
            if beat % 8 in (6, 7):
                note += 2
            add_tone(mix, t, BEAT * 0.82, midi_hz(note), 0.075, "sine")
    peak = max(1, max(abs(v) for v in mix))
    pcm = array("h", (int(max(-32767, min(32767, value * 29000 / peak))) for value in mix))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())


def make_identity(run_date: str):
    rng = random.Random(int(run_date.replace("-", "")))
    title = f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)} {run_date.replace('-', '')}"
    place, memory = rng.choice(PLACES), rng.choice(MEMORIES)
    lyrics = [
        f"Tonight I ride through {place}", f"Still holding {memory}",
        "Two quick steps and one slow goodbye", "My neon heart refuses to cry",
        f"{title}, calling me home", "Spin that old cassette, I am never alone",
        "Hey hey, turn the city bright", f"{title}, dance with me tonight",
    ]
    return rng, title, lyrics


def make_vocal(lyrics: list[str], output: Path):
    text = " ... ".join(lyrics + lyrics[4:])
    subprocess.run(["espeak-ng", "-v", "en-us+f3", "-s", "138", "-p", "62", "-a", "145", "-w", str(output), text], check=True)


def font(size: int, bold: bool = False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def make_cover(path: Path, title: str, artist: str, run_date: str):
    width, height = 1280, 720
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (24 + int(60 * y / height), 5, 58 + int(80 * x / width))
    draw = ImageDraw.Draw(image)
    rng = random.Random(int(run_date.replace("-", "")))
    for _ in range(90):
        x, y = rng.randrange(width), rng.randrange(height)
        r = rng.randrange(1, 5)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 210, 80))
    draw.rounded_rectangle((70, 70, 1210, 650), radius=38, outline=(0, 255, 220), width=7)
    draw.ellipse((825, 155, 1085, 415), fill=(245, 90, 190), outline=(255, 225, 80), width=10)
    draw.ellipse((875, 205, 1035, 365), fill=(42, 8, 68))
    draw.text((115, 135), "ORIGINAL NEWTRO K-TROT", font=font(32, True), fill=(0, 255, 220))
    draw.text((110, 235), title.upper(), font=font(56, True), fill=(255, 235, 90))
    draw.text((115, 355), artist, font=font(46), fill=(255, 255, 255))
    draw.text((115, 540), f"DAILY SINGLE  •  {run_date}", font=font(28), fill=(240, 170, 255))
    image.save(path, quality=95)


def run(command: list[str]):
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    config = json.loads((ROOT / "config/channel.json").read_text(encoding="utf-8"))
    catalog_path = ROOT / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    existing = next((song for song in catalog["songs"] if song["date"] == args.date), None)
    rng, title, lyrics = make_identity(args.date)
    if existing:
        title = existing["title"]
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    instrumental, vocal = build / "instrumental.wav", build / "vocal.wav"
    audio, cover, video = build / "song.wav", build / "cover.png", build / "video.mp4"
    write_instrumental(instrumental, rng)
    make_vocal(lyrics, vocal)
    make_cover(cover, title, config["artist_name"], args.date)
    run(["ffmpeg", "-y", "-i", str(instrumental), "-i", str(vocal), "-filter_complex",
         "[1:a]aecho=0.8:0.6:90:0.25,chorus=0.5:0.8:35:0.4:0.25:2[v];[0:a][v]amix=inputs=2:duration=first:weights='1 0.72',loudnorm=I=-14:TP=-1.5:LRA=11[a]",
         "-map", "[a]", str(audio)])
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(cover), "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", "-movflags", "+faststart", str(video)])
    metadata = {"date": args.date, "title": title, "artist": config["artist_name"], "lyrics": lyrics, "video": str(video), "cover": str(cover)}
    (build / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    if not existing:
        catalog["songs"].append({"date": args.date, "title": title})
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    main()
