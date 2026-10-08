"""Acesso a pendências — ETAPA 11 (thin). Idempotência via busca + update (NULL-safe)."""

from app.core.supabase_client import get_supabase


def list_repo(status=None, tipo=None, funcionario_id=None, de=None, ate=None):
    sb = get_supabase()
    q = sb.table("pendencias").select("*")
    if status:
        q = q.eq("status", status)
    if tipo:
        q = q.eq("tipo", tipo)
    if funcionario_id:
        q = q.eq("funcionario_id", funcionario_id)
    if de:
        q = q.gte("data_ref", de)
    if ate:
        q = q.lte("data_ref", ate)
    return (q.order("data_ref").execute().data) or []


def get_repo(pid: str):
    sb = get_supabase()
    r = sb.table("pendencias").select("*").eq("id", pid).limit(1).execute()
    return r.data[0] if r.data else None


def find_aberta(tipo: str, funcionario_id: str, data_ref: str):
    sb = get_supabase()
    r = (
        sb.table("pendencias").select("*")
        .eq("tipo", tipo).eq("funcionario_id", funcionario_id)
        .eq("data_ref", data_ref).eq("status", "ABERTA").limit(1).execute()
    )
    return r.data[0] if r.data else None


def list_abertas_por_data(data_ref: str, tipos: list | None = None):
    sb = get_supabase()
    q = sb.table("pendencias").select("*").eq("data_ref", data_ref).eq("status", "ABERTA")
    if tipos:
        q = q.in_("tipo", tipos)
    return (q.execute().data) or []


def create_repo(payload: dict):
    sb = get_supabase()
    return sb.table("pendencias").insert(payload).select().execute().data[0]


def update_repo(pid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("pendencias").update(payload).eq("id", pid).select().execute()
    return r.data[0] if r.data else None
