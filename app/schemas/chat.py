from typing import Literal

from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=20)


class ChatSource(BaseModel):
    type: Literal["location", "post"]
    id: int = Field(
        description=(
            "type=location이면 TourAPI source_contentid(Map POI id), "
            "type=post이면 SQLite posts.id입니다."
        )
    )
    name: str | None = None
    title: str | None = None
    category: str | None = None


class ChatResponse(BaseModel):
    answer: str
    query_type: str
    sources: list[ChatSource]
