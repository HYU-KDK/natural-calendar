from setuptools import setup

APP = ['calendar_app.py']
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'LSUIElement': True,  # 독(Dock)에 아이콘 숨김 (메뉴바 앱)
        'CFBundleName': '자연어캘린더',
        'CFBundleDisplayName': '자연어캘린더',
        'CFBundleIdentifier': 'com.user.자연어캘린더',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSCalendarsUsageDescription': '일정을 Apple 캘린더에 저장하기 위해 접근합니다.',
        'NSUserNotificationAlertStyle': 'alert',
    },
    'packages': [
        'rumps',
        'google',
        'google.generativeai',
        'google.ai',
        'google.api_core',
        'google.auth',
        'google.protobuf',
    ],
    'includes': ['google.generativeai'],
}

setup(
    app=APP,
    name='자연어캘린더',
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
