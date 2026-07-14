from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = os.getenv(
	"DATABASE_URL",
	"sqlite+aiosqlite:///./sql_app.db",
)


class Base(DeclarativeBase):
	pass


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
	async with AsyncSessionLocal() as session:
		yield session

