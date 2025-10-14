from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class PostJobBase(BaseModel):
    theme: str

class PostJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    post_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True

class PostJobCreate(PostJobBase):
    pass

