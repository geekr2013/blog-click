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
SAMPLE_RATE = 32_000
TEMPO = 120
BEAT = 60 / TEMPO
TOTAL_BEATS = 448  # 3 minutes 44 seconds

ADJECTIVES = ["Neon", "Midnight", "Velvet", "Electric", "Golden", "Dancing", "Starlight"]
NOUNS = ["Promise", "Taxi", "Heartbeat", "Postcard", "Highway", "Moonlight", "Telephone"]
PLACES = ["Seoul", "the riverside", "a glowing arcade", "the last bus", "a rooftop"]
MEMORIES = ["your red umbrella", "our summer cassette", "that borrowed jacket", "your secret smile"]
CHORDS = [
    (48, 52, 55), (45, 48, 52), (53, 57, 60), (55, 59, 62),
    (48, 52, 55), (57, 60, 64), (53, 57, 60), (55, 59, 62),
]

# start beat, end beat, section name, energy
ARRANGEMENT = [
    (0, 16, "intro", 0.55),
    (16, 80, "verse1", 0.72),
    (80, 144, "chorus1", 1.00),
    (144, 160, "turnaround", 0.62),
    (160, 224, "verse2", 0.76),
    (224, 288, "chorus2", 1.00),
    (288, 320, "bridge", 0.58),
    (320, 416, "final_chorus", 1.08),
    (416, 448, "outro", 0.50),
]


def midi_hz(note: int) -> float:
    return 440.0 * (2 ** ((note - 69) / 12))


def section_at(beat: int) -> tuple[str, float]:
    for start, end, name, energy in ARRANGEMENT:
        if start <= beat < end:
            return name, energy
    return "outro", 0.5


def add_tone(samples: array, start: float, duration: float, frequency: float, volume: float, kind: str = "sine"):
    first = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), len(samples) - first)
    attack = max(1, int(0.012 * SAMPLE_RATE))
    release = max(1, int(0.09 * SAMPLE_RATE))
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
    melody_scale = [60, 62, 64, 67, 69, 72, 74]
    for beat in range(TOTAL_BEATS):
        t = beat * BEAT
        section, energy = section_at(beat)
        chord = CHORDS[(beat // 4) % len(CHORDS)]
        section_start = next(start for start, end, name, _ in ARRANGEMENT if name == section)
        local_beat = beat - section_start
        if beat % 4 == 0:
            for note in chord:
                add_tone(mix, t, BEAT * 3.85, midi_hz(note), 0.026 * energy, "saw")
        bass_note = chord[0] - 12 if beat % 2 == 0 else chord[2] - 12
        add_tone(mix, t, BEAT * 0.72, midi_hz(bass_note), 0.105 * energy, "square")
        add_tone(mix, t, 0.10, 56, 0.20 * energy)
        if beat % 2 == 1 and section not in ("intro", "bridge", "outro"):
            add_noise(mix, rng, t, 0.12, 0.095 * energy)
        if section not in ("intro", "bridge"):
            for eighth in (0, 0.5):
                add_noise(mix, rng, t + eighth * BEAT, 0.032, 0.025 * energy)
        instrumental_section = section in ("intro", "turnaround", "outro")
        phrase_gap = local_beat % 16 in (12, 13, 14, 15)
        if instrumental_section or phrase_gap:
            note = melody_scale[(beat // 2 + rng.randrange(2)) % len(melody_scale)]
            if section in ("chorus1", "chorus2", "final_chorus"):
                note += 5
            add_tone(mix, t, BEAT * 0.78, midi_hz(note), 0.065 * energy, "sine")
        if "chorus" in section and beat % 8 in (0, 3):
            for note in chord:
                add_tone(mix, t, BEAT * 0.36, midi_hz(note + 12), 0.028, "square")
    peak = max(1, max(abs(v) for v in mix))
    pcm = array("h", (int(max(-32767, min(32767, value * 28500 / peak))) for value in mix))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())


def make_identity(run_date: str):
    rng = random.Random(int(run_date.replace("-", "")))
    title = f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)} {run_date.replace('-', '')}"
    place, memory = rng.choice(PLACES), rng.choice(MEMORIES)
    lyrics = {
        "verse1": [f"Tonight I ride through {place}", f"Still holding {memory}", "Two quick steps and one slow goodbye", "My neon heart refuses to cry"],
        "chorus": [f"{title}, calling me home", "Spin that old cassette, I am never alone", "Hey hey, turn the city bright", f"{title}, dance with me tonight"],
        "verse2": ["Silver streetlights follow my shoes", "I turn every teardrop into rhythm and blues", "The morning can wait beyond the door", "Tonight we dance like nineteen eighty four"],
        "bridge": ["Hold on, hold on, the night is young", "Every lonely story needs a song", "One more turn beneath the colored light", "We will keep this little dream alive"],
    }
    return rng, title, lyrics


def make_vocal_section(lines: list[str], output: Path, voice: str, speed: int, pitch: int):
    text = " ... ".join(line for line in lines for _ in (0, 1))
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-p", str(pitch), "-a", "190", "-w", str(output), text], check=True)


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
    instrumental = build / "instrumental.wav"
    audio, cover, video = build / "song.wav", build / "cover.png", build / "video.mp4"
    vocal_specs = [
        ("verse1", lyrics["verse1"], 16), ("chorus1", lyrics["chorus"], 80),
        ("verse2", lyrics["verse2"], 160), ("chorus2", lyrics["chorus"], 224),
        ("bridge", lyrics["bridge"], 288), ("final", lyrics["chorus"], 320),
    ]
    write_instrumental(instrumental, rng)
    vocal_paths = []
    for index, (name, lines, _) in enumerate(vocal_specs):
        path = build / f"vocal_{name}.wav"
        voice = "en-us+f3" if index % 2 == 0 else "en-us+f4"
        make_vocal_section(lines, path, voice=voice, speed=112, pitch=64 + index % 2 * 3)
        vocal_paths.append(path)
    make_cover(cover, title, config["artist_name"], args.date)
    inputs = ["-i", str(instrumental)]
    for path in vocal_paths:
        inputs.extend(["-i", str(path)])
    vocal_filters, labels = [], []
    for index, (_, _, start_beat) in enumerate(vocal_specs, start=1):
        delay = int(start_beat * BEAT * 1000)
        label = f"v{index}"
        labels.append(f"[{label}]")
        vocal_filters.append(
            f"[{index}:a]highpass=f=115,lowpass=f=9000,equalizer=f=2600:t=q:w=1.2:g=4,"
            "acompressor=threshold=-22dB:ratio=4:attack=8:release=110:makeup=7,"
            "vibrato=f=5.4:d=0.12,chorus=0.55:0.75:28:0.35:0.22:1.8,"
            f"aecho=0.8:0.55:95:0.20,volume=1.8,adelay={delay}|{delay}[{label}]"
        )
    filter_complex = (
        "[0:a]highpass=f=32,lowpass=f=15000,equalizer=f=280:t=q:w=1.1:g=-2.5,"
        "equalizer=f=3500:t=q:w=1.0:g=1.5,acompressor=threshold=-18dB:ratio=2.2:attack=20:release=250:makeup=2,volume=0.82[music];"
        + ";".join(vocal_filters)
        + f";{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0[vocals];"
        "[vocals]asplit=2[vkey][vmain];"
        "[music][vkey]sidechaincompress=threshold=0.025:ratio=5:attack=12:release=280[ducked];"
        "[ducked][vmain]amix=inputs=2:duration=first:weights='1 1.45':normalize=0,"
        "alimiter=limit=0.94:attack=5:release=80,loudnorm=I=-14:TP=-1.2:LRA=9[a]"
    )
    run(["ffmpeg", "-y", *inputs, "-filter_complex", filter_complex, "-map", "[a]", str(audio)])
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(cover), "-i", str(audio), "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-c:a", "aac", "-b:a", "256k", "-pix_fmt", "yuv420p", "-shortest", "-movflags", "+faststart", str(video)])
    flat_lyrics = lyrics["verse1"] + lyrics["chorus"] + lyrics["verse2"] + lyrics["chorus"] + lyrics["bridge"] + lyrics["chorus"]
    metadata = {"date": args.date, "title": title, "artist": config["artist_name"], "lyrics": flat_lyrics, "duration_seconds": int(TOTAL_BEATS * BEAT), "video": str(video), "cover": str(cover)}
    (build / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    if not existing:
        catalog["songs"].append({"date": args.date, "title": title})
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    main()
