#!/usr/bin/env python3
"""Generate a fully automated, policy-safe blog growth plan and assets."""
from __future__ import annotations

import datetime as dt
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORT = ROOT / "REPORT.md"

TOPIC_BUCKETS = [
    "초보자를 위한 실전 가이드",
    "자주 묻는 질문 정리",
    "실수/실패 사례와 해결법",
    "비용 절감 팁",
    "체크리스트 모음",
    "도구 비교 및 추천",
    "업데이트/변경사항 해설",
    "1주일 루틴/플랜",
]

TITLE_TEMPLATES = [
    "[{year}] {topic} 완전정리 ({n}가지 핵심)",
    "{topic}: 초보도 바로 따라하는 방법 {n}단계",
    "{topic} 할 때 꼭 피해야 할 실수 {n}가지",
    "{topic} 체크리스트: 발행 전 확인할 {n}포인트",
    "{topic} 비용/시간 줄이는 현실 팁 {n}선",
]

CTA_LIBRARY = [
    "이 글이 도움이 되셨다면 공감/댓글로 다음 주제를 남겨주세요.",
    "관련 글은 블로그 홈의 카테고리에서 이어서 볼 수 있어요.",
    "실행해보신 결과를 댓글로 공유해주시면 후속 글로 정리하겠습니다.",
]

HASHTAGS = [
    "#네이버블로그",
    "#블로그운영",
    "#콘텐츠마케팅",
    "#키워드전략",
    "#포스팅루틴",
    "#SEO",
]


def make_week_plan(seed: int, start: dt.date) -> list[dict]:
    rnd = random.Random(seed)
    plan = []
    for i in range(7):
        date = start + dt.timedelta(days=i)
        topic = rnd.choice(TOPIC_BUCKETS)
        n = rnd.randint(5, 12)
        title = rnd.choice(TITLE_TEMPLATES).format(year=date.year, topic=topic, n=n)
        cta = rnd.choice(CTA_LIBRARY)
        tags = rnd.sample(HASHTAGS, k=4)
        publish_hour = rnd.choice([8, 11, 14, 20, 22])
        plan.append(
            {
                "date": date.isoformat(),
                "title": title,
                "outline": [
                    "문제 정의 (독자가 겪는 상황)",
                    "핵심 해결 전략 3가지",
                    "실행 단계 및 체크리스트",
                    "자주 묻는 질문(FAQ)",
                    "정리 + 다음 글 예고",
                ],
                "cta": cta,
                "hashtags": tags,
                "recommended_publish_time": f"{publish_hour:02d}:00 KST",
            }
        )
    return plan


def write_outputs(plan: list[dict], generated_at: dt.datetime) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    json_path = DATA / "weekly_plan.json"
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 블로그 자동 성장 리포트",
        "",
        f"- 생성 시각(UTC): {generated_at.isoformat(timespec='seconds')}Z",
        "- 목적: 광고 클릭/트래픽 조작 없이, 합법적 콘텐츠 운영 자동화",
        "- 동작: 매일 GitHub Actions가 다음 7일치 발행 계획을 갱신",
        "",
        "## 7일 발행 계획",
        "",
    ]

    for day in plan:
        lines.extend(
            [
                f"### {day['date']} — {day['title']}",
                f"- 권장 발행 시간: {day['recommended_publish_time']}",
                f"- CTA: {day['cta']}",
                f"- 해시태그: {' '.join(day['hashtags'])}",
                "- 아웃라인:",
            ]
        )
        for item in day["outline"]:
            lines.append(f"  - {item}")
        lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    now = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    monday = (now.date() - dt.timedelta(days=now.weekday()))
    plan = make_week_plan(seed=int(now.strftime("%G%V")), start=monday)
    write_outputs(plan, generated_at=now)


if __name__ == "__main__":
    main()
