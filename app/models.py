from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Location(Base):
	__tablename__ = "locations"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	source_contentid: Mapped[str | None] = mapped_column(String(50), unique=True, index=True, nullable=True)
	source_contenttypeid: Mapped[str | None] = mapped_column(String(10), nullable=True)
	source_contenttype: Mapped[str | None] = mapped_column(String(50), nullable=True)
	name: Mapped[str] = mapped_column(String(200), index=True)
	category: Mapped[str] = mapped_column(String(50), index=True)
	address: Mapped[str | None] = mapped_column(String(300), nullable=True)
	summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
	description: Mapped[str | None] = mapped_column(Text, nullable=True)
	telephone: Mapped[str | None] = mapped_column(String(50), nullable=True)
	homepage: Mapped[str | None] = mapped_column(String(300), nullable=True)
	latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
	longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
	region: Mapped[str | None] = mapped_column(String(50), nullable=True)
	source: Mapped[str | None] = mapped_column(String(100), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Post(Base):
	__tablename__ = "posts"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	title: Mapped[str] = mapped_column(String(100), index=True)
	content: Mapped[str] = mapped_column(Text)
	category: Mapped[str] = mapped_column(String(50), index=True)
	password_hash: Mapped[str] = mapped_column(String(255))
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

