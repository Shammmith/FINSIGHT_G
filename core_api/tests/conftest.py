# core_api/tests/conftest.py
import os

# Set dummy env vars BEFORE any app.* module is imported by test collection.
# This decouples "does the app boot" tests from requiring real Supabase creds.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SUPABASE_URL", "https://dummy.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "dummy_key")
os.environ.setdefault("JWT_SECRET", "test_secret")