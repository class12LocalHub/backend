#!/usr/bin/env bash

set -o errexit

# Render persistent disk는 build 단계에서 접근할 수 없으므로 runtime에
# idempotent seed를 실행한 뒤 서버를 시작한다.

echo "🌱 Seeding locations data..."
python -m scripts.seed_locations

echo "🌱 Seeding posts data..."
python -m scripts.seed_posts  # 💡 여기에 게시글 시드 명령어를 추가합니다!

echo "🚀 Starting FastAPI Application..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"