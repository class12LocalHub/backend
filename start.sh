#!/usr/bin/env bash

set -o errexit

# Render persistent disk는 build 단계에서 접근할 수 없으므로 runtime에
# idempotent seed를 실행한 뒤 서버를 시작한다.
python -m scripts.seed_locations
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
