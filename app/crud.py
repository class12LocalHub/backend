from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Location, Post


async def create_tables_and_seed(session: AsyncSession) -> None:
	"""Create tables and load seed data. Fill in later."""
	raise NotImplementedError


async def list_locations(session: AsyncSession, *, category: str | None = None, keyword: str | None = None, page: int = 1, size: int = 20) -> tuple[list[Location], int]:
	raise NotImplementedError


async def get_location(session: AsyncSession, location_id: int) -> Location | None:
	raise NotImplementedError


async def get_dashboard(session: AsyncSession) -> dict:
	raise NotImplementedError


async def list_posts(session: AsyncSession, *, category: str | None = None, keyword: str | None = None, page: int = 1, size: int = 10) -> tuple[list[Post], int]:
	raise NotImplementedError


async def get_post(session: AsyncSession, post_id: int) -> Post | None:
	raise NotImplementedError


async def create_post(session: AsyncSession, payload) -> Post:
	raise NotImplementedError


async def update_post(session: AsyncSession, post_id: int, payload) -> Post:
	raise NotImplementedError


async def delete_post(session: AsyncSession, post_id: int) -> None:
	raise NotImplementedError

