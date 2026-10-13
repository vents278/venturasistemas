"""Rotas auth — ETAPA 4."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.schemas import LoginIn, LoginOut, TrocarSenhaIn, UsuarioOut

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


@router.post("/trocar-senha")
def trocar_senha(body: TrocarSenhaIn, user: dict = Depends(get_current_user)):
    try:
        service.trocar_senha(user["id"], user["email"], body.senha_atual, body.nova_senha)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"mensagem": "Senha alterada com sucesso"}
