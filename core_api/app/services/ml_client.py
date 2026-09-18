# HTTP client -> ML Engine
# core_api/app/services/ml_client.py
import httpx
from app.config import settings

async def call_ml_cluster(descriptions: list[str]) -> dict:
    async with httpx.AsyncClient(timeout=160.0) as client:
        resp = await client.post(
            f"{settings.ML_ENGINE_URL}/api/v1/cluster",
            json={"descriptions": descriptions},
        )
        resp.raise_for_status()
        return resp.json()

async def call_ml_predict(description: str, job_id: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{settings.ML_ENGINE_URL}/api/v1/predict",
            json={"description": description, "job_id": job_id},
        )
        resp.raise_for_status()
        return resp.json()