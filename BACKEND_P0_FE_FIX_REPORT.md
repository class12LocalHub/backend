# LocalHub Backend P0 / FE Integration Fix Report

- 작업일: 2026-07-14
- 범위: 기존 분석의 P0 및 FE 연동에 직접 영향을 주는 P1
- DB 스키마 변경: 없음
- endpoint URL 변경: 없음
- 기존 게시글 요청 필드 변경: 없음
- `requirements.txt` 변경: 없음

## 변경 결과

### Routing

- `/api/locations/suggestions`를 JSON 동적 장소 경로보다 먼저 등록했다.
- SQLite PK를 조회하던 중복 `/api/locations/{location_id}` 구현을 제거했다.
- `/api/locations/{location_id}`는 기존과 동일하게 TourAPI
  `source_contentid`를 조회하는 JSON 구현 하나만 사용한다.
- 중복 `/api/dashboard`를 제거하고 기존 FE 응답인
  `region`, `total_locations`, `category_counts` 구현 하나로 확정했다.
- 모든 등록 router의 `(HTTP method, path)` 조합이 유일함을 테스트했다.

### FE endpoints

- `GET /api/categories`를 명세 형태로 구현했다.
- `POST /api/chat`을 구현했다. 현재 버전은 저장소의 장소 JSON과 게시글
  SQLite를 검색하는 결정적 응답을 제공하며 외부 네트워크를 요구하지 않는다.
- Map/장소 pagination의 `page`, `size`를 검증해 `size=0`의 500을 422로
  변경했다.
- 게시글 상세 응답에 기존 필드를 유지하면서 `location_id`를 명시하고,
  확장 장소 객체에 `source_id`를 추가했다.
- 게시글 상세 조회 시 `view_count`만 증가하고 `updated_at`은 유지되도록 했다.
- 애플리케이션 오류 응답은 FastAPI의 실제 동작인 `detail` envelope로 문서화했다.

### Location ID contract

- Map POI 및 JSON 장소 API의 `id`: TourAPI `source_contentid`
- suggestions의 `id`: SQLite `locations.id`
- suggestions의 `source_id`: TourAPI `source_contentid`
- 게시글 요청의 `location_id`: SQLite `locations.id`

이 의미를 Pydantic Field 설명, README, API 명세서에 동일하게 기록했다.

### Render / CORS

- `CORS_ORIGINS` 환경변수로 Vue 운영 origin을 쉼표 구분해 설정할 수 있다.
- `LOCALHUB_DB_PATH`로 SQLite 파일 위치를 지정할 수 있다.
- build 단계에서는 의존성만 설치하고, persistent disk에 접근 가능한 runtime
  시작 시 idempotent 장소 seed를 실행한다.
- Render 권장 명령을 다음으로 확정했다.

```text
Build Command: bash build.sh
Start Command: bash start.sh
Health Check Path: /api/health
```

## 파일별 변경 요약

- `app/config.py`: CORS와 SQLite 경로 설정
- `app/database.py`: 환경변수 기반 SQLite 파일 경로
- `app/main.py`: 정적 route 우선순위, categories/chat 등록
- `app/routers/locations.py`: suggestions 전용 router
- `app/routers/items.py`: JSON 장소/Map 전용 및 pagination 검증
- `app/routers/dashboard.py`: 단일 dashboard 구현
- `app/routers/categories.py`: 카테고리 API
- `app/routers/chat.py`, `app/services/chat.py`, `app/schemas/chat.py`: 챗봇 API
- `app/routers/posts.py`, `app/schemas/post.py`: 상세 응답과 장소 ID 명시
- `app/schemas/location.py`: Map ID와 suggestions ID 응답 모델
- `build.sh`, `start.sh`, `.python-version`: Render 실행 경로
- `README.md`, `LocalHub_API_명세서_초안_v0.1.md`: 실행 및 ID 계약 문서
- `tests/test_smoke.py`: 임시 SQLite 기반 회귀 테스트

## Git diff 요약

보고서 작성 직전 tracked file 기준:

```text
13 files changed, 386 insertions(+), 271 deletions(-)
```

신규 파일:

```text
.python-version
app/config.py
app/routers/categories.py
app/schemas/chat.py
start.sh
tests/__init__.py
tests/test_smoke.py
```

`requirements.txt`의 기존 패키지는 모두 보존했다.

## 테스트 결과

### Automated smoke test

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_smoke
```

결과:

```text
Ran 6 tests
OK
```

검증 항목:

- health, categories, dashboard
- Map 목록/필터/상세 및 지역정보 목록/상세
- suggestions 정적 route 우선순위와 초성 검색
- Map TourAPI ID와 게시글 SQLite location ID 분리
- 게시글 생성, 목록, 상세, 수정, 삭제
- 게시글 GET 시 `updated_at` 유지
- 챗봇 장소 응답
- 운영 Vue origin CORS preflight
- 중복 endpoint 부재
- 잘못된 Map page size의 422 응답

### Runtime seed

임시 SQLite 파일에 seed를 실행했다.

```text
전체 신규 적재: 6518건
SQLite SELECT COUNT(*): 6518
```

### Actual Uvicorn HTTP smoke

`bash start.sh`로 runtime seed 후 Uvicorn startup 완료를 확인하고 다음 요청이
모두 200임을 확인했다.

```text
GET /api/health
GET /api/categories
GET /api/locations/suggestions?keyword=ㄱㅂㄱ
GET /api/dashboard
```

### Static checks

```text
Python source syntax: OK
bash -n build.sh: OK
bash -n start.sh: OK
python -m pip check: No broken requirements found
git diff --check: OK
```

FastAPI TestClient 실행 시 현재 설치된 FastAPI 0.139 / Starlette 1.3 조합에서
`httpx2` 전환 예정에 대한 deprecation warning이 한 번 출력되지만 테스트 실패나
runtime API 오류는 아니다.
