"""Cliente Supabase — ETAPA 3.

Service key só no backend (bypassa RLS). Anon key para fluxos autenticados.
Nunca expor service key no frontend.
"""

from functools import lru_cache

from supabase import create_client

from app.core.config import settings


@lru_cache
def get_supabase():
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise RuntimeError("Configure SUPABASE_URL e SUPABASE_SERVICE_KEY no .env")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
