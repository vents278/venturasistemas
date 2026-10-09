"""Acesso a horas_extras — ETAPA 10 (thin)."""

from app.core.supabase_client import get_supabase


def list_repo(data=None, de=None, ate=None, funcionario_id=None, percentual=None):
    sb = get_supabase()
    q = sb.table("horas_extras").select("*")
    if data:
        q = q.eq("data", data)
    if de:
        q = q.gte("data", de)
    if ate:
        q = q.lte("data", ate)
    if funcionario_id:
        q = q.eq("funcionario_id", funcionario_id)
    if percentual:
        q = q.eq("percentual", percentual)
    return (q.order("data").execute().data) or []


def upsert_repo(funcionario_id: str, data_str: str, qtd: float, percentual: int):
    sb = get_supabase()
    r = (
        sb.table("horas_extras")
        .upsert(
            {"funcionario_id": funcionario_id, "data": data_str, "qtd_horas": qtd, "percentual": percentual},
            on_conflict="funcionario_id,data,percentual",
        )
        .execute()
    )
    return r.data[0]


def limpar_dia(funcionario_id: str, data_str: str):
    sb = get_supabase()
    sb.table("horas_extras").delete().eq("funcionario_id", funcionario_id).eq("data", data_str).execute()


def limpar_percentual(he_id: str):
    sb = get_supabase()
    sb.table("horas_extras").delete().eq("id", he_id).execute()
