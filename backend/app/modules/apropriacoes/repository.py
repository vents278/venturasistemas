"""Acesso a apropriacoes — ETAPA 8 (thin). Saldo usa rpc carga_prevista + soma local."""

from app.core.supabase_client import get_supabase

SELECT = "*, ordens_servico(codigo,descricao)"


def list_repo(data=None, de=None, ate=None, funcionario_id=None, os_id=None):
    sb = get_supabase()
    q = sb.table("apropriacoes").select(SELECT)
    if data:
        q = q.eq("data", data)
    if de:
        q = q.gte("data", de)
    if ate:
        q = q.lte("data", ate)
    if funcionario_id:
        q = q.eq("funcionario_id", funcionario_id)
    if os_id:
        q = q.eq("os_id", os_id)
    return (q.order("data").execute().data) or []


def get_repo(ap_id: str):
    sb = get_supabase()
    r = sb.table("apropriacoes").select(SELECT).eq("id", ap_id).limit(1).execute()
    return r.data[0] if r.data else None


def upsert_repo(payload: dict):
    sb = get_supabase()
    r = sb.table("apropriacoes").upsert(payload, on_conflict="funcionario_id,data,os_id").execute()
    return r.data[0]


def update_repo(ap_id: str, payload: dict):
    sb = get_supabase()
    r = sb.table("apropriacoes").update(payload).eq("id", ap_id).execute()
    return r.data[0] if r.data else None


def delete_repo(ap_id: str):
    sb = get_supabase()
    sb.table("apropriacoes").delete().eq("id", ap_id).execute()


def total_dia(funcionario_id: str, data_str: str, ignorar_id: str | None = None) -> float:
    sb = get_supabase()
    q = sb.table("apropriacoes").select("id,horas").eq("funcionario_id", funcionario_id).eq("data", data_str)
    rows = (q.execute().data) or []
    return round(sum(float(r["horas"]) for r in rows if r["id"] != ignorar_id), 2)


def carga_prevista(funcionario_id: str, data_str: str) -> float:
    sb = get_supabase()
    r = sb.rpc("carga_prevista", {"p_funcionario": funcionario_id, "p_data": data_str}).execute()
    return float(r.data or 0)


def get_funcionario(func_id: str):
    sb = get_supabase()
    r = sb.table("funcionarios").select("id,ativo,desligamento").eq("id", func_id).limit(1).execute()
    return r.data[0] if r.data else None


def get_os(os_id: str):
    sb = get_supabase()
    r = sb.table("ordens_servico").select("id").eq("id", os_id).limit(1).execute()
    return r.data[0] if r.data else None
