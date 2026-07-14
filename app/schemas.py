from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LocationBase(BaseModel):
	name: str
	category: str
	address: str | None = None
	summary: str | None = None
	description: str | None = None
	telephone: str | None = None
	homepage: str | None = None
	latitude: float | None = None
	longitude: float | None = None
	region: str | None = None


class LocationListItem(LocationBase):
	id: int


class LocationDetailItem(LocationListItem):
	source: str | None = None
	source_contentid: str | None = None
	source_contenttypeid: str | None = None
	source_contenttype: str | None = None


class LocationListResponse(BaseModel):
	items: list[LocationListItem]
	total: int
	page: int
	size: int
	total_pages: int


class PostBase(BaseModel):
	title: str = Field(min_length=1, max_length=100)
	content: str = Field(min_length=1)
	category: str


class PostCreate(PostBase):
	password: str = Field(min_length=4)


class PostUpdate(PostCreate):
	pass


class PostItem(PostBase):
	id: int
	created_at: datetime
	updated_at: datetime


class PostListResponse(BaseModel):
	items: list[PostItem]
	total: int
	page: int
	size: int
	total_pages: int


class DashboardCategoryCount(BaseModel):
	category: str
	count: int


class DashboardResponse(BaseModel):
	region: str
	total_locations: int
	category_counts: list[DashboardCategoryCount]


class ChatMessage(BaseModel):
	role: str
	content: str


class ChatRequest(BaseModel):
	message: str = Field(min_length=1)
	history: list[ChatMessage] = []


class ChatSource(BaseModel):
	type: str
	id: int
	name: str | None = None
	title: str | None = None
	category: str | None = None


class ChatResponse(BaseModel):
	answer: str
	query_type: str
	sources: list[ChatSource]

