"""Dependências de autenticação/autorização — ETAPA 4."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import decode_token

bearer = HTTPBearer(auto_error=True)


def _sem_supabase_configurado() -> bool:
    return not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY


def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    payload = decode_token(cred.credentials)
    user_id = payload.get("sub", "")
    email = payload.get("email", "")
    if _sem_supabase_configurado():
        # Modo teste/dev sem Supabase: retorna payload sem buscar vínculo.
        return {"id": user_id, "email": email, "nome": None, "perfil": None, "ativo": True}
    from app.modules.auth.service import buscar_usuario

    vinc = buscar_usuario(user_id)
    if vinc is None:
        return {"id": user_id, "email": email, "nome": None, "perfil": None, "ativo": True}
    if not vinc.get("ativo", True):
        raise HTTPException(status_code=403, detail="Usuário inativo")
    return vinc


def require_perfil(*perfis: str):
    def _check(user: dict = Depends(get_current_user)) -> dict:
        if user.get("perfil") not in perfis:
            raise HTTPException(status_code=403, detail="Sem permissão")
        return user

    return _check


require_admin = require_perfil("ADMIN")
require_gestor = require_perfil("ADMIN", "GESTOR")
