# SQLAlchemy ORM
# core_api/app/models/db_models.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer, Float, Text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector
from datetime import datetime, timedelta

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Statement(Base):
    __tablename__ = "statements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    file_type = Column(String(10), nullable=False)
    storage_path = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING")
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    purge_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow() + timedelta(hours=48))

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("statements.id", ondelete="CASCADE"))
    txn_date = Column(DateTime, nullable=False)
    raw_description_enc = Column(LargeBinary)
    cleaned_description = Column(Text, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    txn_type = Column(String(10), nullable=False)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"), nullable=True)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class ClusteringJob(Base):
    __tablename__ = "clustering_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("statements.id"))
    status = Column(String(20), default="QUEUED")
    k_optimal = Column(Integer, nullable=True)
    silhouette_score = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Cluster(Base):
    __tablename__ = "clusters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("clustering_jobs.id", ondelete="CASCADE"))
    cluster_label = Column(Integer, nullable=False)
    top_keywords = Column(JSONB, nullable=False)
    txn_count = Column(Integer)
    total_amount = Column(Numeric(14, 2))
    centroid_vector = Column(Vector(384), nullable=False)