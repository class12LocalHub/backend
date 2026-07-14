from fastapi import FastAPI

app = FastAPI(
    title="LocalHub API",
    description="서울 공공데이터 기반 지역 정보 공유 커뮤니티 API",
    version="0.1.0",
)


@app.get(
    "/api/health",
    tags=["System"],
    summary="서버 상태 확인",
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}