"""Acesso a feriados — ETAPA 10 (thin)."""

from app.core.supabase_client import get_supabase


def list_repo(ano: int | None = None):
    sb = get_supabase()
    q = sb.table("feriados").select("*")
    if ano:
        q = q.gte("data", f"{ano}-01-01").lte("data", f"{ano}-12-31")
    return (q.order("data").execute().data) or []


def get_repo(data_str: str):
    sb = get_supabase()
    r = sb.table("feriados").select("*").eq("data", data_str).limit(1).execute()
    return r.data[0] if r.data else None


def create_repo(payload: dict):
    sb = get_supabase()
    return sb.table("feriados").insert(payload).select().execute().data[0]


def delete_repo(data_str: str):
    sb = get_supabase()
    sb.table("feriados").delete().eq("data", data_str).execute()


def is_feriado(data_str: str) -> bool:
    return get_repo(data_str) is not None
