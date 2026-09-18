# core_api/app/routers/jobs.py — Option B
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models.db_models import ClusteringJob
from app.models.schemas import JobTrigger, JobStatusOut
from app.services.orchestrator import run_clustering_job

router = APIRouter(prefix="/api/v1/cluster", tags=["jobs"])

@router.post("", status_code=202)
async def trigger_clustering(
    payload: JobTrigger, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    job = ClusteringJob(id=uuid.uuid4(), statement_id=payload.statement_id, status="QUEUED")
    db.add(job)
    await db.commit()

    background_tasks.add_task(run_clustering_job, job.id, payload.statement_id)
    return {"job_id": str(job.id), "status": "QUEUED"}

@router.get("/{job_id}/status", response_model=JobStatusOut)
async def get_job_status(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClusteringJob).where(ClusteringJob.id == job_id))
    job = result.scalar_one()
    return JobStatusOut(
        id=job.id, status=job.status, k_optimal=job.k_optimal,
        silhouette_score=job.silhouette_score, error_message=job.error_message,
    )