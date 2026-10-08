"""Rotas auth — ETAPA 4."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.schemas import LoginIn, LoginOut, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn) -> LoginOut:
    try:
        sess = service.login_supabase(body.email, body.senha)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    vinc = service.buscar_usuario(sess["user_id"])
    usuario = vinc or {"id": sess["user_id"], "email": sess["email"], "perfil": None, "ativo": True}
    return LoginOut(access_token=sess["access_token"], usuario=UsuarioOut(**usuario))


@router.get("/me", response_model=UsuarioOut)
def me(user: dict = Depends(get_current_user)) -> UsuarioOut:
    return UsuarioOut(**user)


@router.post("/vincular", response_model=UsuarioOut, dependencies=[Depends(require_admin)])
def vincular(user_id: str, email: str, nome: str | None = None) -> UsuarioOut:
    return UsuarioOut(**service.vincular_usuario(user_id, email, nome))
