 # Pydantic request/response models
# core_api/app/models/schemas.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class StatementOut(BaseModel):
    id: UUID
    file_type: str
    status: str
    uploaded_at: datetime

class JobTrigger(BaseModel):
    statement_id: UUID

class JobStatusOut(BaseModel):
    id: UUID
    status: str
    k_optimal: int | None = None
    silhouette_score: float | None = None
    error_message: str | None = None

# core_api/app/models/schemas.py — additions

class ClusterSummary(BaseModel):
    cluster_id: UUID
    cluster_label: int
    keywords: list[str]
    txn_count: int
    total_amount: float
    txn_type_dominant: str  # 'credit' | 'debit' | 'mixed'

class CashFlowSummary(BaseModel):
    total_income: float
    total_expense: float
    net_cash_flow: float
    period_start: datetime | None = None
    period_end: datetime | None = None

class MonthlyTrend(BaseModel):
    month: str            # "2024-01"
    income: float
    expense: float

class AnalyticsDashboardOut(BaseModel):
    cash_flow: CashFlowSummary
    clusters: list[ClusterSummary]
    monthly_trend: list[MonthlyTrend]