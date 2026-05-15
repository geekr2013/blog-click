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


## 웹페이지로 바로 사용하기 (GitHub 연동 배포)
터미널 실행 대신, **브라우저에서 바로 입출력 가능한 웹앱**으로 배포할 수 있습니다.

### 방법 A) Streamlit Community Cloud (추천)
1. 이 저장소를 GitHub에 push
2. https://share.streamlit.io 접속 후 `New app`
3. Repository: 본 저장소 선택
4. Branch: 배포할 브랜치 선택
5. Main file path: `streamlit_app.py`
6. `Advanced settings > Secrets`에 아래 값 등록
   - `VITO_CLIENT_ID`
   - `VITO_CLIENT_SECRET`
   - `GEMINI_API_KEY`
7. Deploy 클릭

배포가 끝나면 `https://<your-app>.streamlit.app` 주소가 생성되어,
해당 웹페이지에서 YouTube URL/MP4 업로드 입력과 결과 출력이 가능합니다.

### 방법 B) 내부망/서버 배포
- 동일 코드로 사내 VM 또는 클라우드 서버에 `streamlit run streamlit_app.py --server.port 8501` 형태로 올려서 웹페이지 제공 가능.
