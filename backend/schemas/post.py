from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class PostOptionSchema(BaseModel):
    text: str
    node_id: int

class PostNodeBase(BaseModel):
    content: str
    is_root: bool = False
    is_ending: bool = False
    options: List[PostOptionSchema] = []

class CompletePostNodeResponse(PostNodeBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    title: str
    session_id: str

    class Config:
        from_attributes = True

class CreatePostRequest(BaseModel):
    topic: str

class CompletePostResponse(PostBase):
    id: int
    created_at: datetime
    root_node: Optional[CompletePostNodeResponse] = None
    all_nodes: Dict[int, CompletePostNodeResponse] = {}

    class Config:
        from_attributes = True