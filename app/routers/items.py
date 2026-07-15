from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.crud import get_location, get_map_filters, list_locations
from app.schemas.location import LocationListResponse, MapFiltersResponse, MapPoiDetail, MapPoiListResponse


router = APIRouter(prefix="/api", tags=["items"])


@router.get("/map/pois")
def list_map_pois(
	place_type: str | None = "all",
	category: str | None = None,
	keyword: str | None = None,
	region: str | None = None,
	bbox: str | None = None,
	page: int = Query(default=1, ge=1),
	size: int = Query(default=20, ge=1, le=100),
) -> MapPoiListResponse:
	items, total, total_pages = list_locations(
		place_type=place_type,
		category=category,
		keyword=keyword,
		region=region,
		bbox=bbox,
		page=page,
		size=size,
	)
	return MapPoiListResponse(items=items, total=total, page=page, size=size, total_pages=total_pages)


@router.get("/map/pois/{poi_id}")
def get_map_poi(poi_id: int) -> MapPoiDetail:
	location = get_location(poi_id)
	if location is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail={
				"code": "LOCATION_NOT_FOUND",
				"message": "지역정보를 찾을 수 없습니다.",
			},
		)
	return MapPoiDetail.model_validate(location)


@router.get("/map/filters")
def get_map_filters_api() -> MapFiltersResponse:
	return MapFiltersResponse.model_validate(get_map_filters())


@router.get("/locations")
def list_locations_api(
	place_type: str | None = "all",
	category: str | None = None,
	keyword: str | None = None,
	page: int = Query(default=1, ge=1),
	size: int = Query(default=20, ge=1, le=100),
	region: str | None = None,
	bbox: str | None = None,
) -> LocationListResponse:
	items, total, total_pages = list_locations(
		place_type=place_type,
		category=category,
		keyword=keyword,
		region=region,
		bbox=bbox,
		page=page,
		size=size,
	)
	return LocationListResponse(items=items, total=total, page=page, size=size, total_pages=total_pages)


@router.get("/locations/{location_id}")
def get_location_api(location_id: int) -> MapPoiDetail:
	location = get_location(location_id)
	if location is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail={
				"code": "LOCATION_NOT_FOUND",
				"message": "지역정보를 찾을 수 없습니다.",
			},
		)
	return MapPoiDetail.model_validate(location)
