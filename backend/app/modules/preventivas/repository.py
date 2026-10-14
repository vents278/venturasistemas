"""Acesso a preventivas — camada fina sobre Supabase (sem regra de negócio)."""

from app.core.supabase_client import get_supabase

SELECT = "*, funcionarios!preventivas_responsavel_id_fkey(nome,matricula)"


def list_repo(de=None, ate=None, data=None, area=None, status=None):
    sb = get_supabase()
    q = sb.table("preventivas").select(SELECT)
    if data:
        q = q.eq("data", data)
    if de:
        q = q.gte("data", de)
    if ate:
        q = q.lte("data", ate)
    if area:
        q = q.ilike("area", f"%{area}%")
    if status:
        q = q.eq("status", status)
    return (q.order("data").order("hora_inicio").execute().data) or []


def get_repo(pid: str):
    sb = get_supabase()
    r = sb.table("preventivas").select(SELECT).eq("id", pid).limit(1).execute()
    return r.data[0] if r.data else None


def create_repo(payload: dict):
    sb = get_supabase()
    return sb.table("preventivas").insert(payload).execute().data[0]


def update_repo(pid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("preventivas").update(payload).eq("id", pid).execute()
    return r.data[0] if r.data else None


def delete_repo(pid: str):
    sb = get_supabase()
    sb.table("preventivas").delete().eq("id", pid).execute()


# ---------- funcionários programados ----------
def list_funcionarios(pid: str):
    sb = get_supabase()
    r = (sb.table("preventiva_funcionarios")
         .select("*, funcionarios(id,nome,matricula,cargo,area,setor,jornada_id,jornadas(codigo))")
         .eq("preventiva_id", pid).order("created_at").execute())
    return r.data or []


def list_funcionarios_por(ids: list):
    if not ids:
        return []
    sb = get_supabase()
    r = (sb.table("preventiva_funcionarios")
         .select("*, funcionarios(id,nome,matricula,cargo,area,setor,jornada_id,jornadas(codigo))")
         .in_("preventiva_id", ids).execute())
    return r.data or []


def get_funcionario_row(pf_id: str):
    sb = get_supabase()
    r = sb.table("preventiva_funcionarios").select("*").eq("id", pf_id).limit(1).execute()
    return r.data[0] if r.data else None


def find_funcionario(pid: str, funcionario_id: str):
    sb = get_supabase()
    r = (sb.table("preventiva_funcionarios").select("*")
         .eq("preventiva_id", pid).eq("funcionario_id", funcionario_id).limit(1).execute())
    return r.data[0] if r.data else None


def create_funcionario(payload: dict):
    sb = get_supabase()
    return sb.table("preventiva_funcionarios").insert(payload).execute().data[0]


def update_funcionario(pf_id: str, payload: dict):
    sb = get_supabase()
    r = sb.table("preventiva_funcionarios").update(payload).eq("id", pf_id).execute()
    return r.data[0] if r.data else None


def delete_funcionario(pf_id: str):
    sb = get_supabase()
    sb.table("preventiva_funcionarios").delete().eq("id", pf_id).execute()


# ---------- OS da preventiva ----------
def list_os(pid: str):
    sb = get_supabase()
    r = (sb.table("preventiva_os").select("*")
         .eq("preventiva_id", pid).order("created_at").execute())
    return r.data or []


def list_os_por(ids: list):
    if not ids:
        return []
    sb = get_supabase()
    r = (sb.table("preventiva_os").select("*")
         .in_("preventiva_id", ids).execute())
    return r.data or []


def list_os_funcionario(pf_id: str):
    sb = get_supabase()
    r = (sb.table("preventiva_os").select("*")
         .eq("preventiva_funcionario_id", pf_id).order("created_at").execute())
    return r.data or []


def get_os_row(osrow_id: str):
    sb = get_supabase()
    r = sb.table("preventiva_os").select("*").eq("id", osrow_id).limit(1).execute()
    return r.data[0] if r.data else None


def find_os_dup(pf_id: str, os_codigo: str):
    sb = get_supabase()
    r = (sb.table("preventiva_os").select("*")
         .eq("preventiva_funcionario_id", pf_id).eq("os_codigo", os_codigo).limit(1).execute())
    return r.data[0] if r.data else None


def create_os(payload: dict):
    sb = get_supabase()
    return sb.table("preventiva_os").insert(payload).execute().data[0]


def update_os(osrow_id: str, payload: dict):
    sb = get_supabase()
    r = sb.table("preventiva_os").update(payload).eq("id", osrow_id).execute()
    return r.data[0] if r.data else None


def delete_os(osrow_id: str):
    sb = get_supabase()
    sb.table("preventiva_os").delete().eq("id", osrow_id).execute()


# ---------- apoio ----------
def get_funcionario(func_id: str):
    sb = get_supabase()
    r = (sb.table("funcionarios")
         .select("id,nome,matricula,ativo,desligamento,empresa_id")
         .eq("id", func_id).limit(1).execute())
    return r.data[0] if r.data else None


def get_os_cadastrada(os_id: str):
    sb = get_supabase()
    r = sb.table("ordens_servico").select("id,codigo,descricao").eq("id", os_id).limit(1).execute()
    return r.data[0] if r.data else None


def achar_os_por_codigo(codigo: str):
    sb = get_supabase()
    r = sb.table("ordens_servico").select("id,codigo").eq("codigo", codigo).limit(1).execute()
    return r.data[0] if r.data else None


def apropriacoes_func_data(funcionario_id: str, data_str: str):
    sb = get_supabase()
    r = (sb.table("apropriacoes").select("id,os_id,horas,data")
         .eq("funcionario_id", funcionario_id).eq("data", data_str).execute())
    return r.data or []
