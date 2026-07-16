from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse  # 💡 StreamingResponse 임포트 추가
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest
# 💡 ChatResponse는 더 이상 사용하지 않으므로 제거하거나 주석 처리합니다.
from app.services.chat import generate_chat_response

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)

@router.post(
    "",
    # response_model=ChatResponse,  # 💡 반환값이 고정된 JSON이 아니므로 제거합니다.
    status_code=status.HTTP_200_OK,
    summary="챗봇 질문 전송 (스트리밍)",
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    try:
        # 💡 stream_generator는 응답 조각을 실시간으로 뱉어내는(yield) 제너레이터입니다.
        stream_generator = generate_chat_response(
            request.messages,
            db=db,
        )

        # 💡 StreamingResponse로 감싸서 text/event-stream 타입으로 즉시 반환합니다.
        return StreamingResponse(
            stream_generator, 
            media_type="text/event-stream"
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "CHAT_RESPONSE_FAILED",
                "message": "챗봇 응답 생성 중 오류가 발생했습니다.",
            },
        ) from error