from __future__ import annotations

import argparse
import json
import random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS = [
    {"title": "네온빛 정거장", "place": "서울역 플랫폼", "memory": "막차표 한 장", "hook": "떠난 사랑도 막차 전에 돌아와", "mood": "애절한 정통 트롯", "bpm": 112, "key": "A minor"},
    {"title": "한강의 마지막 택시", "place": "한강 다리", "memory": "빨간 우산", "hook": "기사님 그 사람에게 달려가요", "mood": "도시 야경 트롯", "bpm": 116, "key": "E minor"},
    {"title": "돌아온 카세트", "place": "을지로 다방", "memory": "낡은 카세트", "hook": "되감기 버튼처럼 사랑도 돌아와", "mood": "복고 댄스 트롯", "bpm": 122, "key": "D minor"},
    {"title": "별빛 고속도로", "place": "경부고속도로", "memory": "차창의 별빛", "hook": "사랑을 싣고 밤새 달려가", "mood": "신나는 드라이브 트롯", "bpm": 126, "key": "G minor"},
    {"title": "당신은 나의 리듬", "place": "종로 골목", "memory": "당신의 편지", "hook": "쿵짝 쿵짝 내 심장은 당신 박자", "mood": "흥겨운 커플 트롯", "bpm": 120, "key": "A minor"},
    {"title": "종로의 달빛", "place": "종로 포장마차", "memory": "빛바랜 사진", "hook": "달빛 한 잔에 그 이름을 삼킨다", "mood": "쓸쓸한 성인 트롯", "bpm": 108, "key": "C minor"},
    {"title": "청춘은 두 박자", "place": "남대문 시장", "memory": "첫차의 약속", "hook": "한 박자 쉬고 두 박자 웃어", "mood": "축제형 응원 트롯", "bpm": 128, "key": "D major"},
    {"title": "사랑은 현금박치기", "place": "동대문 야시장", "memory": "빈 지갑 속 사진", "hook": "밀당 말고 사랑은 현금박치기", "mood": "유쾌한 B급 코믹 트롯", "bpm": 130, "key": "G major"},
    {"title": "내 마음 품절입니다", "place": "명동 백화점", "memory": "분홍 영수증", "hook": "당신이 사 간 마음 환불은 안 돼요", "mood": "발랄한 쇼 트롯", "bpm": 124, "key": "F major"},
    {"title": "비 오는 날의 부르스", "place": "비 내린 옥상", "memory": "젖은 성냥갑", "hook": "빗물아 내 눈물까지 데려가", "mood": "블루스풍 정통 트롯", "bpm": 104, "key": "B minor"},
    {"title": "오빠는 내비게이션", "place": "강변북로", "memory": "고장 난 지도", "hook": "내 마음 목적지는 오직 당신", "mood": "코믹 드라이브 트롯", "bpm": 127, "key": "E major"},
    {"title": "아파트 708호", "place": "오래된 아파트", "memory": "문 앞의 우유병", "hook": "708호 불빛은 오늘도 당신을 기다려", "mood": "생활 밀착형 감성 트롯", "bpm": 114, "key": "F minor"},
    {"title": "사랑의 배터리 잔량 1퍼센트", "place": "심야 편의점", "memory": "충전기 없는 전화", "hook": "당신 한마디면 백 퍼센트 충전", "mood": "뉴트로 전자 트롯", "bpm": 123, "key": "A major"},
    {"title": "엄마의 꽃무늬 원피스", "place": "고향 버스터미널", "memory": "꽃무늬 원피스", "hook": "그 시절 엄마도 눈부신 청춘이었다", "mood": "따뜻한 가족 트롯", "bpm": 106, "key": "C major"},
    {"title": "퇴근길 디스코", "place": "구로공단 골목", "memory": "구겨진 출근표", "hook": "오늘만큼은 넥타이 풀고 흔들어", "mood": "디스코 댄스 트롯", "bpm": 132, "key": "E minor"},
    {"title": "사장님 한 곡 더", "place": "노래방 3번 방", "memory": "서비스 한 곡", "hook": "마지막이라 해놓고 한 곡 더", "mood": "회식 떼창 트롯", "bpm": 129, "key": "G major"},
]


def choose_concept(rng: random.Random) -> tuple[dict, str]:
    catalog_path = ROOT / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {"songs": []}
    used_titles = {song["title"] for song in catalog.get("songs", [])}
    concepts = CONCEPTS.copy()
    rng.shuffle(concepts)
    for concept in concepts:
        if concept["title"] not in used_titles:
            return concept, concept["title"]

    season = len(used_titles) // len(CONCEPTS) + 2
    for concept in concepts:
        title = f"{concept['title']} {season}막"
        if title not in used_titles:
            return concept, title
    raise RuntimeError("Could not select a unique song title")


def build_request(run_date: str) -> dict:
    rng = random.Random(int(run_date.replace("-", "")))
    concept, song_title = choose_concept(rng)
    place, memory = concept["place"], concept["memory"]
    hook = concept["hook"]
    lyrics = f"""[Intro]
아 아, 미나 네온
오늘 밤도 두 박자

[Verse 1]
{place} 불빛 아래 나 홀로 서면
주머니 속 {memory} 다시 웃고 있네
한 걸음은 추억이고 두 걸음은 사랑
돌아서려 해도 발끝은 당신을 부르네

[Pre-Chorus]
세월아 잠시만 천천히 가거라
못다 한 이 노래를 전해야 하니까

[Chorus]
{song_title}, 내 마음을 받아줘
{hook}
울어도 좋아 웃어도 좋아
오늘 밤 이 리듬에 다시 한번 사랑해

[Verse 2]
네온사인 흔들리면 추억도 춤추고
멀어진 그 이름이 간판처럼 반짝이네
한 번뿐인 인생길 후회 없이 가자
당신과 나란히면 어디라도 봄날이야

[Pre-Chorus]
시간아 잠시만 이 밤을 비춰라
우리의 젊은 날이 다시 춤을 추니까

[Chorus]
{song_title}, 내 마음을 받아줘
{hook}
울어도 좋아 웃어도 좋아
오늘 밤 이 리듬에 다시 한번 사랑해

[Bridge]
좋다, 한 번 더
사랑은 박자를 타고 돌아와
얼씨구, 손을 잡아
청춘은 바로 지금부터야

[Final Chorus]
{song_title}, 세상 끝까지 가자
{hook}
울어도 좋아 웃어도 좋아
오늘 밤 이 리듬에 영원히 함께해

[Outro]
아 아, 당신과 두 박자
우리 사랑 두 박자
"""
    return {
        "date": run_date,
        "title": song_title,
        "song_title": song_title,
        "hook": hook,
        "mood": concept["mood"],
        "caption": f"High-quality Korean newtro trot song, {concept['mood']}, with a natural expressive adult female singer, warm human vocal timbre, emotional vibrato, clear Korean diction, tasteful vocal bends, 1980s and 1990s Korean trot arrangement, 2/4 rhythm, acoustic drums, electric bass, brass section, accordion, clean electric guitar, analog synth, dynamic verse and huge catchy chorus. Professional studio recording and mastering, organic performance, no robotic voice, no spoken vocals.",
        "negative_prompt": "robotic voice, text to speech, vocoder, metallic vocal, flat emotion, child voice, poor pronunciation, distorted vocal, muddy mix, clipping, demo quality",
        "lyrics": lyrics,
        "language": "ko",
        "duration": 180,
        "bpm": concept["bpm"],
        "keyscale": concept["key"],
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
