# ml_engine/app/routers/predict.py
import time
from fastapi import APIRouter, HTTPException
from prometheus_client import Histogram
from sqlalchemy import create_engine, text
from app.pipeline import HybridClusteringPipeline
import os

router = APIRouter()
LATENCY = Histogram("predict_latency_seconds", "Prediction latency")
pipeline = HybridClusteringPipeline()
engine = create_engine(os.environ["DATABASE_URL"])

@router.post("/api/v1/predict")
async def predict(payload: dict):
    start = time.time()
    embedding = pipeline._embed([payload["description"]])[0].tolist()

    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT cluster_label, top_keywords,
                       centroid_vector <-> CAST(:emb AS vector) AS distance
                FROM clusters
                WHERE job_id = :job_id
                ORDER BY centroid_vector <-> CAST(:emb AS vector)
                LIMIT 1
            """),
            {"emb": embedding, "job_id": payload["job_id"]},
        ).first()

    if not row:
        raise HTTPException(404, "No clusters found for this job")

    latency_ms = (time.time() - start) * 1000
    LATENCY.observe(latency_ms / 1000)
    return {"cluster_label": row.cluster_label, "keywords": row.top_keywords,
            "distance": float(row.distance), "latency_ms": round(latency_ms, 2)}