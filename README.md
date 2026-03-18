# 📅 자연어 캘린더

자연어로 일정을 입력하면 Gemini AI가 분석해서 macOS 캘린더에 자동으로 저장해주는 메뉴바 앱입니다.

## 주요 기능

- **자연어 입력** — "월요일 오후 3시 팀 미팅", "내일 치과 예약" 같은 자연스러운 문장으로 일정 등록
- **여러 일정 한 번에** — 쉼표로 구분해서 여러 일정을 한 번에 입력 가능
- **iCloud 동기화** — iCloud 캘린더 사용 시 iPhone에도 자동 반영
- **메뉴바 상주** — 백그라운드에서 메뉴바 아이콘으로 빠르게 접근

## 사용 방법

1. 메뉴바의 📅 아이콘 클릭
2. **일정 추가** 선택
3. 자연어로 일정 입력 후 저장

### 입력 예시

```
월요일 오후 3시 팀 미팅
내일 오전 10시 치과 예약
3월 25일 발표 준비, 4월 1일 과제 제출
금요일 저녁 7시 친구 약속
```

## 설치 및 실행

### 요구 사항

- macOS
- Python 3.8+
- [Gemini API 키](https://aistudio.google.com/apikey) (무료)

### 직접 실행

```bash
pip install rumps google-genai
python calendar_app.py
```

### .app으로 빌드

```bash
bash build_app.sh
```

빌드 후 `dist/자연어캘린더.app`을 Applications 폴더로 이동하면 됩니다.

### DMG 패키징

```bash
bash build_dmg.sh
```

## 초기 설정

앱 최초 실행 시 Gemini API 키를 입력하면 자동으로 설정이 완료됩니다.
API 키는 `~/.자연어캘린더/config.json`에 저장됩니다.

- API 키 변경: 메뉴 → **API 키 변경**
- 캘린더 변경: 메뉴 → **캘린더 변경**

## 기술 스택

| 항목 | 내용 |
|------|------|
| UI | [rumps](https://github.com/jaredks/rumps) (macOS 메뉴바) |
| AI | Google Gemini 2.5 Flash |
| 캘린더 연동 | AppleScript |
| 패키징 | PyInstaller |
