"""Rota dashboard — ETAPA 15. Leitura para autenticado."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user
from app.modules.dashboard import service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/resumo")
def resumo(data: str | None = None, _: dict = Depends(get_current_user)):
    try:
        return service.resumo(data)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
