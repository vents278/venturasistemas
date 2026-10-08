"""Regras de auth — ETAPA 4.

Login via Supabase Auth (anon key). Vínculo com public.usuarios via service key.
Sem .env configurado: lança RuntimeError com mensagem clara (não inventa sessão).
"""

from supabase import create_client

from app.core.config import settings


def _anon_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise RuntimeError("Configure SUPABASE_URL e SUPABASE_ANON_KEY no .env")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def login_supabase(email: str, senha: str) -> dict:
    sb = _anon_client()
    res = sb.auth.sign_in_with_password({"email": email, "password": senha})
    if not res.session:
        raise ValueError("Login inválido")
    return {
        "access_token": res.session.access_token,
        "user_id": str(res.user.id),
        "email": res.user.email,
    }


def buscar_usuario(user_id: str) -> dict | None:
    """Busca vínculo em public.usuarios (com perfil). None se ainda sem vínculo."""
    from app.core.supabase_client import get_supabase

    sb = get_supabase()
    r = (
        sb.table("usuarios")
        .select("id,nome,email,ativo,perfis_usuario(nome)")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not r.data:
        return None
    row = r.data[0]
    perfil = row.get("perfis_usuario")
    return {
        "id": row["id"],
        "nome": row.get("nome"),
        "email": row.get("email"),
        "ativo": row.get("ativo", True),
        "perfil": perfil.get("nome") if isinstance(perfil, dict) else None,
    }


def vincular_usuario(user_id: str, email: str, nome: str | None = None) -> dict:
    """Cria linha em public.usuarios para um id do Auth (default OPERADOR). Idempotente."""
    from app.core.supabase_client import get_supabase

    sb = get_supabase()
    existente = buscar_usuario(user_id)
    if existente:
        return existente
    perfil = sb.table("perfis_usuario").select("id").eq("nome", "OPERADOR").limit(1).execute()
    perfil_id = perfil.data[0]["id"] if perfil.data else 3
    sb.table("usuarios").upsert(
        {"id": user_id, "email": email, "nome": nome or email, "perfil_id": perfil_id},
        on_conflict="id",
    ).execute()
    return buscar_usuario(user_id) or {"id": user_id, "email": email, "perfil": "OPERADOR", "ativo": True}
