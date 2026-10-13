"""Regras de gestão de usuários — todo o módulo exige ADMIN (ver main.py)."""

from app.core.supabase_client import get_supabase
from app.shared.acesso import MODULOS


def listar() -> list:
    sb = get_supabase()
    users = (sb.table("usuarios").select("id,nome,email,ativo,perfis_usuario(nome)").order("nome").execute().data) or []
    out = []
    for u in users:
        emp = (sb.table("usuario_empresas").select("empresa_id").eq("usuario_id", u["id"]).execute().data) or []
        mod = (sb.table("usuario_modulos").select("modulo").eq("usuario_id", u["id"]).execute().data) or []
        out.append({**u, "perfil": (u.get("perfis_usuario") or {}).get("nome"),
                    "empresas": [e["empresa_id"] for e in emp], "modulos": [m["modulo"] for m in mod]})
    return out


def criar(body) -> dict:
    from app.modules.auth.service import _anon_client

    if body.perfil not in ("ADMIN", "GESTOR", "OPERADOR"):
        raise ValueError("Perfil inválido")
    mods = [m for m in (body.modulos or []) if m in MODULOS]
    sb = get_supabase()
    try:
        created = sb.auth.admin.create_user({
            "email": str(body.email), "password": body.senha,
            "email_confirm": True, "user_metadata": {"nome": body.nome.strip()},
        })
    except Exception as exc:
        raise ValueError(f"Auth recusou o cadastro: {exc}")
    if not created.user:
        raise ValueError("Auth não retornou usuário")
    uid = str(created.user.id)
    perfil = sb.table("perfis_usuario").select("id").eq("nome", body.perfil).limit(1).execute()
    sb.table("usuarios").upsert(
        {"id": uid, "email": str(body.email), "nome": body.nome.strip(), "perfil_id": perfil.data[0]["id"]},
        on_conflict="id").execute()
    _trocar_acessos(uid, [str(e) for e in (body.empresas or [])], mods)
    return {"id": uid, "email": str(body.email), "nome": body.nome, "perfil": body.perfil}


def _trocar_acessos(uid: str, empresas: list, modulos: list) -> None:
    sb = get_supabase()
    sb.table("usuario_empresas").delete().eq("usuario_id", uid).execute()
    sb.table("usuario_modulos").delete().eq("usuario_id", uid).execute()
    if empresas:
        sb.table("usuario_empresas").insert([{"usuario_id": uid, "empresa_id": e} for e in empresas]).execute()
    if modulos:
        sb.table("usuario_modulos").insert([{"usuario_id": uid, "modulo": m} for m in modulos]).execute()


def atualizar_acessos(uid: str, body, solicitante_id: str) -> dict:
    if uid == solicitante_id and body.perfil:
        raise ValueError("Não é permitido alterar o próprio perfil")
    sb = get_supabase()
    if not sb.table("usuarios").select("id").eq("id", uid).limit(1).execute().data:
        raise KeyError("Usuário não encontrado")
    if body.perfil:
        if body.perfil not in ("ADMIN", "GESTOR", "OPERADOR"):
            raise ValueError("Perfil inválido")
        perfil = sb.table("perfis_usuario").select("id").eq("nome", body.perfil).limit(1).execute()
        sb.table("usuarios").update({"perfil_id": perfil.data[0]["id"]}).eq("id", uid).execute()
    if body.empresas is not None or body.modulos is not None:
        atual_emp = [e["empresa_id"] for e in (sb.table("usuario_empresas").select("empresa_id").eq("usuario_id", uid).execute().data or [])]
        atual_mod = [m["modulo"] for m in (sb.table("usuario_modulos").select("modulo").eq("usuario_id", uid).execute().data or [])]
        _trocar_acessos(uid,
                        [str(e) for e in body.empresas] if body.empresas is not None else atual_emp,
                        [m for m in (body.modulos or []) if m in MODULOS] if body.modulos is not None else atual_mod)
    return {"id": uid, "ok": True}


def excluir(uid: str, solicitante_id: str) -> None:
    if uid == solicitante_id:
        raise ValueError("Você não pode excluir sua própria conta")
    sb = get_supabase()
    sb.auth.admin.delete_user(uid)
    sb.table("usuarios").delete().eq("id", uid).execute()
