from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

class PostOptionsSchema(BaseModel):
    title: str
    node_id: Optional[int] = None

class PostNodeBase(BaseModel):
    content: str
    is_blog: bool = False
    is_linkedin: bool = False

class CompletePostNodeResponse(PostNodeBase):
    id: int
    options: List[PostOptionsSchema] = []
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    title: str
    section_id: Optional[int] = None

    class Config:
        from_attributes = True

class CreatePostRequest(BaseModel):
    theme: str

class CompletePostResponse(PostBase):
    id: int
    created_at: datetime
    root_node: CompletePostNodeResponse
    all_nodes: Dict[int, CompletePostNodeResponse]

    class Config:
        from_attributes = True