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

## Description

Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges

On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals

Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation

Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage

Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support

Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap

If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing

State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment

Show your appreciation to those who have contributed to the project.

## License

For open source projects, say how it is licensed.

## Project status

If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.

```
backend
├─ app
│  ├─ crud.py
│  ├─ database.py
│  ├─ main.py
│  ├─ models
│  │  ├─ location.py
│  │  ├─ post.py
│  │  └─ __init__.py
│  ├─ routers
│  │  ├─ chat.py
│  │  ├─ dashboard.py
│  │  ├─ items.py
│  │  ├─ locations.py
│  │  ├─ map.py
│  │  ├─ posts.py
│  │  └─ __init__.py
│  ├─ schemas
│  │  ├─ location.py
│  │  ├─ post.py
│  │  └─ __init__.py
│  ├─ services
│  │  └─ chat.py
│  └─ __init__.py
├─ build.sh
├─ data
│  ├─ locations.json
│  └─ raw
│     ├─ 서울_관광지.json
│     ├─ 서울_레포츠.json
│     ├─ 서울_문화시설.json
│     ├─ 서울_쇼핑.json
│     ├─ 서울_숙박.json
│     ├─ 서울_여행코스.json
│     └─ 서울_축제공연행사.json
├─ LocalHub_API_명세서_초안_v0.1.md
├─ README.md
├─ requirements.txt
└─ scripts
   ├─ seed_locations.py
   └─ __init__.py

```

```
backend
├─ .python-version
├─ app
│  ├─ config.py
│  ├─ crud.py
│  ├─ database.py
│  ├─ main.py
│  ├─ models
│  │  ├─ location.py
│  │  ├─ post.py
│  │  └─ __init__.py
│  ├─ routers
│  │  ├─ categories.py
│  │  ├─ chat.py
│  │  ├─ dashboard.py
│  │  ├─ items.py
│  │  ├─ locations.py
│  │  ├─ map.py
│  │  ├─ posts.py
│  │  └─ __init__.py
│  ├─ schemas
│  │  ├─ chat.py
│  │  ├─ location.py
│  │  ├─ post.py
│  │  └─ __init__.py
│  ├─ services
│  │  └─ chat.py
│  └─ __init__.py
├─ BACKEND_P0_FE_FIX_REPORT.md
├─ build.sh
├─ data
│  ├─ locations.json
│  └─ raw
│     ├─ 서울_관광지.json
│     ├─ 서울_레포츠.json
│     ├─ 서울_문화시설.json
│     ├─ 서울_쇼핑.json
│     ├─ 서울_숙박.json
│     ├─ 서울_여행코스.json
│     └─ 서울_축제공연행사.json
├─ LocalHub_API_명세서_초안_v0.1.md
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ seed_locations.py
│  ├─ seed_posts.py
│  └─ __init__.py
├─ start.sh
└─ tests
   ├─ test_smoke.py
   └─ __init__.py

```