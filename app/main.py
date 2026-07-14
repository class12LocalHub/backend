from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, items


app = FastAPI(title="LocalHub API")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(items.router)
app.include_router(auth.router)


@app.on_event("startup")
async def startup() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
	# TODO: load seed_locations.json and seed_posts.json here.


@app.get("/api/health")
async def health() -> dict[str, str]:
	return {"status": "ok", "service": "LocalHub API"}

