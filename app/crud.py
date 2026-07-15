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

def search_posts_from_db(
    db: Session, 
    *, 
    keyword: str | None = None, 
    category_id: str | None = None, 
    limit: int = 4
) -> list[Post]:
    query = db.query(Post)
    
    # 1. 카테고리 필터링
    if category_id:
        query = query.filter(Post.category == category_id)
        
    # 2. 제목(title) 또는 태그(custom_tags)만 매칭 (본문은 과감히 제외!)
    if keyword:
        query = query.filter(
            or_(
                Post.title.contains(keyword),
                Post.custom_tags.contains(keyword)  # JSON 타입 검색 지원
            )
        )
        
    return query.order_by(Post.created_at.desc()).limit(limit).all()

