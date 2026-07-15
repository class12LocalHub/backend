from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.crud import DEFAULT_CATEGORIES, list_locations
from app.models.post import Post
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource


SEARCH_STOP_WORDS = {
    "서울",
    "관련",
    "장소",
    "관광지",
    "추천",
    "추천해줘",
    "알려줘",
    "어디야",
    "주소",
    "게시글",
    "찾아줘",
}


def _search_terms(message: str) -> list[str]:
    normalized = (
        message.replace("?", " ")
        .replace("!", " ")
        .replace(",", " ")
        .replace(".", " ")
    )
    return [
        term
        for term in normalized.split()
        if len(term) >= 2 and term not in SEARCH_STOP_WORDS
    ]


def _search_posts(message: str, db: Session) -> ChatResponse:
    terms = _search_terms(message)
    stmt = select(Post)

    if terms:
        stmt = stmt.where(
            or_(
                *[
                    condition
                    for term in terms
                    for condition in (
                        Post.title.contains(term),
                        Post.content.contains(term),
                    )
                ]
            )
        )

    posts = db.scalars(
        stmt.order_by(Post.created_at.desc()).limit(3)
    ).all()
    sources = [
        ChatSource(
            type="post",
            id=post.id,
            title=post.title,
            category=post.category,
        )
        for post in posts
    ]

    if not sources:
        return ChatResponse(
            answer="관련 게시글을 찾지 못했습니다.",
            query_type="게시글검색",
            sources=[],
        )

    return ChatResponse(
        answer=f"관련 게시글 {len(sources)}개를 찾았습니다.",
        query_type="게시글검색",
        sources=sources,
    )


def _search_locations(message: str) -> ChatResponse:
    category = next(
        (
            candidate
            for candidate in DEFAULT_CATEGORIES
            if candidate != "음식점" and candidate in message
        ),
        None,
    )
    terms = _search_terms(message)
    keyword = terms[0] if terms and category is None else None
    items, _, _ = list_locations(
        category=category,
        keyword=keyword,
        page=1,
        size=3,
    )
    sources = [
        ChatSource(
            type="location",
            id=item["id"],
            name=item["name"],
            category=item["category"],
        )
        for item in items
    ]

    if not sources:
        return ChatResponse(
            answer="제공된 서울 지역정보에서 해당 내용을 찾지 못했습니다.",
            query_type="unknown",
            sources=[],
        )

    query_type = f"{category}추천" if category else "장소검색"
    names = ", ".join(source.name or "" for source in sources)
    return ChatResponse(
        answer=f"서울 지역정보에서 {names}을(를) 찾았습니다.",
        query_type=query_type,
        sources=sources,
    )


def build_chat_response(
    request: ChatRequest,
    db: Session,
) -> ChatResponse:
    message = request.message.strip()

    if "게시글" in message:
        return _search_posts(message, db)

    return _search_locations(message)
