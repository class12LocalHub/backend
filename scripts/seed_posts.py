from datetime import datetime

from app.database import engine, Base, SessionLocal
from app.models.post import Post


SAMPLE_POSTS = [
    {
        "title": "홍대 가성비 맛집 모음",
        "content": "홍대에서 가성비 좋은 식당들을 모아봤어요. 떡볶이, 돈까스, 분식 등 다양합니다.",
        "password": "1001",
        "category": "관광지",
        "location_id": 1,
        "custom_tags": ["홍대", "맛집", "가성비"],
        "image_url": None,
    },
    {
        "title": "강남 브런치 & 카페 추천",
        "content": "강남에서 느긋하게 즐길 수 있는 브런치 카페와 분위기 좋은 장소들을 소개합니다.",
        "password": "1002",
        "category": "여행코스",
        "location_id": 2,
        "custom_tags": ["강남", "브런치", "카페"],
        "image_url": None,
    },
    {
        "title": "이태원 글로벌 맛집 투어",
        "content": "다양한 국가의 음식을 즐길 수 있는 이태원의 인기 레스토랑과 바를 정리했습니다.",
        "password": "1003",
        "category": "관광지",
        "location_id": 3,
        "custom_tags": ["이태원", "글로벌", "맛집"],
        "image_url": None,
    },
    {
        "title": "명동 쇼핑 & 길거리 음식",
        "content": "명동에서 쇼핑하고 즐길 수 있는 길거리 음식과 쇼핑 팁을 공유합니다.",
        "password": "1004",
        "category": "쇼핑",
        "location_id": 4,
        "custom_tags": ["명동", "쇼핑", "길거리음식"],
        "image_url": None,
    },
    {
        "title": "성수동 감성 카페 산책",
        "content": "성수동의 감성 카페와 공방, 사진 찍기 좋은 골목들을 추천합니다.",
        "password": "1005",
        "category": "여행코스",
        "location_id": 5,
        "custom_tags": ["성수", "카페", "감성"],
        "image_url": None,
    },
    {
        "title": "서울의 유명 관광지 추천",
        "content": "한눈에 보기 좋은 전망대부터 역사 유적까지, 서울에서 꼭 가볼 만한 관광지를 정리했어요.",
        "password": "2001",
        "category": "관광지",
        "location_id": 6,
        "custom_tags": ["관광지", "명소", "서울"],
        "image_url": None,
    },
    {
        "title": "추천 전시: 한강 아트센터 전시회 후기",
        "content": "한강 아트센터에서 열린 전시회를 다녀온 후기와 감상 포인트를 공유합니다.",
        "password": "2002",
        "category": "문화시설",
        "location_id": 7,
        "custom_tags": ["전시", "미술관", "문화"],
        "image_url": None,
    },
    {
        "title": "여름 축제 방문 후기",
        "content": "여름철에 열린 지역 축제에서 즐긴 공연과 볼거리, 팁을 정리한 후기입니다.",
        "password": "2003",
        "category": "축제공연행사",
        "location_id": 8,
        "custom_tags": ["축제", "공연", "이벤트"],
        "image_url": None,
    },
    {
        "title": "하루로 즐기는 도보 여행코스",
        "content": "도보로 편하게 돌 수 있는 하루 코스를 시간대별로 나눠서 정리했습니다.",
        "password": "2004",
        "category": "여행코스",
        "location_id": 9,
        "custom_tags": ["코스", "도보", "추천"],
        "image_url": None,
    },
    {
        "title": "주말 레포츠 즐기기",
        "content": "도심 근교에서 즐길 수 있는 레포츠 액티비티(패러글라이딩, 수상스포츠 등) 정보를 정리했습니다.",
        "password": "2005",
        "category": "레포츠",
        "location_id": 10,
        "custom_tags": ["레포츠", "액티비티", "아웃도어"],
        "image_url": None,
    },
    {
        "title": "가성비 좋은 서울 숙박 추천",
        "content": "부담 없는 가격대의 게스트하우스와 깔끔한 호스텔을 모아봤습니다.",
        "password": "2006",
        "category": "숙박",
        "location_id": 11,
        "custom_tags": ["숙박", "게스트하우스", "호텔"],
        "image_url": None,
    },
]


def main():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        existing = db.query(Post).count()
        if existing > 0:
            print(f"DB already has {existing} post(s). Seed aborted to avoid duplicates.")
            return

        for p in SAMPLE_POSTS:
            post = Post(
                title=p["title"],
                content=p["content"],
                password=p["password"],
                category=p["category"],
                location_id=p.get("location_id"),
                custom_tags=p.get("custom_tags", []),
                image_url=p.get("image_url"),
                view_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(post)

        db.commit()
        print(f"Inserted {len(SAMPLE_POSTS)} posts into the database.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
