from __future__ import annotations

import argparse
import json
import random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITLES = ["네온빛 정거장", "한강의 마지막 택시", "돌아온 카세트", "별빛 고속도로", "당신은 나의 리듬", "종로의 달빛", "청춘은 두 박자"]
PLACES = ["한강 다리", "종로 골목", "을지로 다방", "서울역 광장", "비 내린 옥상"]
MEMORIES = ["빨간 우산", "낡은 카세트", "빛바랜 사진", "당신의 편지", "첫차의 약속"]


def build_request(run_date: str) -> dict:
    rng = random.Random(int(run_date.replace("-", "")))
    title = f"{rng.choice(TITLES)} {run_date.replace('-', '')}"
    place, memory = rng.choice(PLACES), rng.choice(MEMORIES)
    lyrics = f"""[Intro]
아 아, 오늘도 두 박자

[Verse 1]
{place} 불빛 아래 나 홀로 서면
주머니 속 {memory} 다시 웃고 있네
한 걸음은 그리움 두 걸음은 사랑
돌아서도 내 마음은 당신을 부르네

[Pre-Chorus]
세월아 잠시만 천천히 가거라
못다 한 이 노래를 전해야 하니까

[Chorus]
{title}, 내 마음을 받아줘
쿵짝 쿵짝 가슴이 먼저 당신을 찾아가
울어도 좋아 웃어도 좋아
오늘 밤 이 리듬에 우리 다시 사랑해

[Verse 2]
새벽 첫차 창문에 추억이 흐르고
멀어진 그 이름이 별처럼 반짝이네
한 번뿐인 인생길 후회 없이 가자
당신과 나란히면 어디라도 봄날이야

[Pre-Chorus]
시간아 잠시만 이 밤을 비춰라
우리의 젊은 날이 다시 춤을 추니까

[Chorus]
{title}, 내 마음을 받아줘
쿵짝 쿵짝 가슴이 먼저 당신을 찾아가
울어도 좋아 웃어도 좋아
오늘 밤 이 리듬에 우리 다시 사랑해

[Bridge]
헤이, 한 번 더
사랑은 돌아오는 거야
헤이, 손을 잡아
청춘은 지금부터야

[Final Chorus]
{title}, 세상 끝까지 가자
쿵짝 쿵짝 뜨거운 노래 멈추지 않을 거야
울어도 좋아 웃어도 좋아
오늘 밤 이 리듬에 영원히 함께해

[Outro]
아 아, 당신과 두 박자
우리 사랑 두 박자
"""
    return {
        "date": run_date,
        "title": title,
        "caption": "High-quality Korean newtro trot song with a natural expressive adult female singer, warm human vocal timbre, emotional vibrato, clear Korean diction, tasteful vocal bends, 1980s and 1990s Korean trot arrangement, 2/4 rhythm, acoustic drums, electric bass, brass section, accordion, clean electric guitar, analog synth, dynamic verse and huge catchy chorus. Professional studio recording and mastering, organic performance, no robotic voice, no spoken vocals.",
        "negative_prompt": "robotic voice, text to speech, vocoder, metallic vocal, flat emotion, child voice, poor pronunciation, distorted vocal, muddy mix, clipping, demo quality",
        "lyrics": lyrics,
        "language": "ko",
        "duration": 210,
        "bpm": 118,
        "keyscale": "A minor",
        "timesignature": "2",
        "seed": int(run_date.replace("-", "")),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output", default="kaggle/request.json")
    args = parser.parse_args()
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    request = build_request(args.date)
    output.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(request, ensure_ascii=False))


if __name__ == "__main__":
    main()
