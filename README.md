## 회의록 POC 실행

```bash
pip install -r requirements.txt
streamlit run app/poc_meeting_minutes.py
```

환경변수는 `.env.example`를 참고해 `.env`로 구성하세요.

지원 기능:
- YouTube 링크 입력 또는 MP4 업로드
- 트리거 버튼으로 전체 파이프라인 실행
- MP4/YouTube 원본에서 WAV 추출
- VITO API 기반 화자분리 전사
- Gemini 기반 화자별 요약/지시사항 정리
- 초기 리스크 패널 + 자동 리스크 키워드 감지
- 비동기 전사 polling 대응(긴 파일 처리 안정화)
- 화자-부서 매핑 자동 템플릿 제안
- 회의록 SQLite 저장/히스토리 조회/검색
