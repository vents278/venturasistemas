"""Rotas apropriação — ETAPA 8. /saldo e /lote antes de /{id}."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.apropriacoes import service
from app.modules.apropriacoes.schemas import ApropriacaoIn, ApropriacaoLoteIn, ApropriacaoLoteOSIn, ApropriacaoUpdate
from app.modules.auth.dependencies import get_current_user, require_gestor

router = APIRouter(prefix="/apropriacoes", tags=["apropriacoes"])


@router.get("/saldo")
def saldo(funcionario_id: str, data: str, _: dict = Depends(get_current_user)):
    try:
        return service.saldo(funcionario_id, data)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("")
def listar(
    data: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    funcionario_id: str | None = None,
    os_id: str | None = None,
    _: dict = Depends(get_current_user),
):
    try:
        return service.listar(data, de, ate, funcionario_id, os_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{ap_id}")
def detalhar(ap_id: str, _: dict = Depends(get_current_user)):
    from app.modules.apropriacoes import repository as repo

    row = repo.get_repo(ap_id)
    if not row:
        raise HTTPException(status_code=404, detail="Apropriação não encontrada")
    return row


@router.post("", status_code=201)
def registrar(body: ApropriacaoIn, _: dict = Depends(require_gestor)):
    try:
        return service.registrar(body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/lote", status_code=201)
def registrar_lote(body: ApropriacaoLoteIn, _: dict = Depends(require_gestor)):
    try:
        return service.registrar_lote(str(body.funcionario_id), str(body.data), body.itens)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/lote-os", status_code=201)
def registrar_lote_os(body: ApropriacaoLoteOSIn, _: dict = Depends(require_gestor)):
    try:
        return service.registrar_lote_os(str(body.data), str(body.os_id), body.itens)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{ap_id}")
def atualizar(ap_id: str, body: ApropriacaoUpdate, user: dict = Depends(require_gestor)):
    try:
        return service.atualizar(ap_id, body.horas, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{ap_id}", status_code=204)
def excluir(ap_id: str, user: dict = Depends(require_gestor)):
    try:
        service.excluir(ap_id, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
