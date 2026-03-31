#!/usr/bin/env python3
import rumps
from groq import Groq
import subprocess
import json
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path.home() / ".자연어캘린더"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_all_calendars():
    """AppleScript으로 캘린더 목록 가져오기"""
    script = 'tell application "Calendar" to get name of every calendar'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0:
        names = result.stdout.strip().split(", ")
        return [n.strip() for n in names if n.strip()]
    return []


def get_default_calendar():
    """AppleScript으로 첫 번째 캘린더 이름 가져오기"""
    calendars = get_all_calendars()
    return calendars[0] if calendars else "캘린더"


def ask_input(title, message, default=""):
    """붙여넣기 가능한 네이티브 입력창 (AppleScript)"""
    safe_message = message.replace('"', '\\"')
    safe_default = default.replace('"', '\\"')
    script = f'''
    tell application "System Events"
        activate
        set dlg to display dialog "{safe_message}" with title "{title}" default answer "{safe_default}" buttons {{"취소", "저장"}} default button "저장"
        if button returned of dlg is "저장" then
            return text returned of dlg
        end if
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None  # 취소


class CalendarApp(rumps.App):
    def __init__(self):
        super().__init__("📅")
        self.config = load_config()
        self.menu = ["일정 추가", None, "도움말", "API 키 변경", "캘린더 변경", None, "종료"]

        if not self.config.get("api_key"):
            self.first_setup()

    def first_setup(self):
        rumps.alert(
            title="📅 자연어 캘린더에 오신 걸 환영해요!",
            message=(
                "자연어로 일정을 입력하면\n"
                "AI가 분석해서 캘린더에 저장해줘요.\n\n"
                "시작하려면 무료 Groq API 키가 필요해요.\n\n"
                "① console.groq.com 접속 후 회원가입\n"
                "② 'API Keys' 메뉴 → 'Create API key'\n"
                "③ 키 복사 후 다음 화면에 붙여넣기"
            )
        )
        self.prompt_api_key(is_first=True)

    def validate_api_key(self, key):
        """API 키가 실제로 동작하는지 테스트"""
        try:
            client = Groq(api_key=key)
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            return True, None
        except Exception as e:
            return False, str(e)

    def prompt_api_key(self, is_first=False):
        key = ask_input(
            "🔑 API 키 입력",
            "Groq API 키를 붙여넣기 하세요.\n(console.groq.com 에서 무료 발급)"
        )

        if key and key.strip():
            rumps.alert("🔄 확인 중...", "API 키를 검증하고 있어요. 잠시만 기다려주세요.")
            valid, error = self.validate_api_key(key.strip())

            if not valid:
                rumps.alert("❌ API 키 오류", f"키가 유효하지 않아요.\n\n오류: {error}\n\nconsole.groq.com 에서 키를 다시 확인해보세요.")
                return

            self.config["api_key"] = key.strip()

            if not self.config.get("calendar_name"):
                self.config["calendar_name"] = get_default_calendar()

            save_config(self.config)

            if is_first:
                rumps.alert(
                    title="✅ 설정 완료!",
                    message=(
                        f"캘린더: {self.config['calendar_name']}\n\n"
                        "메뉴바 📅 → 일정 추가로 시작하세요!\n"
                        "캘린더 변경은 메뉴에서 할 수 있어요."
                    )
                )
            else:
                rumps.alert("✅ API 키 변경 완료!", "새 API 키가 정상적으로 확인됐어요.")
        else:
            if is_first:
                rumps.alert("⚠️ API 키 없이는 사용할 수 없어요.", "나중에 메뉴에서 설정할 수 있어요.")

    @rumps.clicked("일정 추가")
    def add_event(self, _):
        if not self.config.get("api_key"):
            self.prompt_api_key()
            return

        text = ask_input(
            "📅 일정 추가",
            "일정을 자연어로 입력하세요.\n예: 월요일 과제 제출, 화요일 오후 8시 동아리 회의"
        )

        if text and text.strip():
            self.process_events(text.strip())

    def process_events(self, text):
        try:
            client = Groq(api_key=self.config["api_key"])
            from datetime import timedelta
            now = datetime.now()
            korean_weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
            today_str = now.strftime("%Y-%m-%d") + f" ({korean_weekdays[now.weekday()]})"
            week_start = now - timedelta(days=now.weekday())
            week_dates = "\n".join(
                f"- {korean_weekdays[i]}: {(week_start + timedelta(days=i)).strftime('%Y-%m-%d')}"
                for i in range(7)
            )
            tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            day_after = (now + timedelta(days=2)).strftime("%Y-%m-%d")

            prompt = f"""오늘은 {today_str}이야. 아래 텍스트에서 일정들을 추출해서 반드시 JSON 배열 형식으로만 답해줘. 다른 말은 절대 하지 마.

형식:
[
  {{"title": "일정제목", "date": "YYYY-MM-DD", "time": "HH:MM", "duration": 60}},
  ...
]

이번주 날짜 (계산하지 말고 아래 값을 그대로 사용해):
{week_dates}
- 내일: {tomorrow}
- 모레: {day_after}

규칙:
- date는 반드시 "2026-03-21" 같은 YYYY-MM-DD 숫자 형식으로만 써. 절대 "토요일", "월요일" 같은 한글을 쓰지 마.
- 요일로 표현된 날짜는 위의 이번주 날짜 표를 그대로 참조해서 변환해. 직접 계산하지 마.
- "내일", "모레"도 위의 값을 그대로 사용해.
- 시간이 없으면 time을 "09:00"으로 설정해줘.
- "오후 7시부터 9시까지"처럼 종료 시간이 있으면 duration을 분 단위로 계산해줘.

일정 텍스트: {text}"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content.strip()

            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]

            events = json.loads(result.strip())
            calendar_name = self.config.get("calendar_name") or get_default_calendar()

            saved_count = 0
            errors = []
            for event in events:
                success, err = self.save_to_calendar(event, calendar_name)
                if success:
                    saved_count += 1
                else:
                    errors.append(err)

            if saved_count > 0:
                rumps.alert("✅ 저장 완료!", f"{saved_count}개의 일정이 '{calendar_name}' 캘린더에 저장됐어요.")
            else:
                error_detail = "\n".join(errors) if errors else "알 수 없는 오류"
                rumps.alert("⚠️ 저장 실패", f"캘린더: '{calendar_name}'\n\n오류: {error_detail}")

        except json.JSONDecodeError as e:
            rumps.alert("❌ 파싱 오류", f"AI 응답을 해석하지 못했어요. 다시 시도해주세요.\n\n{str(e)}")
        except Exception as e:
            rumps.alert("❌ 오류 발생", str(e))

    def save_to_calendar(self, event, calendar_name):
        try:
            title = event.get("title", "새 일정")
            date = event.get("date", datetime.now().strftime("%Y-%m-%d"))
            time_str = event.get("time", "09:00")
            duration = event.get("duration", 60)

            start_dt = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
            end_hour = start_dt.hour + (duration // 60)
            end_minute = (start_dt.minute + duration) % 60

            end_dt = start_dt.replace(hour=end_hour, minute=end_minute)

            applescript = f'''
            tell application "Calendar"
                tell calendar "{calendar_name}"
                    set startDate to current date
                    set year of startDate to {start_dt.year}
                    set day of startDate to 1
                    set month of startDate to {start_dt.month}
                    set day of startDate to {start_dt.day}
                    set hours of startDate to {start_dt.hour}
                    set minutes of startDate to {start_dt.minute}
                    set seconds of startDate to 0

                    set endDate to current date
                    set year of endDate to {end_dt.year}
                    set day of endDate to 1
                    set month of endDate to {end_dt.month}
                    set day of endDate to {end_dt.day}
                    set hours of endDate to {end_dt.hour}
                    set minutes of endDate to {end_dt.minute}
                    set seconds of endDate to 0

                    make new event with properties {{summary:"{title}", start date:startDate, end date:endDate, allday event:false}}
                end tell
            end tell
            '''

            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip() or "AppleScript 실행 실패"

        except Exception as e:
            return False, str(e)

    @rumps.clicked("도움말")
    def show_help(self, _):
        rumps.alert(
            title="📅 자연어 캘린더 도움말",
            message=(
                "【사용 방법】\n"
                "메뉴바 📅 아이콘 → 일정 추가 클릭\n"
                "자연어로 일정 입력 → 저장\n\n"
                "【입력 예시】\n"
                "• 월요일 오후 3시 팀 미팅\n"
                "• 내일 오전 10시 치과 예약\n"
                "• 금요일 저녁 7시 친구 약속\n"
                "• 3월 25일 발표 준비, 4월 1일 과제 제출\n\n"
                "【여러 일정 한 번에】\n"
                "쉼표로 구분해서 한 번에 입력 가능해요!\n\n"
                "【iPhone 동기화】\n"
                "iCloud 켜져 있으면 iPhone 캘린더에\n"
                "자동으로 반영돼요.\n\n"
                "【API 키 발급 (무료)】\n"
                "console.groq.com"
            )
        )

    @rumps.clicked("API 키 변경")
    def change_api_key(self, _):
        self.prompt_api_key(is_first=False)

    @rumps.clicked("캘린더 변경")
    def change_calendar(self, _):
        calendars = get_all_calendars()
        current = self.config.get("calendar_name", "")

        calendar_list = "\\n".join(f"• {c}" for c in calendars)
        name = ask_input(
            "📆 캘린더 변경",
            f"사용할 캘린더 이름을 입력하세요.\\n\\n현재 캘린더 목록:\\n{calendar_list}",
            default=current
        )

        if name and name.strip():
            self.config["calendar_name"] = name.strip()
            save_config(self.config)
            rumps.alert("✅ 변경 완료!", f"'{self.config['calendar_name']}' 캘린더로 설정됐어요.")

    @rumps.clicked("종료")
    def quit_app(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    CalendarApp().run()
