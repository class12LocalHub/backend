# app/services/chat.py
import os
import json
import random
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from app.models.post import Post
from app.schemas.chat import ChatMessage
from app.crud import list_locations, search_posts_from_db
from typing import List
from dotenv import load_dotenv

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 게시판 카테고리 코드 매핑 사전
CATEGORY_CODES = {
    "관광지": "12",
    "문화시설": "14",
    "축제공연행사": "15",
    "여행코스": "25",
    "레포츠": "28",
    "숙박": "32",
    "쇼핑": "38"
}

async def analyze_intent_with_ai(user_message: str) -> dict:
    """
    1단계: 사용자의 질문 의도를 3가지(posts, locations, direct)로 분류하고 필요한 검색 파라미터를 추출합니다.
    """
    system_prompt = (
        "너는 사용자의 질문 의도를 분류하고 적절한 검색 조건을 추출하는 라우터 엔진이야.\n"
        "사용자의 질문을 분석하여 반드시 아래 JSON 형식으로만 응답해야 해. 다른 말은 덧붙이지 마.\n\n"
        "{\n"
        "  \"intent\": \"posts | locations | direct\",\n"
        "  \"category_id\": \"12 | 14 | 15 | 25 | 28 | 32 | 38 | null\",  // 관련된 게시판 카테고리가 연상되는 경우에만 코드를 선택해줘.\n"
        "  \"keyword\": \"검색을 위한 핵심 키워드(지역명이나 핵심 단어) 또는 null\"\n"
        "}\n\n"
        "■ 의도 분류 규칙(intent):\n"
        "1. posts (관련 게시글 검색): 사용자가 '게시글', '자유게시판', '후기', '커뮤니티 글', '글 추천' 등 다른 유저들이 작성한 글을 찾을 때\n"
        "2. locations (장소 추천): 서울의 권역별/행정구역별 관광지 추천, 축제 정보 등 우리 시스템이 보유한 실제 공공 장소 데이터를 바탕으로 응답할 수 있는 질문일 때\n"
        "3. direct (기타): 모범 음식점 위치, 축제 일정표(현재의 리스트 데이터에 없는 스케줄), 날씨, 교통 정보 등 외부 실시간 정보가 필요하거나 기타 일반 대화일 때\n\n"
        "■ category_id 매핑 가이드:\n"
        "- 관광지 관련 질문: \"12\"\n"
        "- 미술관, 전시관 등 문화시설 관련 질문: \"14\"\n"
        "- 축제, 이벤트, 행사 관련 질문: \"15\"\n"
        "- 여행코스 추천 관련 질문: \"25\"\n"
        "- 레포츠, 액티비티 관련 질문: \"28\"\n"
        "- 숙박, 호텔, 게스트하우스 관련 질문: \"32\"\n"
        "- 쇼핑, 시장, 백화점 관련 질문: \"38\"\n"
        "- 음식점, 맛집 관련 질문은 지원하지 않으므로 무조건 null 처리하고 direct 의도로 분류해줘.\n"
    )

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"사용자 질문: \"{user_message}\""}
            ],
            response_format={"type": "json_object"}
        )
        raw_content = response.choices[0].message.content if response.choices else None
        return json.loads(raw_content)
    except Exception as e:
        print(f"[의도 분석 실패]: {e}")
        return {"intent": "direct", "category_id": None, "keyword": None}


async def generate_chat_response(messages: List[ChatMessage], db: Session) -> str:
    user_last_message = messages[-1].content
    
    print("\n" + "=" * 60)
    try:
        # 1. SQLAlchemy가 현재 바라보고 있는 DB 실제 물리 경로/접속 주소 출력
        db_url = db.bind.url if db.bind else "알 수 없음 (바인딩되지 않음)"
        print(f"📡 [DB 경로 확인] ➔ {db_url}")
        
        # 2. posts 테이블의 실제 데이터 총 개수 출력
        posts_count = db.query(Post).count()
        print(f"📊 [데이터 개수] ➔ 현재 posts 테이블 내 총 게시글 수: {posts_count}개")
        
        if posts_count > 0:
            # 존재한다면 가장 최근에 등록된 글 제목 하나를 샘플로 출력하여 검증
            latest_post = db.query(Post).order_by(Post.created_at.desc()).first()
            print(f"📝 [최신 데이터 샘플] ➔ ID: {latest_post.id} | 제목: '{latest_post.title}'")
            
    except Exception as db_diagnostic_error:
        print(f"❌ [DB 진단 실패] DB 연결 상태 또는 posts 테이블을 찾을 수 없습니다.\n오류 내용: {db_diagnostic_error}")
    print("=" * 60 + "\n")
    
    # 1. AI 의도 분석 호출
    analysis = await analyze_intent_with_ai(user_last_message)
    intent = analysis.get("intent", "direct")
    category_id = analysis.get("category_id")
    keyword = analysis.get("keyword") or user_last_message

    print(f"[CHAT] intent={intent}, category_id={category_id!r}, keyword={keyword!r}")

    local_context = ""
    fallback_data = []

    try:
        # 2-1. 의도 1: 게시글 검색 (posts)
        if intent == "posts":
            # 💡 [수정] AI가 뽑아준 카테고리 코드("12")를 DB에 저장된 한글 카테고리명("관광지")으로 변환합니다.
            db_category_name = None
            if category_id:
                # CATEGORY_CODES를 역으로 추적하여 한글 키값을 찾습니다.
                db_category_name = next((k for k, v in CATEGORY_CODES.items() if v == category_id), None)
            
            # DB 조회 시 category_id 파라미터에 한글 카테고리명(db_category_name)을 전달합니다.
            posts = search_posts_from_db(db, keyword=keyword, category_id=db_category_name)
            
            fallback_data = posts # fallback 대비용 데이터 저장
            print(f"[CHAT] posts_found={len(posts)}, keyword={keyword!r}, category_id(코드)={category_id!r}, db_category_name(한글)={db_category_name!r}")
            if posts:
                print("[CHAT] posts_result=" + ", ".join(f"{post.id}:{post.title}" for post in posts))
                context_lines = ["[연관 커뮤니티 게시글 검색 결과]"]
                for idx, post in enumerate(posts, 1):
                    # 카테고리 ID 역매핑하여 이름 획득 (DB에 이미 한글명이 들어있으므로 post.category를 그대로 씁니다)
                    cat_name = post.category or "일반"
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

        api_messages = [{"role": "system", "content": system_instruction}]
        if local_context:
            api_messages.append({"role": "system", "content": local_context})
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

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

    return intro + "\n".join(results)