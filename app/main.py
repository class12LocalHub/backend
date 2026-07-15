from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine

from app.models import Location, Post
from app.routers.categories import router as categories_router
from app.routers.chat import router as chat_router
from app.routers.dashboard import router as dashboard_router
from app.routers.items import router as items_router
from app.routers.locations import router as locations_router
from app.routers.posts import router as posts_router


Base.metadata.create_all(bind=engine)
settings = get_settings()

app = FastAPI(
    title="LocalHub API",
    description="서울 공공데이터 기반 지역 정보 공유 커뮤니티 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts_router)
# 정적 경로를 동적 /api/locations/{location_id}보다 먼저 등록한다.
app.include_router(locations_router)
app.include_router(items_router)
app.include_router(dashboard_router)
app.include_router(categories_router)
app.include_router(chat_router)


@app.get(
    "/api/health",
    tags=["System"],
    summary="서버 상태 확인",
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "LocalHub API",
    }
