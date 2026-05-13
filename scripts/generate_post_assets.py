#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, random, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outbox"
CFG = ROOT / "config" / "content_guidelines.json"


def load_cfg() -> dict:
    return json.loads(CFG.read_text(encoding="utf-8"))


def recent_topics(limit: int = 10) -> set[str]:
    metas = sorted(OUT_DIR.glob("*/meta.json"))[-limit:]
    seen = set()
    for m in metas:
        try:
            seen.add(json.loads(m.read_text(encoding="utf-8")).get("issue", ""))
        except Exception:
            pass
    return {s for s in seen if s}


def clean_title(t: str) -> str:
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\[[^\]]+\]", "", t)
    return t.strip()


def fetch_hot_issue(cfg: dict, seed: int) -> tuple[str, str]:
    hot = cfg.get("hot_issue", {})
    cats = hot.get("categories", [])
    feeds = hot.get("rss_feeds", {})
    rnd = random.Random(seed)
    order = cats[:]
    rnd.shuffle(order)
    used = recent_topics()

    for cat in order:
        url = feeds.get(cat)
        if not url:
            continue
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                xml_data = r.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:10]:
                title = clean_title(item.findtext("title", default=""))
                if title and title not in used:
                    return title, cat
        except Exception:
            continue

    fallback = cfg.get("issues_pool_fallback", ["오늘의 기술 이슈"])
    cands = [x for x in fallback if x not in used] or fallback
    return random.Random(seed).choice(cands), "기술"


def download_realistic_cover(issue: str, out_jpg: Path) -> bool:
    query = urllib.parse.quote(issue + " news people city")
    url = f"https://source.unsplash.com/1600x900/?{query}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            out_jpg.write_bytes(r.read())
        return out_jpg.stat().st_size > 10000
    except Exception:
        return False


def build_markdown(issue: str, category: str, now_kst: dt.datetime, cfg: dict) -> str:
    title = f"{issue}, 지금 알아둬야 할까요?: {category} 이슈를 일상에 적용하는 방법"
    tags = ["#핫이슈", f"#{category}이슈", "#사회", "#정치", "#경제", "#과학", "#기술", "#오늘의뉴스", "#생활인사이트", "#현명한선택", "#미래준비", "#트렌드분석", "#리스크관리", "#정보정리", "#2026트렌드", "#긍정메시지"]
    tags_line = " ".join(tags[:max(cfg['format']['hashtags_min'], 15)])
    return f"""# {title}

## 서론
안녕하세요! {now_kst.strftime('%Y-%m-%d %H:%M KST')} 기준으로, **{issue}**는 일상적인 선택에도 직접 영향을 줄 수 있는 주제입니다. 지금 중요한 이유는 변화 속도가 빠르고, 같은 정보라도 해석에 따라 결과가 달라지기 때문입니다. 이 글은 핵심만 쉽게 정리해 상황별 판단 기준을 제시합니다.

## 본문1. 핵심 정리 3포인트
- **핵심 1**: 이슈의 본질은 감정보다 사실 확인입니다.
- **핵심 2**: 나의 생활/업무에 미치는 영향 범위를 먼저 정리해야 합니다.
- **핵심 3**: 단기 반응보다 중기 기준(1~3개월)을 세우면 흔들림이 줄어듭니다.

### 요약표
| 구분 | 지금 체크할 것 | 선택 기준 |
|---|---|---|
| 사실 | 출처 신뢰도 | 2개 이상 교차확인 |
| 영향 | 비용/시간/위험 | 가장 큰 1개 우선 |
| 실행 | 오늘 할 행동 | 1개만 즉시 실행 |

## 본문2. 득과 실 비교
### 👍 이런 분들에게는 득이 됩니다.
- 변화 신호를 빠르게 읽고 대비하려는 분
- 정보 과잉 속에서 기준을 만들고 싶은 분
- 실천 가능한 루틴으로 연결하고 싶은 분

### 👎 이런 분들에게는 실이 될 수 있습니다.
- 검증 없이 자극적인 정보만 소비하는 경우
- 자신의 상황과 무관한 결정을 따라 하는 경우
- 단기 감정으로 중요한 결정을 내리는 경우

## 본문3. 활용 꿀팁 또는 주의사항
1. **오늘의 이슈를 3줄 요약**해 메모하세요.
2. **나와 관련된 영향 1개**만 골라 행동으로 옮기세요.
3. **일주일 후 재평가**해 기준을 업데이트하세요.

## 결론
핫이슈를 잘 활용하는 사람의 공통점은 빠른 반응이 아니라 **일관된 선택 기준**입니다. 오늘의 정리가 내일의 안정감을 만듭니다. 미래를 위한 선택에 도움이 되기를 바랍니다.

```text
{tags_line}
```
"""


def main() -> None:
    cfg = load_cfg(); now_kst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))); today = now_kst.date()
    issue, category = fetch_hot_issue(cfg, int(now_kst.strftime('%Y%m%d%H')))
    title = f"{issue}, 지금 알아둬야 할까요?: {category} 이슈를 일상에 적용하는 방법"
    post_dir = OUT_DIR / today.isoformat(); post_dir.mkdir(parents=True, exist_ok=True)
    md = post_dir / 'post.md'; jpg = post_dir / 'cover.jpg'; svg = post_dir / 'cover.svg'; meta = post_dir / 'meta.json'
    md.write_text(build_markdown(issue, category, now_kst, cfg), encoding='utf-8')
    got_real = download_realistic_cover(issue, jpg)
    if not got_real:
        svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><rect width="1200" height="630" fill="#1f3c88"/><text x="70" y="200" fill="white" font-size="40">{issue[:42]}</text></svg>', encoding='utf-8')
    cover_rel = str((jpg if got_real else svg).relative_to(ROOT))
    meta.write_text(json.dumps({"date": today.isoformat(), "title": title, "issue": issue, "category": category, "guideline_config": str(CFG.relative_to(ROOT)), "cover_image": cover_rel, "content_markdown": str(md.relative_to(ROOT))}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Generated: {post_dir} | category={category} | cover={'jpg' if got_real else 'svg'}")

if __name__ == '__main__': main()
