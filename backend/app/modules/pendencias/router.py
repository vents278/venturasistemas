"""Rotas pendências — ETAPA 11. Transformar-em-tarefa chega na ETAPA 12."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user, require_gestor
from app.modules.pendencias import service
from app.modules.pendencias.schemas import SincronizarDiaIn

router = APIRouter(prefix="/pendencias", tags=["pendencias"])


@router.get("")
def listar(
    status: str | None = None,
    tipo: str | None = None,
    funcionario_id: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    _: dict = Depends(get_current_user),
):
    try:
        return service.listar(status, tipo, funcionario_id, de, ate)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{pid}")
def detalhar(pid: str, _: dict = Depends(get_current_user)):
    from app.modules.pendencias import repository as repo

    row = repo.get_repo(pid)
    if not row:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    return row


@router.post("/sincronizar-dia")
def sincronizar_dia(body: SincronizarDiaIn, _: dict = Depends(require_gestor)):
    try:
        return service.sincronizar_dia(body.data)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{pid}/resolver")
def resolver(pid: str, user: dict = Depends(require_gestor)):
    try:
        return service.resolver(pid, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{pid}/cancelar")
def cancelar(pid: str, user: dict = Depends(require_gestor)):
    try:
        return service.cancelar(pid, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
