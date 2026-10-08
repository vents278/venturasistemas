"""Rotas horas extras — ETAPA 10."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user, require_gestor
from app.modules.horas_extras import service
from app.modules.horas_extras.schemas import RecalcularDiaIn, RecalcularIn

router = APIRouter(prefix="/horas-extras", tags=["horas-extras"])


@router.get("")
def listar(
    data: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    funcionario_id: str | None = None,
    percentual: int | None = None,
    _: dict = Depends(get_current_user),
):
    try:
        return service.listar(data, de, ate, funcionario_id, percentual)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recalcular")
def recalcular(body: RecalcularIn, _: dict = Depends(require_gestor)):
    try:
        r = service.recalcular(body.funcionario_id, str(body.data))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return r or {"funcionario_id": body.funcionario_id, "data": str(body.data), "horas_extras": None}


@router.post("/recalcular-dia")
def recalcular_dia(body: RecalcularDiaIn, _: dict = Depends(require_gestor)):
    try:
        return service.recalcular_dia(str(body.data))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
