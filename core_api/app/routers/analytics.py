# core_api/app/routers/analytics.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.db import get_db
from app.models.db_models import Transaction, Statement, Cluster, ClusteringJob, User
from app.models.schemas import AnalyticsDashboardOut, CashFlowSummary, ClusterSummary, MonthlyTrend
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/dashboard/{statement_id}", response_model=AnalyticsDashboardOut)
async def get_dashboard(
    statement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ownership check — never trust the statement_id belongs to the caller without verifying
    stmt_check = await db.execute(
        select(Statement).where(Statement.id == statement_id, Statement.user_id == current_user.id)
    )
    if not stmt_check.scalar_one_or_none():
        raise HTTPException(404, "Statement not found or access denied")

    # --- 1. Cash flow summary (income vs expense) ---
    cash_flow_result = await db.execute(
        select(
            func.sum(case((Transaction.txn_type == "credit", Transaction.amount), else_=0)).label("income"),
            func.sum(case((Transaction.txn_type == "debit", Transaction.amount), else_=0)).label("expense"),
            func.min(Transaction.txn_date).label("start"),
            func.max(Transaction.txn_date).label("end"),
        ).where(Transaction.statement_id == statement_id)
    )
    row = cash_flow_result.one()
    income = float(row.income or 0)
    expense = float(row.expense or 0)

    cash_flow = CashFlowSummary(
        total_income=income, total_expense=expense, net_cash_flow=income - expense,
        period_start=row.start, period_end=row.end,
    )

    # --- 2. Cluster-level summary (joined via latest job for this statement) ---
    latest_job = await db.execute(
        select(ClusteringJob.id)
        .where(ClusteringJob.statement_id == statement_id, ClusteringJob.status == "DONE")
        .order_by(ClusteringJob.completed_at.desc())
        .limit(1)
    )
    job_id = latest_job.scalar_one_or_none()

    clusters_out = []
    if job_id:
        cluster_rows = await db.execute(
            select(
                Cluster.id, Cluster.cluster_label, Cluster.top_keywords,
                func.count(Transaction.id).label("txn_count"),
                func.sum(Transaction.amount).label("total_amount"),
                func.mode().within_group(Transaction.txn_type).label("dominant_type"),
            )
            .join(Transaction, Transaction.cluster_id == Cluster.id)
            .where(Cluster.job_id == job_id)
            .group_by(Cluster.id, Cluster.cluster_label, Cluster.top_keywords, Transaction.statement_id)
        )
        for c in cluster_rows:
            clusters_out.append(ClusterSummary(
                cluster_id=c.id, cluster_label=c.cluster_label, keywords=c.top_keywords,
                txn_count=c.txn_count, total_amount=float(c.total_amount or 0),
                txn_type_dominant=c.dominant_type,
            ))

    # --- 3. Monthly trend (income vs expense over time) ---
    month_expr = func.to_char(Transaction.txn_date, "YYYY-MM")
    monthly_result = await db.execute(
        select(
            month_expr.label("month"),
            func.sum(case((Transaction.txn_type == "credit", Transaction.amount), else_=0)).label("income"),
            func.sum(case((Transaction.txn_type == "debit", Transaction.amount), else_=0)).label("expense"),
        )
        .where(Transaction.statement_id == statement_id)
        .group_by(month_expr)
        .order_by(month_expr)
    )
    monthly_trend = [
        MonthlyTrend(month=m.month, income=float(m.income or 0), expense=float(m.expense or 0))
        for m in monthly_result
    ]

    return AnalyticsDashboardOut(cash_flow=cash_flow, clusters=clusters_out, monthly_trend=monthly_trend)