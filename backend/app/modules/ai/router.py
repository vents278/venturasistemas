"""Rotas IA — ETAPA 18. Autenticado, somente leitura."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.ai import service
from app.modules.ai.schemas import PerguntarIn, ResumoDiaIn
from app.modules.auth.dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["ia"])


@router.post("/resumo-dia")
def resumo_dia(body: ResumoDiaIn, _: dict = Depends(get_current_user)):
    try:
        return service.resumo_dia(body.data)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/perguntar")
def perguntar(body: PerguntarIn, _: dict = Depends(get_current_user)):
    try:
        return service.perguntar(body.pergunta)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
