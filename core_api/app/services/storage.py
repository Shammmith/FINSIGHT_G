# Supabase Storage client
# core_api/app/services/storage.py
from supabase import create_client
from supabase.client import Client
from app.config import settings
from functools import lru_cache

#supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

@lru_cache
def get_supabase_client() -> Client:
    """Lazy singleton — client is only created the FIRST time it's actually
    needed (e.g., on a real file upload), not at module import time.
    This keeps unrelated tests/routes fully isolated from Supabase availability."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def upload_statement_file(file_bytes: bytes, path: str) -> str:
    get_supabase_client().storage.from_(settings.SUPABASE_BUCKET).upload(
        path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"}
    )
    return f"{settings.SUPABASE_BUCKET}/{path}"

def delete_statement_file(path: str):
    """Called by a scheduled purge job per the 48h retention policy."""
    get_supabase_client().storage.from_(settings.SUPABASE_BUCKET).remove([path])