from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    role: str  # "user" 또는 "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    answer: str