"""Acesso a public.funcionarios via Supabase — ETAPA 5 (thin, sem regra)."""

from app.core.supabase_client import get_supabase

SELECT = "*, jornadas(codigo,nome)"


def list_repo(q=None, ativo=None, setor=None, area=None, jornada_id=None, page=1, limit=20):
    sb = get_supabase()
    query = sb.table("funcionarios").select(SELECT, count="exact")
    if q:
        query = query.or_(f"nome.ilike.%{q}%,matricula.ilike.%{q}%")
    if ativo is not None:
        query = query.eq("ativo", ativo)
    if setor:
        query = query.eq("setor", setor)
    if area:
        query = query.eq("area", area)
    if jornada_id:
        query = query.eq("jornada_id", jornada_id)
    start = (page - 1) * limit
    res = query.order("nome").range(start, start + limit - 1).execute()
    return {"items": res.data or [], "total": res.count or 0}


def get_repo(func_id: str):
    sb = get_supabase()
    r = sb.table("funcionarios").select(SELECT).eq("id", func_id).limit(1).execute()
    return r.data[0] if r.data else None


def create_repo(payload: dict):
    sb = get_supabase()
    r = sb.table("funcionarios").insert(payload).execute()
    return r.data[0]


def update_repo(func_id: str, payload: dict):
    sb = get_supabase()
    r = sb.table("funcionarios").update(payload).eq("id", func_id).execute()
    return r.data[0] if r.data else None


def set_ativo_repo(func_id: str, ativo: bool):
    return update_repo(func_id, {"ativo": ativo})
