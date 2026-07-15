from fastapi import APIRouter

from app.crud import get_dashboard_stats
from app.schemas.location import DashboardResponse


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    summary="대시보드 통계 조회",
)
def get_dashboard() -> DashboardResponse:
    return DashboardResponse.model_validate(get_dashboard_stats())
