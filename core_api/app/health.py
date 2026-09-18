# core_api/app/health.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}   # target for cron-job.org keep-alive pings