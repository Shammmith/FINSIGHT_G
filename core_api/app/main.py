# core_api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import statements, jobs, auth, admin
from app.health import router as health_router
from app.config import settings
from app.routers import statements, jobs, auth, analytics   # add analytics import

app = FastAPI(title="FinSight Core API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://finsight-iaijahk1d-xyz-0e42.vercel.app",
        "https://finsight-git-main-xyz-0e42.vercel.app"
        
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(dsn=settings.SENTRY_DSN, integrations=[FastApiIntegration()], traces_sample_rate=0.5)

app.include_router(health_router)
app.include_router(auth.router)
app.include_router(statements.router)
app.include_router(jobs.router)
app.include_router(analytics.router)