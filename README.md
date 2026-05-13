# blog-click (Policy-safe automation)

광고 클릭/트래픽 조작 없이, **네이버 블로그 운영 자동화**를 위한 저장소입니다.

## 자동화 파이프라인
1. 매일 스케줄로 `scripts/generate_post_assets.py` 실행
2. `outbox/YYYY-MM-DD/`에 아래 파일 자동 생성
   - `post.md` (본문 초안)
   - `cover.svg` (커버 이미지)
   - `meta.json` (제목/태그/메타)
3. Playwright 기반 브라우저 자동화로 네이버 블로그 에디터 진입
4. 제목/본문/이미지 업로드 후 발행 버튼 클릭

## GitHub Actions
- `.github/workflows/naver-auto-post.yml`
- 한국시간 매일 08:00, 11:00, 16:00 자동 실행 + 수동 실행(workflow_dispatch)

## 최초 1회 설정(필수)
GitHub 저장소 `Settings > Secrets and variables > Actions`에 아래 Secret 추가:
- `NAVER_BLOG_ID` (예: `hi_chk`)
- `NAVER_ID`
- `NAVER_PASSWORD`

## 중요 안내
- 네이버 로그인 정책(캡차/2차 인증/보안 알림)에 따라 자동 발행이 실패할 수 있습니다.
- UI 변경 시 선택자(selector)를 `scripts/naver_publish.mjs`에서 업데이트해야 합니다.
- 이 저장소는 광고 클릭 자동화 기능을 제공하지 않습니다.


## 실제 발행에 필요한 입력값 (필수)
아래 3개 값이 있어야 `Naver Auto Post` 워크플로우가 발행까지 진행됩니다.

1. `NAVER_BLOG_ID`
   - 값 수집 방법: 블로그 주소 `https://blog.naver.com/<여기값>`에서 `<여기값>`을 그대로 사용
   - 현재 당신의 경우: `hi_chk`
2. `NAVER_ID`
   - 값 수집 방법: 네이버 로그인에 사용하는 아이디
3. `NAVER_PASSWORD`
   - 값 수집 방법: 해당 계정 비밀번호

### 어디에 입력하나요?
GitHub 저장소에서 아래 순서로 등록하세요.
1. `Settings` 탭
2. `Secrets and variables` → `Actions`
3. `New repository secret`
4. 이름/값 입력 후 저장

### 최대한 자동으로 처리되게 한 부분
- 글 초안/이미지/메타 생성: 자동 (`scripts/generate_post_assets.py`)
- 발행 실행: 자동 (`scripts/naver_publish.mjs`)
- 매일 실행: 자동 (`.github/workflows/naver-auto-post.yml`)

### 1회 점검 방법 (강력 권장)
워크플로우에 아래 단계를 넣어두거나 로컬에서 실행:
- `python scripts/preflight_check.py`

이 스크립트는 필수 값이 누락되었는지 즉시 알려줍니다.

### 실패 시 가장 흔한 원인
- 네이버 보안 정책(캡차/2차 인증/새 기기 로그인 차단)
- 에디터 UI 변경으로 선택자 불일치

문제가 발생하면 `scripts/naver_publish.mjs`의 selector를 최신 UI 기준으로 조정해야 합니다.


## 글 생성 지침을 쉽게 변경하는 방법
- 모든 지침은 `config/content_guidelines.json`에서 관리됩니다.
- 바꿀 수 있는 항목:
  - 톤/페르소나
  - 글 구조 규칙
  - 해시태그 개수
  - 이슈 후보(`issues_pool`)
- 스크립트 `scripts/generate_post_assets.py`는 위 파일을 읽어 글을 생성하므로, 코드 수정 없이 지침만 바꿔도 즉시 반영됩니다.


## 이미지 생성 방식
- 우선 `source.unsplash.com`에서 주제 기반 실사 이미지를 자동 다운로드(`cover.jpg`)합니다.
- 네트워크 문제 시에만 `cover.svg`를 폴백으로 생성합니다.
- 발행 스크립트는 `meta.json`의 `cover_image` 값을 읽어 자동 업로드합니다.


## Windows에서 `src refspec work does not match any` 오류가 날 때
이 오류는 로컬에 `work` 브랜치가 없는데 `git push origin work`를 실행했을 때 발생합니다.

해결:
1. 현재 브랜치 확인: `git branch --show-current`
2. `main`이라면: `git push -u origin main`
3. 또는 새 브랜치 생성 후 푸시: `git checkout -b work && git push -u origin work`
