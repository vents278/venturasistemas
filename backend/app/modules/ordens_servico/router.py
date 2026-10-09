"""Rotas OS — ETAPA 8."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user, require_gestor
from app.modules.ordens_servico import service
from app.modules.ordens_servico.schemas import OSIn, OSUpdate

router = APIRouter(prefix="/os", tags=["ordens-servico"])


@router.get("")
def listar(q: str | None = None, status: str | None = None, _: dict = Depends(get_current_user)):
    try:
        return service.listar(q, status)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{os_id}")
def detalhar(os_id: str, de: str | None = None, ate: str | None = None, _: dict = Depends(get_current_user)):
    try:
        return service.detalhe_completo(os_id, de, ate)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", status_code=201)
def criar(body: OSIn, _: dict = Depends(require_gestor)):
    try:
        return service.criar(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{os_id}")
def atualizar(os_id: str, body: OSUpdate, user: dict = Depends(require_gestor)):
    try:
        return service.atualizar(os_id, body, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{os_id}", status_code=204)
def excluir(os_id: str, user: dict = Depends(require_gestor)):
    try:
        service.excluir(os_id, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
