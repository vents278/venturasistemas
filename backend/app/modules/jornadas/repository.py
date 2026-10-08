"""Acesso a jornadas + jornada_horarios — ETAPA 6 (thin, sem regra)."""

from app.core.supabase_client import get_supabase


def list_jornadas(ativo=None, com_horarios=False):
    sb = get_supabase()
    sel = "*, jornada_horarios(*)" if com_horarios else "*"
    q = sb.table("jornadas").select(sel)
    if ativo is not None:
        q = q.eq("ativo", ativo)
    return (q.order("codigo").execute().data) or []


def get_jornada(jid: str, com_horarios=False):
    sb = get_supabase()
    sel = "*, jornada_horarios(*)" if com_horarios else "*"
    r = sb.table("jornadas").select(sel).eq("id", jid).limit(1).execute()
    return r.data[0] if r.data else None


def create_jornada(payload: dict):
    sb = get_supabase()
    return sb.table("jornadas").insert(payload).select().execute().data[0]


def update_jornada(jid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("jornadas").update(payload).eq("id", jid).select().execute()
    return r.data[0] if r.data else None


def count_uso(jid: str) -> int:
    sb = get_supabase()
    r = sb.table("funcionarios").select("id", count="exact").eq("jornada_id", jid).limit(1).execute()
    return r.count or 0


def delete_jornada(jid: str):
    sb = get_supabase()
    sb.table("jornadas").delete().eq("id", jid).execute()


def list_horarios(jid: str):
    sb = get_supabase()
    r = sb.table("jornada_horarios").select("*").eq("jornada_id", jid).order("dia_semana").execute()
    return r.data or []


def create_horario(payload: dict):
    sb = get_supabase()
    return sb.table("jornada_horarios").insert(payload).select().execute().data[0]


def get_horario(hid: str):
    sb = get_supabase()
    r = sb.table("jornada_horarios").select("*").eq("id", hid).limit(1).execute()
    return r.data[0] if r.data else None


def update_horario(hid: str, payload: dict):
    sb = get_supabase()
    r = sb.table("jornada_horarios").update(payload).eq("id", hid).select().execute()
    return r.data[0] if r.data else None


def delete_horario(hid: str):
    sb = get_supabase()
    sb.table("jornada_horarios").delete().eq("id", hid).execute()
