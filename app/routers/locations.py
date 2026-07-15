from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.location import Location
from app.schemas.location import LocationSuggestionResponse


router = APIRouter(
    prefix="/api/locations",
    tags=["Locations"],
)


@router.get(
    "/suggestions",
    response_model=LocationSuggestionResponse,
    summary="장소 이름 자동완성 및 초성 검색",
    description="장소명 또는 한글 초성으로 장소를 검색합니다.",
)
def suggest_locations(
    keyword: str = Query(
        min_length=1,
        description="장소명 또는 초성",
        examples=["ㄱㅂㄱ"],
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=20,
        description="최대 검색 결과 개수",
    ),
    db: Session = Depends(get_db),
) -> LocationSuggestionResponse:
    normalized_keyword = keyword.strip()

    stmt = (
        select(Location)
        .where(
            or_(
                Location.name.contains(normalized_keyword),
                Location.initial_consonants.startswith(normalized_keyword),
            )
        )
        .order_by(Location.name.asc())
        .limit(limit)
    )

    locations = db.scalars(stmt).all()

    return LocationSuggestionResponse.model_validate(
        {
            "items": [
                {
                    "id": location.id,
                    "source_id": location.source_id,
                    "name": location.name,
                    "category": location.category,
                    "address": location.address,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "image_url": location.image_url,
                    "thumbnail_url": location.thumbnail_url,
                }
                for location in locations
            ]
        }
    )
