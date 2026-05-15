import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import google.generativeai as genai
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path("data/meeting_poc.db")
RISK_KEYWORDS = ["지연", "리스크", "문제", "장애", "예산", "법무", "보안", "미정", "불가", "차질"]

st.set_page_config(page_title="회의록 POC v2", layout="wide")


@dataclass
class SpeakerUtterance:
    speaker: str
    start: float
    end: float
    text: str


@dataclass
class MeetingRecord:
    created_at: str
    source_type: str
    source_ref: str
    risks_json: str
    utterances_json: str
    summary_md: str


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            risks_json TEXT NOT NULL,
            utterances_json TEXT NOT NULL,
            summary_md TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def download_youtube(url: str, workdir: Path) -> Path:
    out = workdir / "source.mp4"
    cmd = ["yt-dlp", "-f", "mp4", "-o", str(out), url]
    code, _, err = run_cmd(cmd)
    if code != 0:
        raise RuntimeError(f"YouTube 다운로드 실패: {err}")
    return out


def extract_wav(src: Path, workdir: Path) -> Path:
    out = workdir / "audio.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(out),
    ]
    code, _, err = run_cmd(cmd)
    if code != 0:
        raise RuntimeError(f"오디오 추출 실패(ffmpeg 필요): {err}")
    return out


def vito_auth(client_id: str, client_secret: str) -> str:
    token_resp = requests.post(
        "https://openapi.vito.ai/v1/authenticate",
        json={"client_id": client_id, "client_secret": client_secret},
        timeout=30,
    )
    token_resp.raise_for_status()
    return token_resp.json()["access_token"]


def vito_transcribe(audio_path: Path, poll_seconds: int = 2, max_wait_seconds: int = 900) -> dict[str, Any]:
    client_id = os.getenv("VITO_CLIENT_ID")
    client_secret = os.getenv("VITO_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("VITO_CLIENT_ID / VITO_CLIENT_SECRET 환경변수가 필요합니다.")

    access_token = vito_auth(client_id, client_secret)
    with open(audio_path, "rb") as f:
        transcribe_resp = requests.post(
            "https://openapi.vito.ai/v1/transcribe",
            headers={"Authorization": f"bearer {access_token}"},
            files={"file": f},
            data={
                "config": json.dumps(
                    {
                        "use_diarization": True,
                        "diarization": {"spk_count": 0},
                    }
                )
            },
            timeout=120,
        )
    transcribe_resp.raise_for_status()
    body = transcribe_resp.json()

    # 일부 계정은 동기 응답, 일부는 비동기 ID 응답 가능성을 모두 처리
    if body.get("results"):
        return body

    transcribe_id = body.get("id") or body.get("transcribe_id")
    if not transcribe_id:
        raise RuntimeError(f"VITO 응답 포맷을 인식할 수 없습니다: {body}")

    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        status_resp = requests.get(
            f"https://openapi.vito.ai/v1/transcribe/{transcribe_id}",
            headers={"Authorization": f"bearer {access_token}"},
            timeout=30,
        )
        status_resp.raise_for_status()
        status_body = status_resp.json()
        status = status_body.get("status")

        if status in {"completed", "done", "success"} and status_body.get("results"):
            return status_body
        if status in {"failed", "error", "canceled"}:
            raise RuntimeError(f"VITO 전사 실패: {status_body}")
        time.sleep(poll_seconds)

    raise TimeoutError(f"VITO 전사 타임아웃: {max_wait_seconds}초")


def normalize_vito(result: dict[str, Any]) -> list[SpeakerUtterance]:
    chunks = result.get("results", {}).get("utterances", [])
    out: list[SpeakerUtterance] = []
    for c in chunks:
        spk = str(c.get("spk", "unknown"))
        start_sec = float(c.get("start_at", 0)) / 1000
        end_sec = start_sec + (float(c.get("duration", 0)) / 1000)
        out.append(SpeakerUtterance(speaker=f"화자-{spk}", start=start_sec, end=end_sec, text=c.get("msg", "")))
    return out


def detect_risks(utterances: list[SpeakerUtterance]) -> list[str]:
    risks: list[str] = []
    for u in utterances:
        if any(k in u.text for k in RISK_KEYWORDS):
            risks.append(f"[{u.speaker}] {u.text[:180]}")
    return risks[:20]


def infer_speaker_map(utterances: list[SpeakerUtterance]) -> str:
    speakers = sorted({u.speaker for u in utterances})
    if not speakers:
        return ""
    return "\n".join([f"{s}: (부서명 입력 필요)" for s in speakers])


def gemini_summary(utterances: list[SpeakerUtterance], speaker_map_text: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 필요합니다.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    transcript = "\n".join([f"[{u.speaker} {u.start:.1f}-{u.end:.1f}] {u.text}" for u in utterances])
    prompt = f"""
다음은 화자분리된 회의 대화입니다.

화자-부서 매핑(사용자 입력):
{speaker_map_text}

반드시 포함:
1) 화자별 핵심 발언 요약 표(열: 화자,부서,요약)
2) Action Item 표(열: 담당,지시사항,기한,의존성,리스크)
3) 미정/보류 항목 목록
4) 다음 회의에서 확인할 질문 5개
5) 전체 리스크 수준(상/중/하) 및 근거

회의 대화:
{transcript}
"""
    return model.generate_content(prompt).text


def save_meeting(record: MeetingRecord) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO meetings (created_at, source_type, source_ref, risks_json, utterances_json, summary_md)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (record.created_at, record.source_type, record.source_ref, record.risks_json, record.utterances_json, record.summary_md),
    )
    conn.commit()
    meeting_id = cur.lastrowid
    conn.close()
    return int(meeting_id)


def list_meetings(limit: int = 20) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, created_at, source_type, source_ref FROM meetings ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_meeting(meeting_id: int) -> dict[str, Any] | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


init_db()

st.title("🧭 맥락추적형 회의록 정리 POC v2")
st.caption("YouTube/MP4 입력 → WAV 추출 → VITO 화자분리 → Gemini 요약 → 히스토리 저장/조회")

with st.sidebar:
    st.header("저장된 회의록")
    q = st.text_input("검색(소스/일시)")
    meetings = list_meetings(50)
    if q:
        meetings = [m for m in meetings if q.lower() in (m["source_ref"] + m["created_at"]).lower()]

    for m in meetings[:20]:
        if st.button(f"#{m['id']} {m['created_at']} ({m['source_type']})", key=f"m-{m['id']}"):
            st.session_state["selected_meeting_id"] = m["id"]

    st.divider()
    st.markdown("**리스크 키워드 사전**")
    st.code(", ".join(RISK_KEYWORDS), language="text")

selected_id = st.session_state.get("selected_meeting_id")
if selected_id:
    selected = get_meeting(int(selected_id))
    if selected:
        st.subheader(f"저장본 조회: #{selected_id}")
        st.markdown(selected["summary_md"])
        with st.expander("저장된 화자분리 원문 보기"):
            st.json(json.loads(selected["utterances_json"]))

with st.expander("초기 리스크 보기", expanded=True):
    st.markdown(
        """
- API 키/요금제/권한 설정에 따라 외부 API 실패 가능.
- 장시간 영상은 전사 시간이 길어져 비동기 polling이 필요.
- 화자-부서 매핑 미입력 시 지시사항 추적 품질 저하.
- YouTube 다운로드 품질 및 저작권/보안 정책 확인 필요.
"""
    )

col1, col2 = st.columns(2)
source_mode = col1.radio("입력 방식", ["YouTube 링크", "MP4 업로드"])
trigger = col2.button("지시사항 정리 실행", type="primary")

youtube_url = st.text_input("YouTube URL") if source_mode == "YouTube 링크" else None
mp4_file = st.file_uploader("MP4 업로드", type=["mp4"]) if source_mode == "MP4 업로드" else None
speaker_map = st.text_area("화자-부서 매핑 (예: 화자-0:개발팀, 화자-1:기획팀)")

if trigger:
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        src_path: Path
        source_ref = ""

        if source_mode == "YouTube 링크":
            if not youtube_url or not re.match(r"^https?://", youtube_url):
                st.error("유효한 YouTube URL을 입력하세요.")
                st.stop()
            source_ref = youtube_url
            with st.spinner("YouTube 다운로드 중..."):
                src_path = download_youtube(youtube_url, workdir)
        else:
            if not mp4_file:
                st.error("MP4 파일을 업로드하세요.")
                st.stop()
            source_ref = mp4_file.name
            src_path = workdir / "uploaded.mp4"
            src_path.write_bytes(mp4_file.read())

        with st.spinner("음성(WAV) 추출 중..."):
            wav = extract_wav(src_path, workdir)
            st.success(f"추출 완료: {wav.name}")

        with st.spinner("VITO 화자분리 전사 중(긴 파일은 수 분 소요)..."):
            vito_raw = vito_transcribe(wav)
            utterances = normalize_vito(vito_raw)

        if not speaker_map.strip():
            inferred = infer_speaker_map(utterances)
            st.info("화자-부서 매핑이 비어 있어 자동 템플릿을 제안합니다.")
            st.code(inferred or "화자 없음")
            speaker_map = inferred

        risks = detect_risks(utterances)
        st.subheader("탐지된 리스크(초기)")
        if risks:
            for r in risks:
                st.warning(r)
        else:
            st.info("키워드 기반 리스크가 탐지되지 않았습니다.")

        st.subheader("화자분리 전사")
        st.dataframe([asdict(u) for u in utterances], use_container_width=True)

        with st.spinner("Gemini 요약 생성 중..."):
            summary = gemini_summary(utterances, speaker_map)

        st.subheader("최종 정리 결과")
        st.markdown(summary)

        rec = MeetingRecord(
            created_at=datetime.now(timezone.utc).isoformat(),
            source_type=source_mode,
            source_ref=source_ref,
            risks_json=json.dumps(risks, ensure_ascii=False),
            utterances_json=json.dumps([asdict(u) for u in utterances], ensure_ascii=False),
            summary_md=summary,
        )
        meeting_id = save_meeting(rec)
        st.success(f"저장 완료: 회의록 ID #{meeting_id}")
