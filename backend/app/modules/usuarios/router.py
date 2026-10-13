"""Rotas usuários — ADMIN (ver main.py)."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user
from app.modules.usuarios import service
from app.modules.usuarios.schemas import AcessosIn, UsuarioCreateIn

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("")
def listar(_: dict = Depends(get_current_user)):
    try:
        return service.listar()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", status_code=201)
def criar(body: UsuarioCreateIn, _: dict = Depends(get_current_user)):
    try:
        return service.criar(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{uid}/acessos")
def acessos(uid: str, body: AcessosIn, user: dict = Depends(get_current_user)):
    try:
        return service.atualizar_acessos(uid, body, user["id"])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{uid}", status_code=204)
def excluir(uid: str, user: dict = Depends(get_current_user)):
    try:
        service.excluir(uid, user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
