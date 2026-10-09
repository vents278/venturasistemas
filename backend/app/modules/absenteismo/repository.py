"""Acesso a tipos_ausencia + absenteismo — ETAPA 14 (thin)."""

from app.core.supabase_client import get_supabase

SELECT = "*, funcionarios(nome,matricula,setor), tipos_ausencia(codigo,descricao)"


def list_tipos():
    sb = get_supabase()
    return (sb.table("tipos_ausencia").select("*").order("codigo").execute().data) or []


def create_tipo(payload: dict):
    sb = get_supabase()
    return sb.table("tipos_ausencia").insert(payload).execute().data[0]


def count_uso_tipo(tipo_id: int) -> int:
    sb = get_supabase()
    r = sb.table("absenteismo").select("id", count="exact").eq("tipo_id", tipo_id).limit(1).execute()
    return r.count or 0


def delete_tipo(tipo_id: int):
    sb = get_supabase()
    sb.table("tipos_ausencia").delete().eq("id", tipo_id).execute()


def list_repo(de=None, ate=None, funcionario_id=None, tipo_id=None, setor=None):
    sb = get_supabase()
    q = sb.table("absenteismo").select(SELECT)
    if de:
        q = q.gte("data", de)
    if ate:
        q = q.lte("data", ate)
    if funcionario_id:
        q = q.eq("funcionario_id", funcionario_id)
    if tipo_id:
        q = q.eq("tipo_id", tipo_id)
    rows = (q.order("data").execute().data) or []
    if setor:
        rows = [r for r in rows if (r.get("funcionarios") or {}).get("setor") == setor]
    return rows


def get_repo(aid: str):
    sb = get_supabase()
    r = sb.table("absenteismo").select(SELECT).eq("id", aid).limit(1).execute()
    return r.data[0] if r.data else None


def create_repo(payload: dict):
    sb = get_supabase()
    return sb.table("absenteismo").insert(payload).execute().data[0]


def update_repo(aid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("absenteismo").update(payload).eq("id", aid).execute()
    return r.data[0] if r.data else None


def delete_repo(aid: str):
    sb = get_supabase()
    sb.table("absenteismo").delete().eq("id", aid).execute()


def get_tipo(tipo_id: int):
    sb = get_supabase()
    r = sb.table("tipos_ausencia").select("*").eq("id", tipo_id).limit(1).execute()
    return r.data[0] if r.data else None


def get_funcionario(func_id: str):
    sb = get_supabase()
    r = sb.table("funcionarios").select("id,ativo,desligamento").eq("id", func_id).limit(1).execute()
    return r.data[0] if r.data else None


def list_ativos(setor=None):
    sb = get_supabase()
    q = sb.table("funcionarios").select("id,setor").eq("ativo", True)
    rows = (q.execute().data) or []
    return [r for r in rows if not setor or r.get("setor") == setor]
