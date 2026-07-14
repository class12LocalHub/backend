from math import ceil

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.post import Post
from app.schemas.post import (
    PostCreateRequest,
    PostDeleteResponse,
    PostListResponse,
    PostMessageResponse,
    PostPasswordRequest,
    PostResponse,
    PostUpdateRequest,
)


router = APIRouter(
    prefix="/api/posts",
    tags=["Posts"],
)


@router.post(
    "",
    response_model=PostMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="게시글 작성",
)
def create_post(
    request: PostCreateRequest,
    db: Session = Depends(get_db),
) -> PostMessageResponse:
    post = Post(
        title=request.title,
        content=request.content,
        password=request.password,
        category=request.category,
        location_id=request.location_id,
        custom_tags=request.custom_tags,
        image_url=str(request.image_url) if request.image_url else None,
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return PostMessageResponse(
        message="게시글이 등록되었습니다.",
        post=PostResponse.model_validate(post),
    )


@router.get(
    "",
    response_model=PostListResponse,
    summary="게시글 목록 조회",
)
def get_posts(
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    location_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PostListResponse:
    conditions = []

    if category:
        conditions.append(Post.category == category)

    if keyword:
        conditions.append(
            or_(
                Post.title.contains(keyword),
                Post.content.contains(keyword),
            )
        )

    if location_id is not None:
        conditions.append(Post.location_id == location_id)

    count_stmt = select(func.count(Post.id))

    if conditions:
        count_stmt = count_stmt.where(*conditions)

    total = db.scalar(count_stmt) or 0

    stmt = select(Post)

    if conditions:
        stmt = stmt.where(*conditions)

    stmt = (
        stmt.order_by(Post.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    posts = db.scalars(stmt).all()

    return PostListResponse(
        items=list(posts),
        total=total,
        page=page,
        size=size,
        total_pages=ceil(total / size) if total else 0,
    )


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    summary="게시글 상세 조회",
)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
) -> Post:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "POST_NOT_FOUND",
                "message": "게시글을 찾을 수 없습니다.",
            },
        )

    post.view_count += 1
    db.commit()
    db.refresh(post)

    return post


@router.put(
    "/{post_id}",
    response_model=PostMessageResponse,
    summary="게시글 수정",
)
def update_post(
    post_id: int,
    request: PostUpdateRequest,
    db: Session = Depends(get_db),
) -> PostMessageResponse:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "POST_NOT_FOUND",
                "message": "게시글을 찾을 수 없습니다.",
            },
        )

    if post.password != request.password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INVALID_PASSWORD",
                "message": "비밀번호가 일치하지 않습니다.",
            },
        )

    post.title = request.title
    post.content = request.content
    post.category = request.category
    post.location_id = request.location_id
    post.custom_tags = request.custom_tags
    post.image_url = str(request.image_url) if request.image_url else None

    db.commit()
    db.refresh(post)

    return PostMessageResponse(
        message="게시글이 수정되었습니다.",
        post=PostResponse.model_validate(post),
    )


@router.delete(
    "/{post_id}",
    response_model=PostDeleteResponse,
    summary="게시글 삭제",
)
def delete_post(
    post_id: int,
    request: PostPasswordRequest = Body(...),
    db: Session = Depends(get_db),
) -> PostDeleteResponse:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "POST_NOT_FOUND",
                "message": "게시글을 찾을 수 없습니다.",
            },
        )

    if post.password != request.password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INVALID_PASSWORD",
                "message": "비밀번호가 일치하지 않습니다.",
            },
        )

    deleted_id = post.id

    db.delete(post)
    db.commit()

    return PostDeleteResponse(
        message="게시글이 삭제되었습니다.",
        deleted_id=deleted_id,
    )