# Daily K-Trot Robot

매일 새로운 **오리지널 영문 노래**를 만들고 YouTube에 자동 업로드하는 무료 MVP입니다.

## 무엇을 하나요?

- 기존 유명곡을 다운로드하거나 복제하지 않습니다.
- 날짜를 바탕으로 중복되지 않는 제목과 가사를 만듭니다.
- 80~90년대 한국 트로트풍 반주를 직접 합성합니다.
- 무료 `eSpeak NG` 로봇 보컬과 앨범 표지를 만듭니다.
- 완성된 MP4를 GitHub Actions에서 매일 1회 YouTube에 올립니다.

> 이 프로젝트의 음질은 상용 AI 음악 서비스보다 단순합니다. 대신 API 사용료가 없고,
> 원곡 음원을 무단 변형하지 않는 안전한 POC 구조입니다.

## 관리자가 바꾸는 곳

`config/channel.json` 파일만 열어 가수 이름, 소개, 공개 여부 등을 수정하면 됩니다.

YouTube 채널을 바꾸려면 해당 채널로 발급한 GitHub Secret 3개만 교체합니다.

- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

## 실행 시간

매일 한국 시간 오전 9시에 실행됩니다. GitHub 사정에 따라 수십 분 늦을 수 있습니다.
Actions 화면의 `Daily original K-trot upload`에서 수동 실행도 가능합니다.

## 저작권 원칙

다른 사람이 다시 부르거나 AI 목소리로 바꾸더라도 원곡의 작사·작곡 권리는 사라지지
않습니다. 이 저장소는 타인의 최신곡, MR, 음원, 가사 또는 특정 실존 가수의 목소리를
사용하지 않습니다.
