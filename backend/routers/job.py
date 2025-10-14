from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.job import PostJob
from backend.schemas.job import PostJobResponse

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)


@router.get("/{job_id}", response_model=PostJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(PostJob).filter(PostJob.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job