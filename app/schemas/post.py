from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


PostCategory = Literal[
    "관광지",
    "레포츠",
    "문화시설",
    "쇼핑",
    "숙박",
    "여행코스",
    "축제공연행사",
]


class PostCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    password: str = Field(min_length=4, max_length=20)
    category: PostCategory
    location_id: int | None = Field(
        default=None,
        description=(
            "SQLite locations.id. /api/locations/suggestions 응답의 id를 사용합니다. "
            "Map POI id(TourAPI source_contentid)를 사용하지 않습니다."
        ),
    )
    custom_tags: list[str] = Field(default_factory=list, max_length=5)
    image_url: HttpUrl | None = None

    @field_validator("custom_tags")
    @classmethod
    def validate_custom_tags(cls, tags: list[str]) -> list[str]:
        normalized: list[str] = []

        for tag in tags:
            cleaned = tag.strip().lstrip("#")

            if not cleaned:
                continue

            if len(cleaned) > 20:
                raise ValueError("태그는 20자 이하여야 합니다.")

            if cleaned not in normalized:
                normalized.append(cleaned)

        return normalized


class PostUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    password: str = Field(min_length=4, max_length=20)
    category: PostCategory
    location_id: int | None = Field(
        default=None,
        description=(
            "SQLite locations.id. /api/locations/suggestions 응답의 id를 사용합니다. "
            "Map POI id(TourAPI source_contentid)를 사용하지 않습니다."
        ),
    )
    custom_tags: list[str] = Field(default_factory=list, max_length=5)
    image_url: HttpUrl | None = None

    @field_validator("custom_tags")
    @classmethod
    def validate_custom_tags(cls, tags: list[str]) -> list[str]:
        normalized: list[str] = []

        for tag in tags:
            cleaned = tag.strip().lstrip("#")

            if not cleaned:
                continue

            if len(cleaned) > 20:
                raise ValueError("태그는 20자 이하여야 합니다.")

            if cleaned not in normalized:
                normalized.append(cleaned)

        return normalized


class PostPasswordRequest(BaseModel):
    password: str = Field(min_length=4, max_length=20)


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    location_id: int | None = Field(
        description="SQLite locations.id. Map POI id와 다른 ID입니다."
    )
    custom_tags: list[str]
    image_url: str | None
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostListItemResponse(BaseModel):
    id: int
    title: str
    category: str
    location_id: int | None = Field(
        description="SQLite locations.id. Map POI id와 다른 ID입니다."
    )
    custom_tags: list[str]
    image_url: str | None
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    items: list[PostListItemResponse]
    total: int
    page: int
    size: int
    total_pages: int


class PostMessageResponse(BaseModel):
    message: str
    post: PostResponse


class PostDeleteResponse(BaseModel):
    message: str
    deleted_id: int


class PostLocationResponse(BaseModel):
    id: int = Field(description="SQLite locations.id")
    source_id: str = Field(
        description="TourAPI source_contentid. Map POI id와 같은 ID입니다."
    )
    name: str
    category: str
    address: str | None
    latitude: float | None
    longitude: float | None
    thumbnail_url: str | None


class PostDetailResponse(PostResponse):
    location: PostLocationResponse | None
