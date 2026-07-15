# LocalHub API 명세서 초안 v0.1

> 서울 권역 LocalHub MVP 기준  
> 백엔드: FastAPI · SQLAlchemy · SQLite  
> 프론트엔드: Vue.js 3 SPA

---

## 1. 기본 정보

| 항목 | 내용 |
|---|---|
| 서비스명 | LocalHub |
| 백엔드 | FastAPI |
| 데이터베이스 | SQLite |
| ORM | SQLAlchemy |
| 기본 개발 주소 | `http://localhost:8000` |
| API 기본 경로 | `/api` |
| 요청·응답 형식 | JSON |
| 문자 인코딩 | UTF-8 |
| 인증 방식 | 회원 인증 없음 |
| 수정·삭제 권한 | 게시글 작성 시 등록한 비밀번호 확인 |

배포 후 프론트엔드는 환경변수로 백엔드 주소를 관리한다.

```env
VITE_API_BASE_URL=https://localhub-api.onrender.com
```

---

## 2. 전체 API 목록

| 기능 | Method | URL |
|---|---:|---|
| 카테고리 목록 | GET | `/api/categories` |
| 지역정보 목록 | GET | `/api/locations` |
| 지역정보 상세 | GET | `/api/locations/{location_id}` |
| 게시글 목록 | GET | `/api/posts` |
| 게시글 상세 | GET | `/api/posts/{post_id}` |
| 게시글 작성 | POST | `/api/posts` |
| 게시글 수정 | PUT | `/api/posts/{post_id}` |
| 게시글 삭제 | DELETE | `/api/posts/{post_id}` |
| 대시보드 통계 | GET | `/api/dashboard` |
| 챗봇 질문 | POST | `/api/chat` |
| 서버 상태 확인 | GET | `/api/health` |

홈 화면은 별도 API를 만들지 않고 다음 API를 조합한다.

```text
최근 게시글: GET /api/posts?page=1&size=5
카테고리: GET /api/categories
지역정보 수: GET /api/dashboard
```

---

## 3. 공통 카테고리

게시판, 지역정보, 대시보드에서 동일한 카테고리 이름을 사용한다.

```json
[
  "관광지",
  "레포츠",
  "문화시설",
  "쇼핑",
  "숙박",
  "여행코스",
  "축제공연행사"
]
```

정확한 카테고리 명칭은 다음과 같다.

```text
관광지
레포츠
문화시설
쇼핑
숙박
여행코스
축제공연행사
```

다음처럼 다른 명칭은 사용하지 않는다.

```text
축제·행사
축제공연
여행 코스
문화 시설
```

---

## 4. 카테고리 API

### 4.1 카테고리 목록 조회

```http
GET /api/categories
```

#### 응답 예시

```json
{
  "categories": [
    "관광지",
    "레포츠",
    "문화시설",
    "쇼핑",
    "숙박",
    "여행코스",
    "축제공연행사"
  ]
}
```

#### 프론트엔드 사용 위치

- 홈 화면 카테고리 바로가기
- 게시판 목록 카테고리 필터
- 게시글 작성·수정 카테고리 선택창
- 지역정보 검색 필터

---

## 5. 지도 시각화 API

Leaflet.js 기반 관광지·맛집 지도 핀 시각화와 권역 필터를 제공하는 API다. 핀 데이터는 `data/locations.json`을 그대로 조회해 사용한다.

### 장소 ID 계약

- Map API와 JSON 지역정보 API의 `id`는 TourAPI의 `source_contentid`이다.
- `GET /api/locations/suggestions`의 `id`는 SQLite `locations.id`이며,
  게시글 생성·수정의 `location_id`로 사용한다.
- suggestions의 `source_id`는 TourAPI `source_contentid`이므로 Map POI `id`와
  같은 ID 체계이다.
- Map POI `id`와 게시글 `location_id`를 서로 교체해서 사용하지 않는다.

### 5.1 지도 핀 목록 조회

```http
GET /api/map/pois
```

#### Query Parameter

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---:|---:|---|
| `place_type` | string | X | `all` | `all`, `tourist`, `restaurant` 중 하나 |
| `category` | string | X | 전체 | 세부 카테고리 필터 |
| `keyword` | string | X | 없음 | 장소명·주소·태그 검색 |
| `region` | string | X | 전체 | 권역 필터 |
| `bbox` | string | X | 없음 | 현재 지도 영역 `minLng,minLat,maxLng,maxLat` |
| `page` | integer | X | 1 | 현재 페이지 |
| `size` | integer | X | 20 | 한 페이지 개수 |

#### 요청 예시

```http
GET /api/map/pois?place_type=tourist&region=서울&bbox=126.85,37.45,127.10,37.60&page=1&size=20
```

#### 응답 예시

```json
{
  "items": [
    {
      "id": 2611482,
      "name": "150년 수령 느티나무",
      "category": "관광지",
      "address": "서울특별시 양천구 목동중앙본로1길 37 (목동)",
      "summary": "150년 수령 느티나무은(는) 관광지에 속하는 서울 지역정보입니다.",
      "description": "150년 수령 느티나무 관련 관광지 정보입니다. 주소: 서울특별시 양천구 목동중앙본로1길 37 (목동).",
      "telephone": null,
      "homepage": null,
      "latitude": 37.5376778592,
      "longitude": 126.8687762819,
      "region": "서울",
      "place_type": "tourist",
      "firstimage2": "http://tong.visitkorea.or.kr/cms/resource/57/3396257_image3_1.JPG"
    }
  ],
  "total": 6518,
  "page": 1,
  "size": 20,
  "total_pages": 326
}
```

좌표가 JSON에 없으면 해당 항목은 목록에서 제외한다. 현재 구현은 지도에 찍을 수 있는 항목만 반환한다.

#### 프론트엔드 사용 위치

- Leaflet 지도 핀 표시
- 관광지·맛집 목록 패널
- 권역 필터 버튼
- 현재 지도 영역 재조회

---

### 5.2 지도 핀 상세 조회

```http
GET /api/map/pois/{poi_id}
```

#### 요청 예시

```http
GET /api/map/pois/2611482
```

#### 응답 예시

```json
{
  "id": 2611482,
  "name": "150년 수령 느티나무",
  "category": "관광지",
  "address": "서울특별시 양천구 목동중앙본로1길 37 (목동)",
  "summary": "150년 수령 느티나무은(는) 관광지에 속하는 서울 지역정보입니다.",
  "description": "150년 수령 느티나무 관련 관광지 정보입니다. 주소: 서울특별시 양천구 목동중앙본로1길 37 (목동).",
  "telephone": null,
  "homepage": null,
  "latitude": 37.5376778592,
  "longitude": 126.8687762819,
  "region": "서울",
  "place_type": "tourist",
  "firstimage": "http://tong.visitkorea.or.kr/cms/resource/57/3396257_image2_1.JPG",
  "firstimage2": "http://tong.visitkorea.or.kr/cms/resource/57/3396257_image3_1.JPG",
  "source": "TourAPI 4.0 원본 데이터",
  "source_region": "서울",
  "source_contentid": "2611482",
  "source_contenttypeid": "12",
  "source_contenttype": "관광지",
  "zipcode": "07961",
  "createdtime": "20190717201103",
  "modifiedtime": "20250319191708",
  "mlevel": "6",
  "cpyrhtDivCd": "Type3",
  "areacode": "1",
  "sigungucode": "19",
  "lDongRegnCd": "11",
  "lDongSignguCd": "470",
  "cat1": "A01",
  "cat2": "A0102",
  "cat3": "A01020100",
  "lclsSystm1": "NA",
  "lclsSystm2": "NA03",
  "lclsSystm3": "NA030200"
}
```

`source_contentid`, `createdtime`, `modifiedtime`, 이미지, 코드 값 등은 원본 JSON에 존재하는 값이면 그대로 반환한다.

#### 프론트엔드 사용 위치

- 지도 핀 클릭 상세 팝업
- 장소 정보 사이드 패널

---

### 5.3 지도 필터 목록 조회

```http
GET /api/map/filters
```

#### 응답 예시

```json
{
  "place_types": [
    { "value": "all", "label": "전체" },
    { "value": "tourist", "label": "관광지" },
    { "value": "restaurant", "label": "맛집" }
  ],
  "regions": ["서울"],
  "categories": ["관광지", "레포츠", "문화시설", "쇼핑", "숙박", "여행코스", "축제공연행사"]
}
```

#### 프론트엔드 사용 위치

- 지도 필터 드롭다운
- 권역 버튼 그룹
- 관광지/맛집 토글

---

## 6. 지역정보 API

지도 기능 외에 지역정보를 별도로 조회할 때 사용하는 API다.

### 6.1 지역정보 목록 조회

```http
GET /api/locations
```

#### Query Parameter

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---:|---:|---|
| `category` | string | X | 전체 | 카테고리 필터 |
| `keyword` | string | X | 없음 | 장소명·주소 검색 |
| `page` | integer | X | 1 | 현재 페이지 |
| `size` | integer | X | 20 | 한 페이지 개수 |

#### 요청 예시

```http
GET /api/locations?category=관광지&keyword=한강&page=1&size=20
```

#### 응답 예시

```json
{
  "items": [
    {
      "id": 2611482,
      "name": "150년 수령 느티나무",
      "category": "관광지",
      "address": "서울특별시 양천구 목동중앙본로1길 37 (목동)",
      "summary": "150년 수령 느티나무은(는) 관광지에 속하는 서울 지역정보입니다.",
      "latitude": 37.5376778592,
      "longitude": 126.8687762819
    }
  ],
  "total": 783,
  "page": 1,
  "size": 20,
  "total_pages": 40
}
```

좌표가 JSON에 없으면 다음처럼 반환한다.

```json
{
  "latitude": null,
  "longitude": null
}
```

---

### 6.2 지역정보 상세 조회

```http
GET /api/locations/{location_id}
```

#### 요청 예시

```http
GET /api/locations/2611482
```

#### 응답 예시

```json
{
  "id": 2611482,
  "name": "150년 수령 느티나무",
  "category": "관광지",
  "address": "서울특별시 양천구 목동중앙본로1길 37 (목동)",
  "description": "150년 수령 느티나무 관련 관광지 정보입니다. 주소: 서울특별시 양천구 목동중앙본로1길 37 (목동).",
  "telephone": null,
  "homepage": null,
  "latitude": 37.5376778592,
  "longitude": 126.8687762819,
  "start_date": null,
  "end_date": null,
  "source": "TourAPI 4.0 원본 데이터"
}
```

`telephone`, `homepage`, 날짜, 좌표 등은 원본 JSON에 값이 없으면 `null`로 반환한다.

### 6.3 장소 자동완성 및 초성 검색

```http
GET /api/locations/suggestions?keyword=ㄱㅂㄱ&limit=10
```

```json
{
  "items": [
    {
      "id": 15,
      "source_id": "126508",
      "name": "경복궁",
      "category": "관광지",
      "address": "서울특별시 종로구 사직로 161",
      "latitude": 37.579617,
      "longitude": 126.977041,
      "image_url": null,
      "thumbnail_url": null
    }
  ]
}
```

`id`는 게시글 `location_id`에 사용하는 SQLite PK이고,
`source_id`는 Map POI `id`와 같은 TourAPI ID이다.

---

## 6. 게시글 API

### 6.1 게시글 데이터 구조

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | integer | 게시글 번호 |
| `title` | string | 제목 |
| `content` | string | 본문 |
| `category` | string | 카테고리 |
| `password` | string | 수정·삭제 검증용 비밀번호 |
| `created_at` | datetime | 작성일 |
| `updated_at` | datetime | 수정일 |

비밀번호는 데이터베이스에 저장하지만 API 응답에는 포함하지 않는다.

`location_id`는 선택 필드이며, `/api/locations/suggestions` 응답의
`id`(SQLite `locations.id`)를 사용한다. Map POI `id`를 사용하지 않는다.

---

### 6.2 게시글 목록 조회

```http
GET /api/posts
```

#### Query Parameter

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---:|---:|---|
| `category` | string | X | 전체 | 카테고리 필터 |
| `keyword` | string | X | 없음 | 제목·본문 검색 |
| `page` | integer | X | 1 | 현재 페이지 |
| `size` | integer | X | 10 | 페이지당 개수 |
| `sort` | string | X | `latest` | 정렬 방식 |

#### 요청 예시

```http
GET /api/posts?category=레포츠&keyword=한강&page=1&size=10
```

#### 응답 예시

```json
{
  "items": [
    {
      "id": 104,
      "title": "한강에서 즐기는 패들보드 코스",
      "category": "레포츠",
      "created_at": "2026-07-14T10:30:00",
      "updated_at": "2026-07-14T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "total_pages": 1
}
```

현재 필수 범위에서는 조회수와 좋아요 필드를 제외한다.

---

### 6.3 게시글 상세 조회

```http
GET /api/posts/{post_id}
```

#### 요청 예시

```http
GET /api/posts/104
```

#### 응답 예시

```json
{
  "id": 104,
  "title": "한강에서 즐기는 패들보드 코스",
  "content": "주말에 한강에서 패들보드를 체험했습니다.",
  "category": "레포츠",
  "created_at": "2026-07-14T10:30:00",
  "updated_at": "2026-07-14T10:30:00"
}
```

비밀번호는 반환하지 않는다.

---

### 6.4 게시글 작성

```http
POST /api/posts
```

#### 요청 Body

```json
{
  "title": "북촌한옥마을 산책 코스 추천",
  "content": "조용하게 산책하기 좋은 골목을 소개합니다.",
  "category": "관광지",
  "password": "1234"
}
```

#### 유효성 검사

| 필드 | 조건 |
|---|---|
| `title` | 1자 이상, 최대 100자 |
| `content` | 1자 이상 |
| `category` | 지정된 7개 카테고리 중 하나 |
| `password` | 4자 이상 권장 |

#### 성공 응답

```http
201 Created
```

```json
{
  "message": "게시글이 등록되었습니다.",
  "post": {
    "id": 105,
    "title": "북촌한옥마을 산책 코스 추천",
    "content": "조용하게 산책하기 좋은 골목을 소개합니다.",
    "category": "관광지",
    "created_at": "2026-07-14T13:30:00",
    "updated_at": "2026-07-14T13:30:00"
  }
}
```

---

### 6.5 게시글 수정

```http
PUT /api/posts/{post_id}
```

#### 요청 Body

```json
{
  "title": "북촌한옥마을 산책 코스",
  "content": "내용을 수정했습니다.",
  "category": "관광지",
  "password": "1234"
}
```

`password`는 새로운 비밀번호가 아니라 작성할 때 입력한 기존 비밀번호를 확인하기 위한 값이다.

#### 성공 응답

```json
{
  "message": "게시글이 수정되었습니다.",
  "post": {
    "id": 105,
    "title": "북촌한옥마을 산책 코스",
    "content": "내용을 수정했습니다.",
    "category": "관광지",
    "created_at": "2026-07-14T13:30:00",
    "updated_at": "2026-07-14T14:00:00"
  }
}
```

#### 비밀번호 불일치

```http
403 Forbidden
```

```json
{
  "detail": {
    "code": "INVALID_PASSWORD",
    "message": "비밀번호가 일치하지 않습니다."
  }
}
```

---

### 6.6 게시글 삭제

```http
DELETE /api/posts/{post_id}
```

#### 요청 Body

```json
{
  "password": "1234"
}
```

#### 프론트엔드 요청 예시

```javascript
await fetch(`${API_BASE_URL}/api/posts/${postId}`, {
  method: 'DELETE',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    password: inputPassword,
  }),
})
```

#### 성공 응답

```json
{
  "message": "게시글이 삭제되었습니다.",
  "deleted_id": 105
}
```

#### 비밀번호 불일치

```http
403 Forbidden
```

```json
{
  "detail": {
    "code": "INVALID_PASSWORD",
    "message": "비밀번호가 일치하지 않습니다."
  }
}
```

---

## 7. 대시보드 API

댓글 수와 조회수는 제외하고 지역정보 전체 개수와 카테고리별 분포만 제공한다.

### 7.1 대시보드 통계 조회

```http
GET /api/dashboard
```

#### 응답 예시

```json
{
  "region": "서울",
  "total_locations": 1248,
  "category_counts": [
    {
      "category": "관광지",
      "count": 350
    },
    {
      "category": "레포츠",
      "count": 220
    },
    {
      "category": "문화시설",
      "count": 200
    },
    {
      "category": "쇼핑",
      "count": 160
    },
    {
      "category": "숙박",
      "count": 140
    },
    {
      "category": "여행코스",
      "count": 100
    },
    {
      "category": "축제공연행사",
      "count": 78
    }
  ]
}
```

#### 프론트엔드 연결 예시

```javascript
const labels = category_counts.map((item) => item.category)
const data = category_counts.map((item) => item.count)
```

막대그래프와 도넛그래프에서 동일한 데이터를 사용할 수 있다.

---

## 8. 챗봇 API

### 8.1 챗봇 질문 전송

```http
POST /api/chat
```

#### 요청 Body

```json
{
  "message": "서울에서 산책하기 좋은 관광지를 추천해줘",
  "history": [
    {
      "role": "assistant",
      "content": "안녕하세요. 서울 지역정보를 물어보세요."
    }
  ]
}
```

`history`는 선택값으로 설정할 수 있다.

#### 응답 예시

```json
{
  "answer": "서울에서 산책하기 좋은 관광지로 북촌한옥마을과 서울숲을 추천합니다.",
  "query_type": "관광지추천",
  "sources": [
    {
      "type": "location",
      "id": 15,
      "name": "북촌한옥마을",
      "category": "관광지"
    },
    {
      "type": "location",
      "id": 21,
      "name": "서울숲",
      "category": "관광지"
    }
  ]
}
```

### 8.2 챗봇 지원 질문 유형

| 유형 | 질문 예시 | 조회 대상 |
|---|---|---|
| 관광지 추천 | 서울 관광지 추천해줘 | 지역정보 JSON |
| 축제 일정 | 이번 달 축제 알려줘 | 축제공연행사 JSON |
| 장소 위치 | 서울숲 주소 알려줘 | 지역정보 JSON |
| 게시글 검색 | 한강 관련 게시글 찾아줘 | 게시글 DB |
| 숙박 추천 | 서울 숙박시설 추천해줘 | 숙박 JSON |
| 여행코스 | 서울 여행코스 추천해줘 | 여행코스 JSON |

#### 게시글 검색 응답 예시

```json
{
  "answer": "한강과 관련된 게시글 2개를 찾았습니다.",
  "query_type": "게시글검색",
  "sources": [
    {
      "type": "post",
      "id": 104,
      "title": "한강에서 즐기는 패들보드 코스",
      "category": "레포츠"
    },
    {
      "type": "post",
      "id": 98,
      "title": "한강 야경 산책 후기",
      "category": "관광지"
    }
  ]
}
```

#### 응답할 수 없는 경우

```json
{
  "answer": "제공된 서울 지역정보에서 해당 내용을 찾지 못했습니다.",
  "query_type": "unknown",
  "sources": []
}
```

> 확인 필요: 제공 JSON에 음식점 데이터가 없다면 음식점 위치 질문을 정확하게 지원할 수 없다. 실제 제공 데이터에 있는 관광지, 숙박, 쇼핑, 여행코스 등의 질문으로 테스트 항목을 조정한다.

---

## 9. 서버 상태 확인 API

Render 배포 후 백엔드 서버가 정상 실행되는지 확인하는 API다.

```http
GET /api/health
```

#### 응답 예시

```json
{
  "status": "ok",
  "service": "LocalHub API"
}
```

---

## 10. 공통 오류 응답

모든 오류는 가능한 한 동일한 구조로 반환한다.

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "사용자에게 보여줄 오류 메시지"
  }
}
```

| 상태 코드 | 상황 |
|---:|---|
| `200` | 조회·수정·삭제 성공 |
| `201` | 게시글 생성 성공 |
| `400` | 잘못된 요청 |
| `403` | 비밀번호 불일치 |
| `404` | 게시글 또는 지역정보 없음 |
| `422` | 입력값 검증 실패 |
| `500` | 서버 내부 오류 |

### 게시글 없음

```json
{
  "detail": {
    "code": "POST_NOT_FOUND",
    "message": "게시글을 찾을 수 없습니다."
  }
}
```

### 허용되지 않은 카테고리

```json
{
  "detail": {
    "code": "INVALID_CATEGORY",
    "message": "사용할 수 없는 카테고리입니다."
  }
}
```

---

## 11. 화면별 API 연결표

| 프론트엔드 화면 | 사용하는 API |
|---|---|
| 홈 | `GET /api/categories`, `GET /api/posts?size=5` |
| 게시판 목록 | `GET /api/posts` |
| 게시글 상세 | `GET /api/posts/{post_id}` |
| 게시글 작성 | `POST /api/posts` |
| 게시글 수정 | `PUT /api/posts/{post_id}` |
| 게시글 삭제 모달 | `DELETE /api/posts/{post_id}` |
| 대시보드 | `GET /api/dashboard` |
| 챗봇 | `POST /api/chat` |
| 카테고리 바로가기 | `GET /api/locations?category=...` |

---

## 12. 백엔드 담당자와 확정할 사항

1. 게시글 수정 API를 `PUT`으로 할지 `PATCH`로 할지
2. 게시글 목록 한 페이지를 10개로 할지 20개로 할지
3. 제공 JSON의 실제 필드명과 좌표·날짜 존재 여부
4. 챗봇에서 지원할 대표 질문 네 가지
5. 게시글 검색을 제목만 대상으로 할지 제목과 본문 모두 대상으로 할지
6. `DELETE` 요청 Body 사용 여부

현재 초안 기준은 다음과 같다.

```text
수정 방식: PUT
게시글 페이지 크기: 10개
지역정보 페이지 크기: 20개
삭제 비밀번호: DELETE 요청 Body
대시보드: 지역정보 전체 수 + 카테고리별 수
```

---

## 13. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v0.1 | 2026-07-14 | LocalHub MVP API 명세 초안 작성 |
