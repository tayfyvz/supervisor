import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks
from sqlalchemy.orm import Session

from backend.db.database import get_db, SessionLocal
from backend.models.post import Post, PostNode
from backend.models.job import PostJob
from backend.schemas.post import (CompletePostResponse, CompletePostNodeResponse, CreatePostRequest)
from backend.schemas.job import PostJobResponse

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/create", response_model=PostJobResponse)
def create_post(
        request: CreatePostRequest,
        background_tasks: BackgroundTasks,
        response: Response,
        session_id: str = Depends(get_session_id),
        db: Session = Depends(get_db)
):
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    job_id = str(uuid.uuid4())

    job = PostJob(
        job_id=job_id,
        session_id=session_id,
        theme=request.theme,
        status="pending"
    )

    db.add(job)
    db.commit()

    background_tasks.add_task(
        generate_post_task,
        job_id=job_id,
        theme=request.theme,
        session_id=session_id,
    )
    return job

def generate_post_task(job_id: str, theme: str, session_id: str):
    db = SessionLocal()

    try:
        job = db.query(PostJob).filter(PostJob.job_id == job_id).first()
        if not job:
            return
        try:
            job.status = "processing"
            db.commit()

            post = {} # todo: generate post

            job.post_id = 1 # todo: update post id

            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = str(e)
            db.commit()
    finally:
        db.close()

@router.get("/{post_id}/complete", response_model=CompletePostResponse)
def get_complete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    complete_post = build_complete_post_tree(db, post)
    return complete_post


def build_complete_post_tree(db: Session, post: Post) -> CompletePostResponse:
    pass