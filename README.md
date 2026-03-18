# 📅 자연어 캘린더

자연어로 일정을 입력하면 AI가 분석해서 macOS 캘린더에 자동으로 저장해주는 메뉴바 앱입니다.

## 주요 기능

- **자연어 입력** — "토요일 오후 7시 찬양팀", "내일 치과 예약" 같은 자연스러운 문장으로 일정 등록
- **여러 일정 한 번에** — 쉼표로 구분해서 여러 일정을 한 번에 입력 가능
- **iCloud 동기화** — iCloud 캘린더 사용 시 iPhone에도 자동 반영
- **메뉴바 상주** — 백그라운드에서 메뉴바 아이콘으로 빠르게 접근
- **API 키 검증** — 키 입력 시 실제 동작 여부 즉시 확인

## 사용 방법

1. 메뉴바의 📅 아이콘 클릭
2. **일정 추가** 선택
3. 자연어로 일정 입력 후 저장

### 입력 예시

```
토요일 오후 7시부터 9시까지 찬양팀
내일 오전 10시 치과 예약
3월 25일 발표 준비, 4월 1일 과제 제출
금요일 저녁 7시 친구 약속
```

## 설치 및 실행

### 요구 사항

- macOS
- Python 3.9+
- [Groq API 키](https://console.groq.com) (무료, 카드 등록 불필요)

### Groq API 키 발급 방법

1. [console.groq.com](https://console.groq.com) 접속 후 회원가입
2. 좌측 **API Keys** → **Create API key**
3. 키 복사 후 앱 첫 실행 시 붙여넣기

### 직접 실행

```bash
pip3 install rumps groq
python3 calendar_app.py
```

### .app으로 빌드

```bash
bash build_app.sh
```

빌드 후 `dist/자연어캘린더.app`을 Applications 폴더로 이동하면 됩니다.

> 처음 실행 시 "개발자를 확인할 수 없음" 경고가 뜨면:
> **시스템 설정 → 개인 정보 보호 및 보안 → '확인 없이 열기'** 클릭

## 초기 설정

앱 최초 실행 시 Groq API 키를 입력하면 자동으로 설정이 완료됩니다.
설정은 `~/.자연어캘린더/config.json`에 저장됩니다.

- API 키 변경: 메뉴 → **API 키 변경**
- 캘린더 변경: 메뉴 → **캘린더 변경**

## 기술 스택

| 항목 | 내용 |
|------|------|
| UI | [rumps](https://github.com/jaredks/rumps) (macOS 메뉴바) |
| AI | Groq API (llama-3.3-70b-versatile) |
| 캘린더 연동 | AppleScript |
| 패키징 | PyInstaller |
