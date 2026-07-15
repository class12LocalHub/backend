from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=4000)


# 기존 코드에서 사용하던 이름도 호환되도록 별칭으로 유지한다.
ChatHistoryItem = ChatMessage


class ChatRequest(BaseModel):
    # 새 chat 브랜치 요청 형식
    messages: list[ChatMessage] = Field(
        default_factory=list,
        max_length=21,
    )

    # 기존 develop 요청 형식과의 하위 호환
    message: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
    )

    @model_validator(mode="after")
    def normalize_messages(self) -> "ChatRequest":
        """
        다음 두 요청 형식을 모두 messages 배열로 정규화한다.

        1. {"messages": [...]}
        2. {"message": "...", "history": [...]}
        """

        if self.messages:
            return self

        if self.message:
            self.messages = [
                *self.history,
                ChatMessage(
                    role="user",
                    content=self.message,
                ),
            ]
            return self

        raise ValueError(
            "messages 또는 message 중 하나는 반드시 입력해야 합니다."
        )


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

    # 현재 챗봇 서비스가 answer만 반환해도 동작하도록 기본값 설정
    query_type: str = "general"
    sources: list[ChatSource] = Field(default_factory=list)