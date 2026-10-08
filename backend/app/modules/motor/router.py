"""Rotas do motor — ETAPA 9. POST dry-run (GESTOR); nada é gravado em pendências."""

from fastapi import APIRouter, Depends, HTTPException

from app.engine import motor_regras
from app.modules.auth.dependencies import require_gestor
from app.modules.motor.schemas import AvaliarDiaIn, AvaliarIn

router = APIRouter(prefix="/motor", tags=["motor"])


@router.post("/avaliar")
def avaliar(body: AvaliarIn, _: dict = Depends(require_gestor)):
    try:
        return {"achados": motor_regras.avaliar(body.funcionario_id, body.data)}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/avaliar-dia")
def avaliar_dia(body: AvaliarDiaIn, _: dict = Depends(require_gestor)):
    try:
        return motor_regras.avaliar_dia(body.data)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
