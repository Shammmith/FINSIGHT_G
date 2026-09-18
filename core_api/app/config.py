# core_api/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ADMIN_API_KEY: str
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_BUCKET: str = "statements"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    ML_ENGINE_URL: str = "http://localhost:8001"
    SENTRY_DSN: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()