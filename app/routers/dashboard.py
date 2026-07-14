from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.location import Location
from app.models.post import Post


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    summary="대시보드 통계 조회",
)
def get_dashboard(
    db: Session = Depends(get_db),
) -> dict:
    total_posts = db.scalar(
        select(func.count(Post.id))
    ) or 0

    total_locations = db.scalar(
        select(func.count(Location.id))
    ) or 0

    post_category_rows = db.execute(
        select(
            Post.category,
            func.count(Post.id),
        )
        .group_by(Post.category)
        .order_by(func.count(Post.id).desc())
    ).all()

    location_category_rows = db.execute(
        select(
            Location.category,
            func.count(Location.id),
        )
        .group_by(Location.category)
        .order_by(func.count(Location.id).desc())
    ).all()

    popular_posts = db.scalars(
        select(Post)
        .order_by(
            Post.view_count.desc(),
            Post.created_at.desc(),
        )
        .limit(5)
    ).all()

    popular_locations = db.execute(
        select(
            Location.id,
            Location.name,
            func.count(Post.id).label("post_count"),
        )
        .join(
            Post,
            Post.location_id == Location.id,
        )
        .group_by(
            Location.id,
            Location.name,
        )
        .order_by(func.count(Post.id).desc())
        .limit(5)
    ).all()

    return {
        "region": "서울",
        "summary": {
            "total_posts": total_posts,
            "total_locations": total_locations,
        },
        "post_category_counts": [
            {
                "category": category,
                "count": count,
            }
            for category, count in post_category_rows
        ],
        "location_category_counts": [
            {
                "category": category,
                "count": count,
            }
            for category, count in location_category_rows
        ],
        "popular_posts": [
            {
                "id": post.id,
                "title": post.title,
                "category": post.category,
                "view_count": post.view_count,
            }
            for post in popular_posts
        ],
        "popular_locations": [
            {
                "id": location_id,
                "name": name,
                "post_count": post_count,
            }
            for location_id, name, post_count in popular_locations
        ],
    }