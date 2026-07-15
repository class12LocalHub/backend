from __future__ import annotations

import json
from functools import lru_cache
from math import ceil
from pathlib import Path
from typing import Any
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.post import Post


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "locations.json"
MAP_PLACE_TYPES = {
	"관광지": "tourist",
	"레포츠": "tourist",
	"문화시설": "tourist",
	"숙박": "tourist",
	"여행코스": "tourist",
	"축제공연행사": "tourist",
	"쇼핑": "tourist",
	"음식점": "restaurant",
}

MAP_PLACE_TYPE_LABELS = {
	"all": "전체",
	"tourist": "관광지",
	"restaurant": "맛집",
}

DEFAULT_CATEGORIES = [
	"관광지",
	"레포츠",
	"문화시설",
	"쇼핑",
	"숙박",
	"여행코스",
	"축제공연행사",
	"음식점",
]


@lru_cache(maxsize=1)
def load_locations() -> list[dict[str, Any]]:
	if not DATA_FILE.exists():
		return []

	with DATA_FILE.open("r", encoding="utf-8") as file:
		data = json.load(file)

	if isinstance(data, list):
		return [item for item in data if isinstance(item, dict)]

	return []


def normalize_text(value: str | None) -> str:
	return (value or "").strip().lower()


def to_int(value: Any) -> int | None:
	try:
		if value is None:
			return None
		return int(str(value))
	except (TypeError, ValueError):
		return None


def to_float(value: Any) -> float | None:
	try:
		if value is None:
			return None
		text = str(value).strip()
		if not text:
			return None
		return float(text)
	except (TypeError, ValueError):
		return None


def derive_place_type(item: dict[str, Any]) -> str:
	category = str(item.get("category") or item.get("source_contenttype") or "").strip()
	return MAP_PLACE_TYPES.get(category, "tourist")


def parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
	if not bbox:
		return None

	parts = [part.strip() for part in bbox.split(",")]
	if len(parts) != 4:
		return None

	try:
		min_lng, min_lat, max_lng, max_lat = (float(part) for part in parts)
	except ValueError:
		return None

	return min_lng, min_lat, max_lng, max_lat


def build_location_payload(item: dict[str, Any]) -> dict[str, Any]:
	source_contentid = str(item.get("source_contentid") or "").strip()
	id_value = to_int(source_contentid)

	return {
		"id": id_value if id_value is not None else source_contentid,
		"source_region": item.get("source_region"),
		"source_contentid": source_contentid or None,
		"source_contenttypeid": item.get("source_contenttypeid"),
		"source_contenttype": item.get("source_contenttype"),
		"name": item.get("name"),
		"place_type": derive_place_type(item),
		"category": item.get("category"),
		"address": item.get("address"),
		"summary": item.get("summary"),
		"description": item.get("description"),
		"telephone": item.get("telephone"),
		"homepage": item.get("homepage"),
		"latitude": item.get("latitude"),
		"longitude": item.get("longitude"),
		"region": item.get("source_region"),
		"source": item.get("source"),
		"firstimage": item.get("firstimage"),
		"firstimage2": item.get("firstimage2"),
		"zipcode": item.get("zipcode"),
		"createdtime": item.get("createdtime"),
		"modifiedtime": item.get("modifiedtime"),
		"mlevel": item.get("mlevel"),
		"cpyrhtDivCd": item.get("cpyrhtDivCd"),
		"areacode": item.get("areacode"),
		"sigungucode": item.get("sigungucode"),
		"lDongRegnCd": item.get("lDongRegnCd"),
		"lDongSignguCd": item.get("lDongSignguCd"),
		"cat1": item.get("cat1"),
		"cat2": item.get("cat2"),
		"cat3": item.get("cat3"),
		"lclsSystm1": item.get("lclsSystm1"),
		"lclsSystm2": item.get("lclsSystm2"),
		"lclsSystm3": item.get("lclsSystm3"),
		"search_tags": item.get("search_tags") or [],
	}


def matches_filters(
	item: dict[str, Any],
	*,
	category: str | None = None,
	keyword: str | None = None,
	region: str | None = None,
	place_type: str | None = None,
	bbox: str | None = None,
) -> bool:
	if category and str(item.get("category")) != category:
		return False

	if place_type and place_type != "all":
		if derive_place_type(item) != place_type:
			return False

	if region:
		region_text = normalize_text(region)
		item_region = normalize_text(str(item.get("source_region")))
		address = normalize_text(str(item.get("address")))
		if region_text not in item_region and region_text not in address:
			return False

	if keyword:
		keyword_text = normalize_text(keyword)
		haystack = " ".join(
			[
				str(item.get("name") or ""),
				str(item.get("address") or ""),
				str(item.get("summary") or ""),
				str(item.get("description") or ""),
				" ".join(str(tag) for tag in item.get("search_tags") or []),
			]
		).lower()
		if keyword_text not in haystack:
			return False

	parsed_bbox = parse_bbox(bbox)
	if parsed_bbox is not None:
		min_lng, min_lat, max_lng, max_lat = parsed_bbox
		latitude = to_float(item.get("latitude"))
		longitude = to_float(item.get("longitude"))
		if latitude is None or longitude is None:
			return False
		if not (min_lng <= longitude <= max_lng and min_lat <= latitude <= max_lat):
			return False

	return True


def paginate(items: list[dict[str, Any]], page: int, size: int) -> tuple[list[dict[str, Any]], int, int]:
	total = len(items)
	total_pages = ceil(total / size) if total else 0
	start = (page - 1) * size
	end = start + size
	return items[start:end], total, total_pages


def list_locations(
	*,
	category: str | None = None,
	keyword: str | None = None,
	region: str | None = None,
	place_type: str | None = None,
	bbox: str | None = None,
	page: int = 1,
	size: int = 20,
) -> tuple[list[dict[str, Any]], int, int]:
	filtered = [
		build_location_payload(item)
		for item in load_locations()
		if matches_filters(
			item,
			category=category,
			keyword=keyword,
			region=region,
			place_type=place_type,
			bbox=bbox,
		)
	]
	return paginate(filtered, page, size)


def get_location(location_id: int) -> dict[str, Any] | None:
	for item in load_locations():
		source_contentid = to_int(item.get("source_contentid"))
		if source_contentid == location_id:
			return build_location_payload(item)
	return None


def get_map_filters() -> dict[str, Any]:
	regions = sorted(
		{
			str(item.get("source_region") or "").strip()
			for item in load_locations()
			if str(item.get("source_region") or "").strip()
		}
	)
	categories = [category for category in DEFAULT_CATEGORIES if category != "음식점"]
	return {
		"place_types": [
			{"value": key, "label": label}
			for key, label in MAP_PLACE_TYPE_LABELS.items()
		],
		"regions": regions,
		"categories": categories,
	}


def get_dashboard_stats() -> dict[str, Any]:
	locations = load_locations()
	category_counts: dict[str, int] = {}

	for item in locations:
		category = str(item.get("category") or "").strip()
		if not category:
			continue
		category_counts[category] = category_counts.get(category, 0) + 1

	return {
		"region": "서울",
		"total_locations": len(locations),
		"category_counts": [
			{"category": category, "count": category_counts.get(category, 0)}
			for category in DEFAULT_CATEGORIES
			if category in category_counts
		],
	}

단 하나의 테스트 게시물을 타깃으로 삼아 정확히 비교 분석할 수 있도록 로그를 대폭 업그레이드했습니다.

실제 DB에 저장된 테스트용 1번 게시물의 원본 데이터(title, category, custom_tags)와 현재 사용자의 검색 조건(keyword, category_id)을 터미널 콘솔창에 양옆으로 배치하여, 어디가 일치하고 어디가 불일치하는지 눈으로 즉시 확인할 수 있는 비교 로그를 추가했습니다.

🛠️ 데이터 비교 로그가 추가된 search_posts_from_db 전체 코드
Python
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.post import Post

def search_posts_from_db(
    db: Session, 
    *, 
    keyword: str | None = None, 
    category_id: str | None = None, 
    limit: int = 4
) -> list[Post]:
    """
    데이터베이스의 posts 테이블에서 제목, 태그를 검색하고 카테고리 필터를 적용합니다.
    실제 저장된 1번 테스트 데이터와 검색 비교 대조군을 실시간 로깅합니다.
    """
    print("\n" + "═" * 60)
    print("📥 [DB QUERY START] search_posts_from_db 분석 및 대조군 테스트")
    print("═" * 60)

    # 1. 테스트 목적을 위해 현재 DB에 존재하는 1번 게시글 원본 강제 로드 및 분석
    try:
        test_post = db.query(Post).filter(Post.id == 1).first()
        if test_post:
            print("📝 [대조군 데이터 - DB 실제 값]")
            print(f"   ├─ ID        : {test_post.id}")
            print(f"   ├─ 제목(Title): {test_post.title!r}")
            print(f"   ├─ 카테고리  : {test_post.category!r} (타입: {type(test_post.category).__name__})")
            print(f"   └─ 태그(Tags) : {test_post.custom_tags!r} (타입: {type(test_post.custom_tags).__name__})")
        else:
            print("⚠️ [대조군 데이터 Warning] DB에 ID가 1인 테스트 게시글이 존재하지 않습니다.")
    except Exception as check_err:
        print(f"❌ [대조군 로드 실패] 에러: {check_err}")

    # 2. 현재 넘어온 검색 요청 데이터 출력
    print("\n🔍 [실시간 검색 요청 값]")
    print(f"   ├─ category_id : {category_id!r} (타입: {type(category_id).__name__})")
    print(f"   └─ keyword     : {keyword!r} (타입: {type(keyword).__name__})")

    # 3. 매칭 조건 가시적 대조(Match Checking)
    if test_post:
        print("\n⚖️ [조건별 일치 여부 판독기]")
        
        # 카테고리 검증
        cat_match = (test_post.category == category_id)
        print(f"   ├─ 카테고리 일치 여부: {'✅ MATCH (일치함)' if cat_match else '❌ MISMATCH (불일치)'}")
        print(f"   │  └─ 상세비교: {test_post.category!r} == {category_id!r}")
        
        # 키워드(제목 포함) 검증
        title_match = keyword in test_post.title if keyword and test_post.title else False
        print(f"   ├─ 제목 내 키워드 포함: {'✅ MATCH (포함됨)' if title_match else '❌ MISMATCH (없음)'}")
        print(f"   │  └─ 상세비교: {keyword!r} in {test_post.title!r}")
        
        # 키워드(커스텀 태그 포함) 검증
        # custom_tags가 문자열이거나 리스트 형태일 때의 범용 검색 포함 처리
        tag_match = False
        if keyword and test_post.custom_tags:
            tag_match = keyword in str(test_post.custom_tags)
        print(f"   └─ 태그 내 키워드 포함: {'✅ MATCH (포함됨)' if tag_match else '❌ MISMATCH (없음)'}")
        print(f"      └─ 상세비교: {keyword!r} in {test_post.custom_tags!r}")

    print("─" * 60)

    # 4. 실제 DB 쿼리 조립 및 실행
    query = db.query(Post)
    
    # 카테고리 필터링
    if category_id:
        query = query.filter(Post.category == category_id)
        
    # 제목(title) 또는 태그(custom_tags)만 매칭
    if keyword:
        query = query.filter(
            or_(
                Post.title.contains(keyword),
                Post.custom_tags.contains(keyword)
            )
        )
        
    results = query.order_by(Post.created_at.desc()).limit(limit).all()

    # 5. 최종 조회 성공 여부 출력
    print(f"📤 [DB QUERY END] 쿼리 최종 반환 게시글 수 : {len(results)}개")
    if results:
        print(f"   🚀 최종 반환 리스트 ID 목록: {[p.id for p in results]}")
    print("═" * 60 + "\n")

    return results

