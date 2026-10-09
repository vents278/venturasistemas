"""Acesso a emails — ETAPA 13 (thin)."""

from app.core.supabase_client import get_supabase


def list_repo(status=None, de=None, ate=None):
    sb = get_supabase()
    q = sb.table("emails").select("*")
    if status:
        q = q.eq("status", status)
    if de:
        q = q.gte("created_at", de)
    if ate:
        q = q.lte("created_at", ate)
    return (q.order("created_at").execute().data) or []


def get_repo(eid: str):
    sb = get_supabase()
    r = sb.table("emails").select("*").eq("id", eid).limit(1).execute()
    return r.data[0] if r.data else None


def find_por_he(he_id: str):
    sb = get_supabase()
    r = sb.table("emails").select("*").eq("hora_extra_id", he_id).order("created_at", desc=True).limit(1).execute()
    return r.data[0] if r.data else None


def create_repo(payload: dict):
    sb = get_supabase()
    return sb.table("emails").insert(payload).execute().data[0]


def update_repo(eid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("emails").update(payload).eq("id", eid).execute()
    return r.data[0] if r.data else None


def delete_repo(eid: str):
    sb = get_supabase()
    sb.table("emails").delete().eq("id", eid).execute()
