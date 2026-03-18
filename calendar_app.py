#!/usr/bin/env python3
import rumps
from google import genai
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
        # 환영 안내
        rumps.alert(
            title="📅 자연어 캘린더에 오신 걸 환영해요!",
            message=(
                "자연어로 일정을 입력하면\n"
                "AI가 분석해서 캘린더에 저장해줘요.\n\n"
                "시작하려면 무료 Gemini API 키가 필요해요.\n\n"
                "① aistudio.google.com/apikey 접속\n"
                "② 'Create API key' 클릭\n"
                "③ 키 복사 후 다음 화면에 붙여넣기"
            )
        )
        self.prompt_api_key(is_first=True)

    def validate_api_key(self, key):
        """API 키가 실제로 동작하는지 테스트"""
        try:
            client = genai.Client(api_key=key)
            client.models.generate_content(model="gemini-2.0-flash", contents="hi")
            return True, None
        except Exception as e:
            return False, str(e)

    def prompt_api_key(self, is_first=False):
        key = ask_input(
            "🔑 API 키 입력",
            "Gemini API 키를 붙여넣기 하세요.\n(aistudio.google.com/apikey 에서 무료 발급)"
        )

        if key and key.strip():
            rumps.alert("🔄 확인 중...", "API 키를 검증하고 있어요. 잠시만 기다려주세요.")
            valid, error = self.validate_api_key(key.strip())

            if not valid:
                rumps.alert("❌ API 키 오류", f"키가 유효하지 않아요.\n\n오류: {error}\n\naistudio.google.com/apikey 에서 키를 다시 확인해보세요.")
                return

            self.config["api_key"] = key.strip()

            # 캘린더 자동 감지
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
            client = genai.Client(api_key=self.config["api_key"])
            today = datetime.now().strftime("%Y년 %m월 %d일 (%A)")

            prompt = f"""오늘은 {today}이야. 아래 텍스트에서 일정들을 추출해서 반드시 JSON 배열 형식으로만 답해줘. 다른 말은 절대 하지 마.

형식:
[
  {{"title": "일정제목", "date": "YYYY-MM-DD", "time": "HH:MM", "duration": 60}},
  ...
]

시간이 없으면 time을 "09:00"으로 설정해줘.
날짜가 "월요일"처럼 요일로 되어있으면 이번주 해당 요일 날짜로 변환해줘.

일정 텍스트: {text}"""

            message = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            result = message.text.strip()

            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]

            events = json.loads(result.strip())
            calendar_name = self.config.get("calendar_name") or get_default_calendar()

            saved_count = 0
            for event in events:
                if self.save_to_calendar(event, calendar_name):
                    saved_count += 1

            if saved_count > 0:
                rumps.alert("✅ 저장 완료!", f"{saved_count}개의 일정이 '{calendar_name}' 캘린더에 저장됐어요.")
            else:
                rumps.alert("⚠️ 저장 실패", "캘린더에 저장하지 못했어요.\n\n캘린더 접근 권한을 확인해주세요.\n시스템 설정 → 개인 정보 보호 및 보안 → 캘린더")

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
                    set month of startDate to {start_dt.month}
                    set day of startDate to {start_dt.day}
                    set hours of startDate to {start_dt.hour}
                    set minutes of startDate to {start_dt.minute}
                    set seconds of startDate to 0

                    set endDate to current date
                    set year of endDate to {end_dt.year}
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
            return result.returncode == 0

        except Exception as e:
            print(f"캘린더 저장 오류: {e}")
            return False

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
                "aistudio.google.com/apikey"
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
