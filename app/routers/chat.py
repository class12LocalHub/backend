from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db  # get_db 의존성 임포트
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import generate_chat_response
from app.crud import load_locations, Post
from sqlalchemy.sql import text

router = APIRouter(
    prefix="/api/chat",
    tags=["Chatbot"]
)

@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_bot(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 서비스 호출 시 db 세션 객체를 함께 전달합니다.
        answer = await generate_chat_response(payload.messages, db=db)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"챗봇 응답 생성 중 오류가 발생했습니다: {str(e)}"
        )
    
    from app.crud import load_locations, Post
from sqlalchemy.sql import text
