# Quality K-Trot Studio

매주 화요일과 금요일에 새로운 **오리지널 한국어 뉴트로 트롯**을 만들고 YouTube에 자동 업로드하는 품질 중심 MVP입니다.

## 무엇을 하나요?

- 기존 유명곡이나 실존 가수의 목소리를 복제하지 않습니다.
- 날짜를 바탕으로 중복되지 않는 한국어 제목과 가사를 만듭니다.
- Kaggle 무료 GPU에서 ACE-Step 1.5로 사람에 가까운 노래와 반주를 함께 생성합니다.
- 매번 다른 색상의 앨범 표지와 움직이는 오디오 파형 영상을 만듭니다.
- GitHub Actions가 최종 마스터링과 YouTube 업로드를 담당합니다.

무료 GPU 상황에 따라 실행 대기 또는 실패가 발생할 수 있습니다. 횟수보다 품질을 우선하여 주 2회만 실행합니다.

## 관리자가 바꾸는 곳

`config/channel.json`에서 가수 이름, 소개, 공개 여부를 수정할 수 있습니다.

YouTube 채널을 바꿀 때는 해당 채널로 발급한 아래 Secret을 교체합니다.

- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

## Kaggle 무료 GPU 연결

GitHub Actions Secrets에 아래 두 값을 한 번 등록해야 합니다.

- `KAGGLE_USERNAME`
- `KAGGLE_KEY`

## 실행 시간

매주 화요일과 금요일 한국 시간 오전 9시에 실행됩니다.
Actions 화면의 `Quality Korean K-trot via free GPU`에서 수동 실행할 수도 있습니다.

## 저작권 원칙

다른 사람이 다시 부르거나 AI 목소리로 바꾸더라도 원곡의 권리는 사라지지 않습니다.
이 저장소는 타인의 최신곡, MR, 음원, 가사 또는 특정 실존 가수의 목소리를 사용하지 않습니다.
