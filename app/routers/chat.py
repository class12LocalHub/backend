from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import generate_chat_response


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="챗봇 질문 전송",
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    try:
        answer = await generate_chat_response(
            request.messages,
            db=db,
        )

        return ChatResponse(answer=answer)

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "CHAT_RESPONSE_FAILED",
                "message": "챗봇 응답 생성 중 오류가 발생했습니다.",
            },
        ) from error