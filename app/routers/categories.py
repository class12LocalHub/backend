from fastapi import APIRouter

from app.crud import DEFAULT_CATEGORIES
from app.schemas.location import CategoryListResponse


router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get(
    "",
    response_model=CategoryListResponse,
    summary="카테고리 목록 조회",
)
def get_categories() -> CategoryListResponse:
    return CategoryListResponse(
        categories=[
            category
            for category in DEFAULT_CATEGORIES
            if category != "음식점"
        ]
    )
