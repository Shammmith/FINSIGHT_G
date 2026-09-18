# ml_engine/app/routers/cluster.py
from fastapi import APIRouter
from app.pipeline import HybridClusteringPipeline

router = APIRouter()
pipeline = HybridClusteringPipeline()

@router.post("/api/v1/cluster")
async def cluster(payload: dict):
    """Synchronous from ML Engine's perspective — Core API calls this
    from within its own BackgroundTask, so it's already off the user's request thread."""
    result = pipeline.run(payload["descriptions"])
    # Convert int keys to str for JSON compliance
    result["keywords"] = {str(k): v for k, v in result["keywords"].items()}
    return result