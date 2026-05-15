import json
import os
import re
import sqlite3
import shutil
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


def get_secret(name: str) -> str | None:
    v = os.getenv(name)
    if v:
        return v.strip()
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return None


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
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError(
            "ffmpeg 바이너리를 찾을 수 없습니다. Streamlit Cloud는 packages.txt에 `ffmpeg`를 추가하고 재배포하세요."
        )

    out = workdir / "audio.wav"
    cmd = [
        ffmpeg_bin, "-y", "-i", str(src), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(out),
    ]
    code, _, err = run_cmd(cmd)
    if code != 0:
        raise RuntimeError(f"오디오 추출 실패(ffmpeg 필요): {err}")
    return out


def vito_auth(client_id: str, client_secret: str) -> str:
    # VITO authenticate endpoint expects x-www-form-urlencoded payload.
    token_resp = requests.post(
        "https://openapi.vito.ai/v1/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded", "accept": "application/json"},
        data={"client_id": client_id, "client_secret": client_secret},
        timeout=30,
    )
    if token_resp.status_code >= 400:
        body = token_resp.text[:500]
        raise RuntimeError(f"VITO 인증 실패({token_resp.status_code}). client_id/client_secret 및 Streamlit Secrets 형식을 확인하세요. 응답: {body}")
    return token_resp.json()["access_token"]


def vito_transcribe(audio_path: Path, poll_seconds: int = 2, max_wait_seconds: int = 900) -> dict[str, Any]:
    client_id = get_secret("VITO_CLIENT_ID")
    client_secret = get_secret("VITO_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("VITO_CLIENT_ID / VITO_CLIENT_SECRET 환경변수가 필요합니다.")

    access_token = vito_auth(client_id, client_secret)
    with open(audio_path, "rb") as f:
        transcribe_resp = requests.post(
            "https://openapi.vito.ai/v1/transcribe",
            headers={"Authorization": f"bearer {access_token}"},
            files={"file": f},
            data={"config": json.dumps({"use_diarization": True, "diarization": {"spk_count": 0}})},
            timeout=120,
        )
    transcribe_resp.raise_for_status()
    body = transcribe_resp.json()
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
    return [f"[{u.speaker}] {u.text[:180]}" for u in utterances if any(k in u.text for k in RISK_KEYWORDS)][:20]


def infer_speaker_map(utterances: list[SpeakerUtterance]) -> str:
    speakers = sorted({u.speaker for u in utterances})
    return "\n".join([f"{s}: (부서명 입력 필요)" for s in speakers]) if speakers else ""


def gemini_summary(utterances: list[SpeakerUtterance], speaker_map_text: str) -> str:
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 필요합니다.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    transcript = "\n".join([f"[{u.speaker} {u.start:.1f}-{u.end:.1f}] {u.text}" for u in utterances])
    prompt = f"""화자-부서 매핑:\n{speaker_map_text}\n\n회의 대화:\n{transcript}\n\n화자별 요약표, 액션아이템표, 리스크, 다음 확인질문 5개를 작성."""
    return model.generate_content(prompt).text


def save_meeting(record: MeetingRecord) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO meetings (created_at, source_type, source_ref, risks_json, utterances_json, summary_md) VALUES (?, ?, ?, ?, ?, ?)",
        (record.created_at, record.source_type, record.source_ref, record.risks_json, record.utterances_json, record.summary_md),
    )
    conn.commit()
    meeting_id = cur.lastrowid
    conn.close()
    return int(meeting_id)


def list_meetings(limit: int = 20) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, created_at, source_type, source_ref FROM meetings ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_meeting(meeting_id: int) -> dict[str, Any] | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def render_app() -> None:
    st.set_page_config(page_title="회의록 POC v2", layout="wide")
    init_db()

    st.title("🧭 맥락추적형 회의록 정리 POC v2")
    st.caption("YouTube/MP4 입력 → WAV 추출 → VITO 화자분리 → Gemini 요약 → 히스토리 저장/조회")

    with st.expander("환경변수 점검", expanded=False):
        st.write({
            "VITO_CLIENT_ID": bool(get_secret("VITO_CLIENT_ID")),
            "VITO_CLIENT_SECRET": bool(get_secret("VITO_CLIENT_SECRET")),
            "GEMINI_API_KEY": bool(get_secret("GEMINI_API_KEY")),
        })
        st.caption("Streamlit Cloud에서는 GitHub Secrets가 아니라 App Settings > Secrets에 등록해야 합니다.")

    with st.sidebar:
        st.header("저장된 회의록")
        q = st.text_input("검색(소스/일시)")
        meetings = list_meetings(50)
        if q:
            meetings = [m for m in meetings if q.lower() in (m["source_ref"] + m["created_at"]).lower()]
        for m in meetings[:20]:
            if st.button(f"#{m['id']} {m['created_at']} ({m['source_type']})", key=f"m-{m['id']}"):
                st.session_state["selected_meeting_id"] = m["id"]

    selected_id = st.session_state.get("selected_meeting_id")
    if selected_id:
        selected = get_meeting(int(selected_id))
        if selected:
            st.subheader(f"저장본 조회: #{selected_id}")
            st.markdown(selected["summary_md"])

    source_mode = st.radio("입력 방식", ["YouTube 링크", "MP4 업로드"])
    trigger = st.button("지시사항 정리 실행", type="primary")
    youtube_url = st.text_input("YouTube URL") if source_mode == "YouTube 링크" else None
    mp4_file = st.file_uploader("MP4 업로드", type=["mp4"]) if source_mode == "MP4 업로드" else None
    speaker_map = st.text_area("화자-부서 매핑 (예: 화자-0:개발팀)")

    if trigger:
        try:
            with tempfile.TemporaryDirectory() as td:
                workdir = Path(td)
                if source_mode == "YouTube 링크":
                    if not youtube_url or not re.match(r"^https?://", youtube_url):
                        st.error("유효한 YouTube URL을 입력하세요.")
                        return
                    source_ref = youtube_url
                    src_path = download_youtube(youtube_url, workdir)
                else:
                    if not mp4_file:
                        st.error("MP4 파일을 업로드하세요.")
                        return
                    source_ref = mp4_file.name
                    src_path = workdir / "uploaded.mp4"
                    src_path.write_bytes(mp4_file.read())

                wav = extract_wav(src_path, workdir)
                vito_raw = vito_transcribe(wav)
                utterances = normalize_vito(vito_raw)
                if not speaker_map.strip():
                    speaker_map = infer_speaker_map(utterances)
                risks = detect_risks(utterances)
                st.dataframe([asdict(u) for u in utterances], use_container_width=True)
                summary = gemini_summary(utterances, speaker_map)
                st.markdown(summary)
                meeting_id = save_meeting(
                    MeetingRecord(
                        created_at=datetime.now(timezone.utc).isoformat(),
                        source_type=source_mode,
                        source_ref=source_ref,
                        risks_json=json.dumps(risks, ensure_ascii=False),
                        utterances_json=json.dumps([asdict(u) for u in utterances], ensure_ascii=False),
                        summary_md=summary,
                    )
                )
                st.success(f"저장 완료: 회의록 ID #{meeting_id}")
        except Exception as e:
            st.error(f"처리 중 오류: {e}")


if __name__ == "__main__":
    render_app()
