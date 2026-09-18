# ml_engine/app/main.py
from dotenv import load_dotenv
load_dotenv()

import os
# Force CPU thread limits before importing torch
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import torch
torch.set_num_threads(1)  # constrained free-tier RAM/CPU

from fastapi import FastAPI
from app.routers import cluster, predict
from prometheus_client import make_asgi_app

app = FastAPI(title="FinSight ML Engine", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(cluster.router)
app.include_router(predict.router)
app.mount("/metrics", make_asgi_app())