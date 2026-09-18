# core_api/app/routers/admin.py
from datetime import datetime
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models.db_models import Statement
from app.services.storage import delete_statement_file
from app.config import settings

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/purge-expired")
async def purge_expired_statements(x_admin_key: str = Header(None)):
    """
    Deletes raw statement files from Supabase Storage whose retention
    window (purge_at) has passed. Triggered externally by cron-job.org
    every few hours — this is a batch HTTP endpoint, not a background
    cron process, since free-tier compute has no persistent scheduler.
    """
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(403, "Invalid admin key")

    purged_count = 0
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        result = await db.execute(
            select(Statement).where(
                Statement.purge_at <= now,
                Statement.status != "PURGED",
            )
        )
        expired = result.scalars().all()

        for stmt in expired:
            try:
                delete_statement_file(stmt.storage_path)
                stmt.status = "PURGED"
                purged_count += 1
            except Exception as e:
                print(f"Failed to purge {stmt.id}: {e}")  # log, don't block the batch

        await db.commit()

    return {"purged": purged_count, "checked_at": now.isoformat()}