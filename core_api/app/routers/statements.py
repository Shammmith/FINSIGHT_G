# core_api/app/routers/statements.py
import uuid
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models.db_models import Statement, Transaction, User
from app.services.parser import parse_csv, parse_pdf
from app.services.storage import upload_statement_file
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/statements", tags=["statements"])


@router.post("/upload")
async def upload_statement(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()
    ext = file.filename.split(".")[-1].lower()
    if ext not in ("csv", "pdf"):
        raise HTTPException(400, "Only CSV/PDF supported")

    statement_id = uuid.uuid4()
    storage_path = f"{current_user.id}/{statement_id}.{ext}"
    upload_statement_file(file_bytes, storage_path)

    statement = Statement(
        id=statement_id,
        user_id=current_user.id,
        file_type=ext,
        storage_path=storage_path,
    )
    db.add(statement)

    records = parse_csv(file_bytes) if ext == "csv" else parse_pdf(file_bytes)
    for r in records:
        db.add(Transaction(
            statement_id=statement_id,
            txn_date=r["txn_date"],
            cleaned_description=r["cleaned_description"],
            amount=r["amount"],
            txn_type=r["txn_type"],
        ))

    statement.status = "PARSED"
    await db.commit()
    return {"statement_id": str(statement_id), "transactions_parsed": len(records)}