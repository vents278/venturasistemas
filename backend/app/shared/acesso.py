"""Acesso: empresas + módulos por usuário — multi-empresa.

Sem .env/Supabase: acesso total (dev/testes). ADMIN: bypass.
Sem linhas em usuario_* : acesso total (compat); com linhas: restrito.
"""

MODULOS = ["dashboard", "funcionarios", "jornadas", "presencas", "apropriacoes",
           "horas-extras", "pendencias", "tarefas", "emails", "absenteismo",
           "relatorios", "auditoria", "motor", "ai", "empresas", "usuarios"]


def acessos_usuario(sb, user_id: str) -> dict:
    try:
        emp = (sb.table("usuario_empresas").select("empresa_id").eq("usuario_id", user_id).execute().data) or []
        mod = (sb.table("usuario_modulos").select("modulo").eq("usuario_id", user_id).execute().data) or []
        return {"empresas": [e["empresa_id"] for e in emp], "modulos": [m["modulo"] for m in mod]}
    except Exception:
        return {"empresas": [], "modulos": []}


def pode_modulo(user: dict, modulo: str) -> bool:
    if user.get("perfil") == "ADMIN":
        return True
    mods = user.get("modulos") or []
    return True if not mods else modulo in mods


def empresa_no_escopo(user: dict, empresa_id: str | None, func_empresa: str | None = None) -> bool:
    """Valida empresa selecionada e/ou empresa do registro."""
    if user.get("perfil") == "ADMIN":
        return True
    emps = user.get("empresas") or []
    if not emps:
        return True
    if empresa_id and empresa_id not in emps:
        return False
    if func_empresa is not None and func_empresa not in emps:
        return False
    return True
