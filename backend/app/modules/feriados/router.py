"""Rotas feriados — ETAPA 10."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user, require_gestor
from app.modules.feriados import service
from app.modules.feriados.schemas import FeriadoIn

router = APIRouter(prefix="/feriados", tags=["feriados"])


@router.get("")
def listar(ano: int | None = None, _: dict = Depends(get_current_user)):
    try:
        return service.listar(ano)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", status_code=201)
def criar(body: FeriadoIn, _: dict = Depends(require_gestor)):
    try:
        return service.criar(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{data}", status_code=204)
def excluir(data: str, _: dict = Depends(require_gestor)):
    try:
        service.excluir(data)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
