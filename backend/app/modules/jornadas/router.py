"""Rotas jornadas + horários — ETAPA 6."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user, require_admin, require_gestor
from app.modules.jornadas import service
from app.modules.jornadas.schemas import HorarioIn, HorarioUpdate, JornadaIn, JornadaUpdate

router = APIRouter(prefix="/jornadas", tags=["jornadas"])


@router.get("")
def listar(ativo: bool | None = None, com_horarios: bool = False, _: dict = Depends(get_current_user)):
    try:
        return service.listar(ativo, com_horarios)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{jid}")
def detalhar(jid: str, com_horarios: bool = False, _: dict = Depends(get_current_user)):
    try:
        return service.detalhar(jid, com_horarios)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", status_code=201)
def criar(body: JornadaIn, _: dict = Depends(require_gestor)):
    try:
        return service.criar(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{jid}")
def atualizar(jid: str, body: JornadaUpdate, user: dict = Depends(require_gestor)):
    try:
        return service.atualizar(jid, body, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{jid}", status_code=204)
def excluir(jid: str, user: dict = Depends(require_admin)):
    try:
        service.excluir(jid, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{jid}/horarios")
def listar_horarios(jid: str, _: dict = Depends(get_current_user)):
    try:
        service.detalhar(jid)
        from app.modules.jornadas import repository as repo

        return repo.list_horarios(jid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{jid}/horarios", status_code=201)
def criar_horario(jid: str, body: HorarioIn, _: dict = Depends(require_gestor)):
    try:
        return service.criar_horario(jid, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/horarios/{hid}")
def atualizar_horario(hid: str, body: HorarioUpdate, user: dict = Depends(require_gestor)):
    try:
        return service.atualizar_horario(hid, body, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/horarios/{hid}", status_code=204)
def excluir_horario(hid: str, user: dict = Depends(require_gestor)):
    try:
        service.excluir_horario(hid, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
