# BackgroundTasks job runner
# core_api/app/services/orchestrator.py — Option B: BackgroundTasks + DB polling
from sqlalchemy import select, update
from datetime import datetime
import uuid
from app.db import AsyncSessionLocal
from app.models.db_models import Transaction, ClusteringJob, Cluster
from app.services.ml_client import call_ml_cluster

async def run_clustering_job(job_id: uuid.UUID, statement_id: uuid.UUID):
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(ClusteringJob).where(ClusteringJob.id == job_id)
            .values(status="PROCESSING", started_at=datetime.utcnow())
        )
        await db.commit()

        try:
            result = await db.execute(
                select(Transaction).where(Transaction.statement_id == statement_id)
            )
            txns = result.scalars().all()
            descriptions = [t.cleaned_description for t in txns]

            ml_result = await call_ml_cluster(descriptions)

            # Persist clusters
            cluster_id_map = {}
            for label, centroid in enumerate(ml_result["centroids"]):
                cluster = Cluster(
                    job_id=job_id,
                    cluster_label=label,
                    top_keywords=ml_result["keywords"][str(label)],
                    centroid_vector=centroid,
                    txn_count=ml_result["labels"].count(label),
                )
                db.add(cluster)
                await db.flush()
                cluster_id_map[label] = cluster.id

            # Assign each transaction to its cluster + embedding
            for txn, label, emb in zip(txns, ml_result["labels"], ml_result["embeddings"]):
                txn.cluster_id = cluster_id_map[label]
                txn.embedding = emb

            await db.execute(
                update(ClusteringJob).where(ClusteringJob.id == job_id)
                .values(
                    status="DONE",
                    k_optimal=ml_result["optimal_k"],
                    silhouette_score=ml_result["silhouette"],
                    completed_at=datetime.utcnow(),
                )
            )
            await db.commit()

        except Exception as e:
            await db.execute(
                update(ClusteringJob).where(ClusteringJob.id == job_id)
                .values(status="FAILED", error_message=str(e))
            )
            await db.commit()