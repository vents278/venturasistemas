"""Acesso a ordens_servico — ETAPA 8 (thin)."""

from app.core.supabase_client import get_supabase


def list_repo(q=None, status=None):
    sb = get_supabase()
    query = sb.table("ordens_servico").select("*")
    if q:
        query = query.or_(f"codigo.ilike.%{q}%,descricao.ilike.%{q}%")
    if status:
        query = query.eq("status", status)
    return (query.order("codigo").execute().data) or []


def get_repo(os_id: str):
    sb = get_supabase()
    r = sb.table("ordens_servico").select("*").eq("id", os_id).limit(1).execute()
    return r.data[0] if r.data else None


def create_repo(payload: dict):
    sb = get_supabase()
    return sb.table("ordens_servico").insert(payload).execute().data[0]


def update_repo(os_id: str, payload: dict):
    sb = get_supabase()
    r = sb.table("ordens_servico").update(payload).eq("id", os_id).execute()
    return r.data[0] if r.data else None


def count_uso(os_id: str) -> int:
    sb = get_supabase()
    r = sb.table("apropriacoes").select("id", count="exact").eq("os_id", os_id).limit(1).execute()
    return r.count or 0


def delete_repo(os_id: str):
    sb = get_supabase()
    sb.table("ordens_servico").delete().eq("id", os_id).execute()
