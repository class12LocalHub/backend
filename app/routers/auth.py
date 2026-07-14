from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat_api(payload: dict, db: AsyncSession = Depends(get_db)):
	raise NotImplementedError

