# LocalHub Backend

서울 공공데이터 기반 LocalHub의 FastAPI 백엔드입니다.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
bash start.sh
```

기본 주소는 `http://127.0.0.1:8000`이며 상태 확인 endpoint는
`GET /api/health`입니다.

## Environment variables

```env
# 쉼표로 구분하며 trailing slash 없이 작성합니다.
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://your-vue-app.example.com

# 생략하면 저장소의 data/localhub.db를 사용합니다.
# Render persistent disk 사용 시 /var/data 아래를 권장합니다.
LOCALHUB_DB_PATH=/var/data/localhub.db
```

`data/locations.json`은 Map/지역정보 조회에 사용되는 immutable 데이터이고,
SQLite는 자동완성, 게시글, 게시글-장소 연결에 사용됩니다.

## Location ID contract

- `GET /api/map/pois`와 `GET /api/locations`의 `id`는 TourAPI의
  `source_contentid`입니다.
- `GET /api/locations/suggestions`의 `id`는 SQLite `locations.id`이며,
  게시글 생성·수정 요청의 `location_id`에 사용합니다.
- suggestions의 `source_id`는 TourAPI `source_contentid`로, Map POI의
  `id`와 같은 값입니다.
- Map POI `id`를 게시글 `location_id`로 직접 보내면 안 됩니다.

## Render

저장소 자체가 백엔드 루트이므로 Render의 Root Directory는 비워 둡니다.

```text
Build Command: bash build.sh
Start Command: bash start.sh
Health Check Path: /api/health
```

SQLite 게시글을 재배포·재시작 후에도 보존하려면 persistent disk를
`/var/data`에 mount하고 `LOCALHUB_DB_PATH=/var/data/localhub.db`를 설정합니다.
장소 seed는 중복을 건너뛰므로 매 시작 시 안전하게 실행됩니다.

## Smoke tests

테스트는 임시 SQLite 파일을 사용하며 저장소의 DB를 수정하지 않습니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v tests.test_smoke
```
