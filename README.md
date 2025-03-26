# YouTube 일본어 음성 자막 추출 및 번역기

일본어 유튜브 영상을 입력하면 다음 과정을 자동으로 수행하는 Python 기반 도구

1. **오디오 다운로드**: 유튜브에서 오디오 추출 및 mp3 변환
2. **오디오 분할**: Whisper로 처리하기 쉽게 mp3 파일을 여러 조각으로 분할
3. **음성 인식**: OpenAI Whisper를 사용해 일본어 음성을 텍스트로 변환
4. **번역**: Google Translate 또는 Naver Papago를 사용해 한국어로 번역
5. **저장**: 타임싱크 포함 텍스트 파일로 저장

---

## 주요 기능

- Whisper 모델 사용 (`tiny`, `small`, `medium`, `large` 선택 가능)
- Papago API 또는 Google Translate 선택 가능
- 긴 영상도 자동 분할 처리
- 타임코드 포함 번역 결과 출력


⚠️ ffmpeg는 시스템에 따로 설치되어 있어야 함
(Ubuntu: sudo apt install ffmpeg, Windows: ffmpeg 바이너리 추가)

---

## 실행 후 입력 예시
유튜브 링크 입력: https://www.youtube.com/watch?v=xxxxx  
Papago API를 사용할까요? (y/n): y //n 입력하면 구글 번역기 사용  
Papago Client ID 입력: [입력]  
Papago Client Secret 입력: [입력]  
Whisper 모델 크기 선택 (tiny/small/medium/large): small  
번역 결과는 translated.txt 파일로 저장됨

---

## 출력 예시 (translated.txt)
[7.50 - 13.20]
일본어: 今から発表を始めます。
한국어: 지금부터 발표를 시작하겠습니다.
