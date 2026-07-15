from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


PlaceType = Literal["tourist", "restaurant", "all"]


class LocationBase(BaseModel):
    id: int = Field(
        description="TourAPI source_contentid. 게시글 location_id(SQLite PK)와 다른 ID입니다."
    )
    name: str
    category: str
    address: str | None = None
    summary: str | None = None
    description: str | None = None
    telephone: str | None = None
    homepage: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    region: str | None = None


class MapPoiItem(LocationBase):
    place_type: PlaceType
    firstimage2: str | None = None


class MapPoiDetail(MapPoiItem):
    source: str | None = None
    source_region: str | None = None
    source_contentid: str | None = None
    source_contenttypeid: str | None = None
    source_contenttype: str | None = None
    firstimage: str | None = None
    zipcode: str | None = None
    createdtime: str | None = None
    modifiedtime: str | None = None
    mlevel: str | None = None
    cpyrhtDivCd: str | None = None
    areacode: str | None = None
    sigungucode: str | None = None
    lDongRegnCd: str | None = None
    lDongSignguCd: str | None = None
    cat1: str | None = None
    cat2: str | None = None
    cat3: str | None = None
    lclsSystm1: str | None = None
    lclsSystm2: str | None = None
    lclsSystm3: str | None = None


class MapPoiListResponse(BaseModel):
    items: list[MapPoiItem]
    total: int
    page: int
    size: int
    total_pages: int


class MapFiltersResponse(BaseModel):
    place_types: list[dict[str, str]]
    regions: list[str]
    categories: list[str]


class LocationListResponse(BaseModel):
    items: list[LocationBase]
    total: int
    page: int
    size: int
    total_pages: int


class DashboardCategoryCount(BaseModel):
    category: str
    count: int


class DashboardResponse(BaseModel):
    region: str
    total_locations: int
    category_counts: list[DashboardCategoryCount]


class LocationSuggestionItem(BaseModel):
    id: int = Field(
        description="SQLite locations.id. 게시글 요청의 location_id에 사용합니다."
    )
    source_id: str = Field(
        description="TourAPI source_contentid. Map POI id와 같은 ID 체계입니다."
    )
    name: str
    category: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None


class LocationSuggestionResponse(BaseModel):
    items: list[LocationSuggestionItem]


class CategoryListResponse(BaseModel):
    categories: list[str]
