# FinSight 📊🤖

**AI-Powered Financial Analytics & Unsupervised Transaction Clustering Platform**

FinSight is an enterprise-grade, full-stack application that ingests raw bank statements (PDF/CSV) and uses Machine Learning to automatically discover spending patterns. Instead of relying on rigid, hard-coded rules, FinSight uses **Semantic Sentence Embeddings (SBERT)** and **Unsupervised Clustering (K-Means)** to group transactions by actual semantic meaning, automatically determining the optimal number of spending categories.

## 🚀 Key Features

*   **Smart Ingestion & PII Scrubbing:** Parses PDFs and CSVs, automatically stripping Personally Identifiable Information (card numbers, SSNs, IBANs) via regex before data ever hits the database or ML model.
*   **Semantic Clustering:** Uses `all-MiniLM-L6-v2` (Sentence-Transformers) to map transactions into a 384-dimensional vector space. "SBUX" and "Starbucks" cluster together based on semantic meaning, not just lexical overlap.
*   **Automated K-Determination:** Implements the Kneedle algorithm (Elbow Method) and Silhouette Scoring to dynamically determine the optimal number of spending categories (K) without user intervention.
*   **Interpretable AI:** Runs TF-IDF over discovered clusters to automatically generate human-readable keyword tags (e.g., "coffee, cafe, latte") for dense vector clusters.
*   **Real-Time Vector Search:** Uses PostgreSQL with `pgvector` (`ivfflat` index) to classify new, incoming transactions against fitted cluster centroids in `< 50ms`.
*   **Interactive Dashboard:** React/Next.js frontend featuring Recharts for income vs. expense tracking and cluster analysis.

## 🏗️ Architecture & System Design

FinSight uses a **Decoupled 2-Service Architecture** to isolate I/O-bound API traffic from CPU-bound Machine Learning workloads.

![Architecture: React -> Core API (FastAPI) -> Supabase (Postgres+pgvector). Core API triggers ML Engine (FastAPI) asynchronously.]

### The Stack
*   **Frontend:** React, Next.js, Recharts, Axios
*   **Core API (I/O Bound):** FastAPI, SQLAlchemy 2.0 (asyncpg), Pydantic v2, PyJWT
*   **ML Engine (CPU Bound):** FastAPI, PyTorch, Sentence-Transformers, Scikit-Learn, Kneed
*   **Database & Storage:** Supabase (PostgreSQL 15), `pgvector`, `pgcrypto`, Supabase S3 Storage
*   **Infrastructure:** Render (Backend), Vercel (Frontend), cron-job.org (Serverless scheduling)

### Key Architectural Decisions
1.  **Why Decoupled instead of a Monolith?** The ML Engine requires ~500MB of PyTorch/SciPy dependencies and is heavily CPU-bound. The Core API is lightweight and I/O-bound. Separating them allows independent horizontal scaling and prevents ML jobs from starving authentication/upload requests.
2.  **Why `pgvector` instead of Pinecone?** At MVP scale, a dedicated vector DB introduces unnecessary network latency and data synchronization headaches. `pgvector` allows us to store transaction metadata and embeddings in the same ACID-compliant database, executing inference via a simple `<->` cosine distance SQL query.
3.  **Why SBERT + TF-IDF?** SBERT provides excellent *semantic grouping* but dense vectors are uninterpretable. TF-IDF provides excellent *interpretability* but poor semantic grouping. FinSight uses SBERT to form the clusters, and TF-IDF to label them.

## 💻 Local Development Setup

### Prerequisites
*   Python 3.11+
*   Node.js 18+
*   A free [Supabase](https://supabase.com/) account (for Postgres + pgvector)

### 1. Database Setup
Run the SQL script located in `core_api/alembic/versions/0001_init_pgvector_schema.py` in your Supabase SQL Editor to provision the tables, `pgvector`, and `pgcrypto` extensions.

### 2. Core API
```bash
cd core_api
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
# Create .env with DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_KEY, JWT_SECRET
uvicorn app.main:app --reload --port 8000
```
### 3. ML Engine
```bash
cd ml_engine
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 4. Frontend
```bash
cd frontend
npm install
# Create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## 🔒 Security & Compliance
- No PII Retention: Raw files are auto-purged after 48 hours via a scheduled batch job.

- Encryption at Rest: Raw descriptions are encrypted via AES-256 (pgcrypto).

- Stateless Auth: JWT-based authentication with bcrypt password hashing.