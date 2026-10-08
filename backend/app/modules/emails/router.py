"""Rotas e-mails — ETAPA 13."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user, require_gestor
from app.modules.emails import service
from app.modules.emails.schemas import EnviarIn, GarantirDiaIn

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("")
def listar(status: str | None = None, de: str | None = None, ate: str | None = None, _: dict = Depends(get_current_user)):
    try:
        return service.listar(status, de, ate)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{eid}")
def detalhar(eid: str, _: dict = Depends(get_current_user)):
    from app.modules.emails import repository as repo

    row = repo.get_repo(eid)
    if not row:
        raise HTTPException(status_code=404, detail="E-mail não encontrado")
    return row


@router.post("/garantir-dia")
def garantir_dia(body: GarantirDiaIn, _: dict = Depends(require_gestor)):
    try:
        return service.garantir_dia(body.data)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{eid}/enviar")
def enviar(eid: str, body: EnviarIn, user: dict = Depends(require_gestor)):
    try:
        return service.enviar(eid, body.destinatario, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
