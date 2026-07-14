from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


router = APIRouter(prefix="/api", tags=["items"])


@router.get("/map/pois")
async def list_map_pois(
	category: str | None = None,
	keyword: str | None = None,
	region: str | None = None,
	bbox: str | None = None,
	page: int = 1,
	size: int = 20,
	db: AsyncSession = Depends(get_db),
):
	raise NotImplementedError


@router.get("/map/pois/{poi_id}")
async def get_map_poi(poi_id: int, db: AsyncSession = Depends(get_db)):
	raise NotImplementedError


@router.get("/map/filters")
async def get_map_filters(db: AsyncSession = Depends(get_db)):
	raise NotImplementedError


@router.get("/locations")
async def list_locations_api(
	category: str | None = None,
	keyword: str | None = None,
	page: int = 1,
	size: int = 20,
	db: AsyncSession = Depends(get_db),
):
	raise NotImplementedError


@router.get("/locations/{location_id}")
async def get_location_api(location_id: int, db: AsyncSession = Depends(get_db)):
	raise NotImplementedError


@router.get("/dashboard")
async def dashboard_api(db: AsyncSession = Depends(get_db)):
	raise NotImplementedError

