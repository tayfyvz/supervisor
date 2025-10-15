import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks
from sqlalchemy.orm import Session

from backend.db.database import get_db, SessionLocal
from backend.models.post import Post, PostNode
from backend.models.job import PostJob
from backend.schemas.post import (CompletePostResponse, CompletePostNodeResponse, CreatePostRequest, PostOptionSchema)
from backend.schemas.job import PostJobResponse

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.get("/", response_model=List[CompletePostResponse])
def list_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all posts with pagination"""
    posts = db.query(Post).offset(skip).limit(limit).all()
    return [build_complete_post_tree(db, post) for post in posts]


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
        topic=request.topic,
        status="pending"
    )

    db.add(job)
    db.commit()

    background_tasks.add_task(
        generate_post_task,
        job_id=job_id,
        topic=request.topic,
        session_id=session_id,
    )
    return job

def generate_post_task(job_id: str, topic: str, session_id: str):
    db = SessionLocal()

    try:
        job = db.query(PostJob).filter(PostJob.job_id == job_id).first()
        if not job:
            return
        try:
            job.status = "processing"
            db.commit()

            # Generate the post using the PostGenerator
            from backend.core.post_generator import PostGenerator
            post = PostGenerator.generate_post(db, session_id, topic)

            job.post_id = post.id
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


@router.get("/nodes/{node_id}", response_model=CompletePostNodeResponse)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(PostNode).filter(PostNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Parse options from JSON
    options = []
    if node.options:
        for option in node.options:
            options.append(PostOptionSchema(
                text=option["text"],
                node_id=option["node_id"]
            ))

    return CompletePostNodeResponse(
        id=node.id,
        content=node.content,
        is_root=node.is_root,
        is_ending=node.is_ending,
        options=options,
        created_at=node.created_at
    )


def build_complete_post_tree(db: Session, post: Post) -> CompletePostResponse:
    """Build a complete post tree with all nodes and their relationships"""
    # Get all nodes for this post
    nodes = db.query(PostNode).filter(PostNode.post_id == post.id).all()
    
    # Create a mapping of node_id to node data
    nodes_dict = {}
    root_node = None
    
    for node in nodes:
        # Parse options from JSON
        options = []
        if node.options:
            for option in node.options:
                options.append(PostOptionSchema(
                    text=option["text"],
                    node_id=option["node_id"]
                ))
        
        node_data = CompletePostNodeResponse(
            id=node.id,
            content=node.content,
            is_root=node.is_root,
            is_ending=node.is_ending,
            options=options,
            created_at=node.created_at
        )
        
        nodes_dict[node.id] = node_data
        
        if node.is_root:
            root_node = node_data
    
    return CompletePostResponse(
        id=post.id,
        title=post.title,
        session_id=post.session_id,
        created_at=post.created_at,
        root_node=root_node,
        all_nodes=nodes_dict
    )