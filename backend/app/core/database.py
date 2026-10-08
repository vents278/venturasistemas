"""Conexão DB — ETAPA 2: apenas factory + health check.

ETAPA 3 (Supabase) vai plugar o DATABASE_URL real.
SQLAlchemy usado quando fizer sentido; Supabase client para Auth/Storage.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def get_engine():
    if not settings.DATABASE_URL:
        return None
    return create_engine(settings.DATABASE_URL, pool_pre_ping=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def db_ping() -> bool:
    engine = get_engine()
    if engine is None:
        return False
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
