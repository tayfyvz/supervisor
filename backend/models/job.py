from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func

from backend.db.database import Base

class PostJob(Base):
    __tablename__ = 'post_jobs'

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    session_id = Column(String, index=True)
    topic = Column(String)
    status = Column(String)
    post_id = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)