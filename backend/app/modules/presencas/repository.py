"""Acesso a presencas + status_presenca — ETAPA 7 (thin, sem regra)."""

from app.core.supabase_client import get_supabase

SELECT = "*, funcionarios(nome,matricula,setor)"


def list_repo(data=None, de=None, ate=None, funcionario_id=None, status=None):
    sb = get_supabase()
    q = sb.table("presencas").select(SELECT)
    if data:
        q = q.eq("data", data)
    if de:
        q = q.gte("data", de)
    if ate:
        q = q.lte("data", ate)
    if funcionario_id:
        q = q.eq("funcionario_id", funcionario_id)
    if status:
        q = q.eq("status_codigo", status)
    return (q.order("data").execute().data) or []


def get_repo(pid: str):
    sb = get_supabase()
    r = sb.table("presencas").select(SELECT).eq("id", pid).limit(1).execute()
    return r.data[0] if r.data else None


def upsert_repo(payload: dict):
    sb = get_supabase()
    r = (
        sb.table("presencas")
        .upsert(payload, on_conflict="funcionario_id,data")
        .select()
        .execute()
    )
    return r.data[0]


def update_repo(pid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("presencas").update(payload).eq("id", pid).select().execute()
    return r.data[0] if r.data else None


def delete_repo(pid: str):
    sb = get_supabase()
    sb.table("presencas").delete().eq("id", pid).execute()


def list_status():
    sb = get_supabase()
    return (sb.table("status_presenca").select("*").order("codigo").execute().data) or []


def get_status(codigo: str):
    sb = get_supabase()
    r = sb.table("status_presenca").select("*").eq("codigo", codigo).limit(1).execute()
    return r.data[0] if r.data else None


def get_funcionario(func_id: str):
    sb = get_supabase()
    r = (
        sb.table("funcionarios")
        .select("id,ativo,desligamento,jornada_id")
        .eq("id", func_id)
        .limit(1)
        .execute()
    )
    return r.data[0] if r.data else None
