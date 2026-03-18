#!/bin/bash
echo "📦 자연어 캘린더 앱 빌드 시작..."

# 패키지 설치
pip install rumps google-generativeai pyinstaller

# PyInstaller로 .app 빌드
pyinstaller \
  --windowed \
  --onefile \
  --name "자연어캘린더" \
  --add-data "." \
  calendar_app.py

echo ""
echo "✅ 빌드 완료!"
echo "📁 dist/자연어캘린더.app 파일을 친구들에게 전달하세요."
echo ""
echo "⚠️  친구들에게 전달 시 안내사항:"
echo "1. 앱을 Applications 폴더로 복사"
echo "2. 처음 실행 시 '개발자를 확인할 수 없음' 경고 뜨면:"
echo "   → 시스템 설정 > 개인 정보 보호 및 보안 > '확인 없이 열기' 클릭"
