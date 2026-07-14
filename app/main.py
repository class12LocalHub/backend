from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

from app.routers.items import router as items_router
from app.models import Location, Post
from app.routers.dashboard import router as dashboard_router
from app.routers.locations import router as locations_router
from app.routers.posts import router as posts_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LocalHub API",
    description="서울 공공데이터 기반 지역 정보 공유 커뮤니티 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts_router)
app.include_router(items_router)
app.include_router(locations_router)
app.include_router(dashboard_router)


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
