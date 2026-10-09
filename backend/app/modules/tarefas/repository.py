"""Acesso a tarefas + filhas — ETAPA 12 (thin)."""

from app.core.supabase_client import get_supabase


def list_repo(status=None, responsavel_id=None, prioridade=None, q=None):
    sb = get_supabase()
    query = sb.table("tarefas").select("*")
    if status:
        query = query.eq("status", status)
    if responsavel_id:
        query = query.eq("responsavel_id", responsavel_id)
    if prioridade:
        query = query.eq("prioridade", prioridade)
    if q:
        query = query.ilike("titulo", f"%{q}%")
    return (query.order("created_at").execute().data) or []


def get_repo(tid: str):
    sb = get_supabase()
    r = sb.table("tarefas").select("*").eq("id", tid).limit(1).execute()
    return r.data[0] if r.data else None


def detalhar_repo(tid: str) -> dict | None:
    sb = get_supabase()
    t = sb.table("tarefas").select("*").eq("id", tid).limit(1).execute()
    if not t.data:
        return None
    row = t.data[0]
    row["checklists"] = sb.table("tarefa_checklists").select("*").eq("tarefa_id", tid).execute().data or []
    row["comentarios"] = sb.table("tarefa_comentarios").select("*").eq("tarefa_id", tid).order("created_at").execute().data or []
    row["anexos"] = sb.table("tarefa_anexos").select("*").eq("tarefa_id", tid).execute().data or []
    return row


def create_repo(payload: dict):
    sb = get_supabase()
    return sb.table("tarefas").insert(payload).execute().data[0]


def update_repo(tid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("tarefas").update(payload).eq("id", tid).execute()
    return r.data[0] if r.data else None


def delete_repo(tid: str):
    sb = get_supabase()
    sb.table("tarefas").delete().eq("id", tid).execute()


def find_por_pendencia(pid: str):
    sb = get_supabase()
    r = sb.table("tarefas").select("id").eq("pendencia_origem_id", pid).limit(1).execute()
    return r.data[0] if r.data else None


# ---- checklists ----
def add_checklist(tid: str, titulo: str):
    sb = get_supabase()
    return sb.table("tarefa_checklists").insert({"tarefa_id": tid, "titulo": titulo}).execute().data[0]


def update_checklist(cid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("tarefa_checklists").update(payload).eq("id", cid).execute()
    return r.data[0] if r.data else None


def delete_checklist(cid: str):
    sb = get_supabase()
    sb.table("tarefa_checklists").delete().eq("id", cid).execute()


# ---- comentários ----
def add_comentario(tid: str, autor_id: str | None, texto: str):
    sb = get_supabase()
    payload = {"tarefa_id": tid, "texto": texto}
    if autor_id:
        payload["autor_id"] = autor_id
    return sb.table("tarefa_comentarios").insert(payload).execute().data[0]


def delete_comentario(mid: str):
    sb = get_supabase()
    sb.table("tarefa_comentarios").delete().eq("id", mid).execute()


# ---- anexos (URL; upload real via Storage entra em Documentos) ----
def add_anexo(tid: str, arquivo_url: str, nome: str | None):
    sb = get_supabase()
    return sb.table("tarefa_anexos").insert({"tarefa_id": tid, "arquivo_url": arquivo_url, "nome": nome}).execute().data[0]


def delete_anexo(aid: str):
    sb = get_supabase()
    sb.table("tarefa_anexos").delete().eq("id", aid).execute()
