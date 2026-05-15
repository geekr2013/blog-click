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


### ffmpeg 오류 해결 (No such file or directory: 'ffmpeg')
Streamlit Cloud 배포 시 시스템 패키지가 필요하므로 저장소 루트에 `packages.txt`를 두고 아래를 넣어야 합니다.

```
ffmpeg
```

이미 반영되어 있으니, 배포 화면에서 **Reboot app / Redeploy**를 실행하세요.


### 환경변수 오류 해결 (VITO_CLIENT_ID / VITO_CLIENT_SECRET 필요)
중요: **Streamlit Community Cloud 앱은 GitHub Repository Secrets를 자동으로 읽지 않습니다.**
반드시 Streamlit 앱의 `App settings > Secrets`에 아래를 등록하세요.

```toml
VITO_CLIENT_ID = "..."
VITO_CLIENT_SECRET = "..."
GEMINI_API_KEY = "..."
```

그리고 앱을 Reboot 하면 반영됩니다.


### VITO 인증 400 Bad Request 오류 해결
VITO `/v1/authenticate`는 `application/x-www-form-urlencoded` 형식을 요구합니다.
코드는 해당 형식으로 반영되어 있습니다.

추가 점검:
1. Streamlit `App settings > Secrets` 값에 따옴표/공백/줄바꿈 오타가 없는지
2. 발급받은 키가 RTZR/VITO 콘솔의 **현재 활성 키**인지
3. 키 복사 시 앞뒤 공백이 들어가지 않았는지


### Gemini 404 모델 오류 해결
`GEMINI_MODEL`을 Streamlit Secrets에 지정할 수 있습니다. (예: `gemini-2.0-flash`)
앱은 `ListModels`로 사용 가능한 모델을 조회해 자동 fallback도 수행합니다.


### Gemini 429(무료 할당량 초과) 대응
현재 오류는 **무료 티어 할당량이 0 또는 초과**된 상태라서 발생한 것입니다.
즉, 코드 문제가 아니라 계정/플랜 제한 문제일 수 있습니다.

대응 옵션:
1. Gemini 유료 결제/할당량 상향
2. OpenAI로 폴백 (권장)

Streamlit Secrets 예시:
```toml
LLM_PROVIDER = "gemini"
OPENAI_API_KEY = "..."
OPENAI_MODEL = "gpt-4.1-mini"
```

앱은 기본적으로 Gemini를 먼저 시도하고, Gemini가 실패하면 `OPENAI_API_KEY`가 있을 때 자동으로 OpenAI로 폴백합니다.
원하면 `LLM_PROVIDER = "openai"`로 OpenAI 우선 사용도 가능합니다.


### OpenAI 429 insufficient_quota 오류 해결
이 오류는 코드 문제가 아니라 **계정 사용량/결제 한도** 문제입니다.

대응:
1. OpenAI 결제/한도 설정 확인
2. Gemini 사용 가능 시 `LLM_PROVIDER="gemini"`
3. 둘 다 실패할 경우 앱은 **규칙기반 요약(fallback)** 으로 자동 대체되어 화면 출력은 계속됩니다.


### 완전 무료 모드로 사용하기 (권장 기본값)
외부 LLM 과금 없이 사용하려면 아래처럼 설정하세요.

```toml
LLM_PROVIDER = "rule"
```

이 모드에서는 앱 내 **규칙기반 요약 엔진**이 동작하며, 아래 결과를 제공합니다.
- 화자별 요약
- 부서/주제별 요약
- 리스크 키워드 정리
- 액션아이템 초안

즉, 유료 API 키가 없어도 웹UI에서 최종 정리 결과를 계속 받을 수 있습니다.
