import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.crud import list_locations
from app.models.post import Post
from app.schemas.chat import ChatMessage, ChatResponse, ChatSource


load_dotenv()


SUPPORTED_CATEGORIES = [
    "관광지",
    "문화시설",
    "축제공연행사",
    "여행코스",
    "레포츠",
    "숙박",
    "쇼핑",
]

CATEGORY_ID_TO_NAME = {
    "12": "관광지",
    "14": "문화시설",
    "15": "축제공연행사",
    "25": "여행코스",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
}

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
    "보여줘",
}

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API 키가 없어도 서버 자체는 실행될 수 있도록 한다.
openai_client = (
    AsyncOpenAI(api_key=OPENAI_API_KEY)
    if OPENAI_API_KEY
    else None
)


def _extract_keyword(message: str) -> str | None:
    normalized = message

    for mark in ("?", "!", ",", ".", "\n"):
        normalized = normalized.replace(mark, " ")

    terms = [
        term.strip()
        for term in normalized.split()
        if len(term.strip()) >= 2
        and term.strip() not in SEARCH_STOP_WORDS
        and term.strip() not in SUPPORTED_CATEGORIES
    ]

    return terms[0] if terms else None


def _fallback_analysis(message: str) -> dict:
    if any(
        word in message
        for word in (
            "게시글",
            "커뮤니티",
            "후기",
            "작성글",
            "글 찾아",
        )
    ):
        intent = "posts"
    elif any(
        word in message
        for word in (
            "장소",
            "추천",
            "관광",
            "숙박",
            "호텔",
            "쇼핑",
            "축제",
            "여행코스",
            "레포츠",
            "문화시설",
        )
    ):
        intent = "locations"
    else:
        intent = "direct"

    category = next(
        (
            category
            for category in SUPPORTED_CATEGORIES
            if category in message
        ),
        None,
    )

    return {
        "intent": intent,
        "category": category,
        "keyword": _extract_keyword(message),
    }


async def analyze_intent_with_ai(
    user_message: str,
) -> dict:
    if openai_client is None:
        return _fallback_analysis(user_message)

    system_prompt = """
너는 LocalHub 사용자의 질문을 분석하는 분류기다.

반드시 아래 JSON 형식으로만 응답한다.

{
  "intent": "posts | locations | direct",
  "category": "관광지 | 문화시설 | 축제공연행사 | 여행코스 | 레포츠 | 숙박 | 쇼핑 | null",
  "keyword": "검색할 핵심 단어 또는 null"
}

분류 규칙:
- posts: 게시글, 후기, 커뮤니티 글을 찾는 질문
- locations: LocalHub가 보유한 서울 장소를 찾거나 추천받는 질문
- direct: 날씨, 교통 등 현재 LocalHub 데이터 검색과 직접 관련 없는 질문

음식점 데이터는 지원하지 않으므로 음식점 질문은 direct로 분류한다.
""".strip()

    try:
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            response_format={
                "type": "json_object",
            },
        )
        raw_content = response.choices[0].message.content if response.choices else None
        return json.loads(raw_content)
    except Exception as e:
        print(f"[의도 분석 실패]: {e}")
        return {"intent": "direct", "category_id": None, "keyword": None}


def _search_posts(
    db: Session,
    *,
    keyword: str | None,
    category: str | None,
    limit: int = 4,
) -> list[Post]:
    stmt = select(Post)

    if category:
        stmt = stmt.where(
            Post.category == category
        )

    if keyword:
        # 사용자가 직접 입력한 custom_tags는 검색에 포함하지 않는다.
        stmt = stmt.where(
            or_(
                Post.title.contains(keyword),
                Post.content.contains(keyword),
            )
        )

    stmt = (
        stmt.order_by(Post.created_at.desc())
        .limit(limit)
    )

    return list(db.scalars(stmt).all())


def _search_locations(
    *,
    keyword: str | None,
    category: str | None,
    limit: int = 4,
) -> list[dict]:
    locations, _, _ = list_locations(
        category=category,
        keyword=keyword,
        page=1,
        size=limit,
    )

    return locations


def _to_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _post_sources(
    posts: list[Post],
) -> list[ChatSource]:
    return [
        ChatSource(
            type="post",
            id=post.id,
            title=post.title,
            category=post.category,
        )
        for post in posts
    ]


def _location_sources(
    locations: list[dict],
) -> list[ChatSource]:
    sources: list[ChatSource] = []

    for location in locations:
        location_id = _to_int(
            location.get("id")
        )

        if location_id is None:
            continue

        sources.append(
            ChatSource(
                type="location",
                id=location_id,
                name=location.get("name"),
                category=location.get(
                    "category"
                ),
            )
        )

    return sources


def _fallback_response(
    *,
    user_message: str,
    intent: str,
    data: list,
    query_type: str,
    sources: list[ChatSource],
) -> ChatResponse:
    if intent == "posts":
        if not data:
            answer = (
                "관련 게시글을 찾지 못했습니다."
            )
        else:
            lines = [
                "관련 커뮤니티 게시글을 찾았습니다."
            ]

            for index, post in enumerate(
                data,
                start=1,
            ):
                lines.append(
                    (
                        f"{index}. {post.title} "
                        f"({post.category})"
                    )
                )

            answer = "\n".join(lines)

    elif intent == "locations":
        if not data:
            answer = (
                "제공된 서울 지역정보에서 "
                "관련 장소를 찾지 못했습니다."
            )
        else:
            lines = [
                "추천 장소를 찾았습니다."
            ]

            for index, location in enumerate(
                data,
                start=1,
            ):
                lines.append(
                    (
                        f"{index}. "
                        f"{location.get('name')} - "
                        f"{location.get('address') or '주소 정보 없음'}"
                    )
                )

            answer = "\n".join(lines)

    else:
        answer = (
            "현재 AI 응답 기능을 사용할 수 없습니다. "
            "서울 장소나 게시글 검색으로 질문해 주세요."
        )

    return ChatResponse(
        answer=answer,
        query_type=query_type,
        sources=sources,
    )


async def generate_chat_response(
    messages: list[ChatMessage],
    db: Session,
) -> ChatResponse:
    if not messages:
        return ChatResponse(
            answer="질문을 입력해 주세요.",
            query_type="unknown",
            sources=[],
        )

    user_last_message = next(
        (
            message.content
            for message in reversed(messages)
            if message.role == "user"
        ),
        messages[-1].content,
    )

    analysis = await analyze_intent_with_ai(
        user_last_message
    )

    intent = analysis.get(
        "intent",
        "direct",
    )
    category = analysis.get("category")
    keyword = (
        analysis.get("keyword")
        or _extract_keyword(user_last_message)
    )

    print(f"[CHAT] intent={intent}, category_id={category_id!r}, keyword={keyword!r}")

    local_context = ""
    data: list = []
    sources: list[ChatSource] = []

    if intent == "posts":
        data = _search_posts(
            db,
            keyword=keyword,
            category=category,
        )
        sources = _post_sources(data)
        query_type = "게시글검색"

        if data:
            context_lines = [
                "[연관 커뮤니티 게시글]"
            ]

            for index, post in enumerate(
                data,
                start=1,
            ):
                context_lines.append(
                    (
                        f"{index}. 제목: {post.title}\n"
                        f"카테고리: {post.category}\n"
                        f"내용: {post.content[:200]}"
                    )
                )

            local_context = "\n".join(
                context_lines
            )

    elif intent == "locations":
        data = _search_locations(
            keyword=keyword,
            category=category,
        )
        sources = _location_sources(data)

        query_type = (
            f"{category}추천"
            if category
            else "장소검색"
        )

        if data:
            context_lines = [
                "[LocalHub 서울 장소 데이터]"
            ]

            for index, location in enumerate(
                data,
                start=1,
            ):
                context_lines.append(
                    (
                        f"{index}. 이름: "
                        f"{location.get('name')}\n"
                        f"카테고리: "
                        f"{location.get('category')}\n"
                        f"주소: "
                        f"{location.get('address')}\n"
                        f"설명: "
                        f"{location.get('summary') or location.get('description') or '정보 없음'}"
                    )
                )

            local_context = "\n".join(
                context_lines
            )

    else:
        query_type = "general"

    if openai_client is None:
        return _fallback_response(
            user_message=user_last_message,
            intent=intent,
            data=data,
            query_type=query_type,
            sources=sources,
        )

    system_instruction = """
너는 서울 지역정보 커뮤니티 LocalHub의 AI 가이드다.

규칙:
1. 답변은 핵심만 간결하게 작성한다.
2. 최대 4개까지만 추천한다.
3. 제공된 지역정보와 게시글 내용을 우선 사용한다.
4. 제공되지 않은 장소의 주소나 운영시간을 지어내지 않는다.
5. 커뮤니티 게시글은 사용자가 작성한 후기라는 점을 명확히 한다.
""".strip()

    api_messages = [
        {
            "role": "system",
            "content": system_instruction,
        }
    ]

    if local_context:
        api_messages.append(
            {
                "role": "system",
                "content": local_context,
            }
        )

    for message in messages[-20:]:
        api_messages.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    try:
        # 2-1. 의도 1: 게시글 검색 (posts)
        if intent == "posts":
            posts = search_posts_from_db(db, keyword=keyword, category_id=category_id)
            fallback_data = posts # fallback 대비용 데이터 저장
            print(f"[CHAT] posts_found={len(posts)}, keyword={keyword!r}, category_id={category_id!r}")
            if posts:
                print("[CHAT] posts_result=" + ", ".join(f"{post.id}:{post.title}" for post in posts))
                context_lines = ["[연관 커뮤니티 게시글 검색 결과]"]
                for idx, post in enumerate(posts, 1):
                    # 카테고리 ID 역매핑하여 이름 획득
                    cat_name = next((k for k, v in CATEGORY_CODES.items() if v == post.category), "일반")
                    context_lines.append(
                        f"게시글 {idx}. 제목: {post.title} | 게시판: {cat_name}\n"
                        f"   - 본문 요약: {post.content[:150]}..."
                    )
                local_context = "\n".join(context_lines)

        # 2-2. 의도 2: 장소 추천 (locations)
        elif intent == "locations":
            # TourAPI JSON 데이터 카테고리 매핑용 역변환
            cat_name = next((k for k, v in CATEGORY_CODES.items() if v == category_id), None)
            locations, _, _ = list_locations(category=cat_name, keyword=keyword, size=4)
            fallback_data = locations
            print(
                f"[CHAT] locations_found={len(locations)}, keyword={keyword!r}, category_id={category_id!r}, mapped_category={cat_name!r}"
            )
            if locations:
                print("[CHAT] locations_result=" + ", ".join(f"{loc.get('id')}:{loc.get('name')}" for loc in locations))
                context_lines = ["[추천 장소 정보 데이터]"]
                for idx, loc in enumerate(locations, 1):
                    context_lines.append(
                        f"장소 {idx}. 명칭: {loc.get('name')} | 분류: {loc.get('category')} | 주소: {loc.get('address')}\n"
                        f"   - 설명: {loc.get('summary') or loc.get('description') or '정보 없음'}"
                    )
                local_context = "\n".join(context_lines)

        # 2-3. 의도 3: 기타 (direct)
        # 별도 DB 조회를 거치지 않고 prompt에 빈 값을 주어 GPT가 다이렉트로 답변하게 유도합니다.
        else:
            local_context = ""

        # 3. GPT-4o-mini 호출
        system_instruction = (
            "너는 서울 및 지역 관광 커뮤니티인 'LocalHub'의 AI 가이드야.\n"
            "답변 규칙:\n"
            "1. 답변은 최대 5줄, 불필요한 장문 설명은 하지 마.\n"
            "2. 추천은 핵심만 간단히 정리하고, 각 항목은 1~2줄로 써.\n"
            "3. 리스트는 최대 4개까지만 보여줘.\n"
            "[연관 커뮤니티 게시글 검색 결과]가 있으면 관련 글을 짧게 요약해줘.\n"
            "게시글 데이터가 없다면 그냥 현재 게시판에 관련 게시글이 없다고 말해줘.\n"
            "[추천 장소 정보 데이터]가 있으면 이름, 주소, 한줄 소개만 간단히 보여줘.\n"
            "장소 데이터가 없다변 해당 지역/주제에 대해 네가 아는 범위에서 짧고 자연스럽게 안내해줘.\n"
        )

        if not response.choices:
            raise ValueError(
                "OpenAI 응답 choice가 없습니다."
            )

        answer = (
            response.choices[0]
            .message.content
            or ""
        ).strip()

        response = await openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=api_messages,
            response_format={"type": "text"},
            max_completion_tokens=2500
        )
        first_choice = response.choices[0] if response.choices else None
        raw_message = first_choice.message if first_choice else None
        answer = (response.choices[0].message.content or "").strip()
        if not answer:
            print("[OpenAI API 경고] 빈 응답이 반환되어 fallback으로 전환합니다.")
            return generate_fallback_response(user_last_message, intent, fallback_data)
        return answer

    except Exception as openai_error:
        # 4. Fallback 작동: API 문제 발생 시 자체 조합 텍스트 제공
        print(f"[OpenAI API 에러 - Fallback 실행]: {openai_error}")
        return generate_fallback_response(user_last_message, intent, fallback_data)


def generate_fallback_response(user_message: str, intent: str, data: list) -> str:
    """
    OpenAI API 실패 시 데이터를 직접 조합하여 마크다운 형태로 답변을 빌드합니다.
    """
    intro = "시스템 점검 중이어서 DB 기준으로 간단히 안내드릴게요.\n\n"
    
    if not data:
        return intro + f"'{user_message}'와(과) 관련된 정보를 매칭해 보았지만, 적절한 데이터가 검색되지 않았습니다. 😢"

    results = []
    
    # 게시글 Fallback 포맷팅
    if intent == "posts":
        results.append("🔍 **연관된 인기 커뮤니티 게시글들을 찾았습니다:**\n")
        for idx, post in enumerate(data, 1):
            results.append(
                f"### {idx}. {post.title}\n"
                f"- 📝 내용: {post.content[:150]}...\n"
                f"- 🕒 등록일: {post.created_at.strftime('%Y-%m-%d')}\n"
            )
            
    # 장소 Fallback 포맷팅
    else:
        results.append("📍 **추천드릴 만한 가볼 만한 곳 리스트입니다:**\n")
        for idx, loc in enumerate(data, 1):
            results.append(
                f"### {idx}. {loc.get('name')} ({loc.get('category', '관광지')})\n"
                f"- 📍 주소: {loc.get('address', '주소 미제공')}\n"
                f"- ✍️ 소개: {loc.get('summary') or loc.get('description') or '상세 설명 정보가 부족합니다.'}\n"
            )

        return ChatResponse(
            answer=answer,
            query_type=query_type,
            sources=sources,
        )

    except Exception as error:
        print(
            f"[OpenAI 응답 실패 - fallback]: {error}"
        )

        return _fallback_response(
            user_message=user_last_message,
            intent=intent,
            data=data,
            query_type=query_type,
            sources=sources,
        )