#!/bin/bash
set -e

echo "📦 빌드 준비 중..."

# py2app 설치
pip install py2app rumps google-generativeai

# 기존 빌드 정리
rm -rf build dist

echo "🔨 .app 빌드 중... (시간이 좀 걸려요)"
python setup.py py2app

echo "💿 DMG 만드는 중..."
hdiutil create \
  -volname "자연어캘린더" \
  -srcfolder "dist/자연어캘린더.app" \
  -ov \
  -format UDZO \
  "dist/자연어캘린더.dmg"

echo ""
echo "✅ 완료!"
echo "📁 배포 파일: dist/자연어캘린더.dmg"
echo ""
echo "【친구들에게 안내할 내용】"
echo "1. DMG 파일 열기"
echo "2. 자연어캘린더.app을 Applications 폴더로 드래그"
echo "3. 앱 실행 시 '개발자를 확인할 수 없음' 뜨면:"
echo "   → 시스템 설정 > 개인정보 보호 및 보안 > '확인 없이 열기'"
echo "4. Gemini API 키 입력 (앱이 안내해줘요)"
