"""Rotas presença — ETAPA 7. /status-presenca antes de /{id} (ordem importa)."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user, require_gestor
from app.modules.presencas import service
from app.modules.presencas.schemas import LoteIn, PresencaIn, PresencaUpdate

router = APIRouter(prefix="/presencas", tags=["presencas"])


@router.get("/status-presenca")
def status_presenca(_: dict = Depends(get_current_user)):
    try:
        from app.modules.presencas import repository as repo

        return repo.list_status()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/grade")
def grade(de: str, ate: str, setor: str | None = None, _: dict = Depends(get_current_user)):
    try:
        return service.montar_grade(de, ate, setor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("")
def listar(
    data: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    funcionario_id: str | None = None,
    status: str | None = None,
    _: dict = Depends(get_current_user),
):
    try:
        return service.listar(data, de, ate, funcionario_id, status.upper() if status else None)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{pid}")
def detalhar(pid: str, _: dict = Depends(get_current_user)):
    from app.modules.presencas import repository as repo

    row = repo.get_repo(pid)
    if not row:
        raise HTTPException(status_code=404, detail="Presença não encontrada")
    return row


@router.post("", status_code=201)
def registrar(body: PresencaIn, _: dict = Depends(require_gestor)):
    try:
        return service.registrar(body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/lote", status_code=201)
def registrar_lote(body: LoteIn, _: dict = Depends(require_gestor)):
    return service.registrar_lote(str(body.data), body.itens)


@router.patch("/{pid}")
def atualizar(pid: str, body: PresencaUpdate, user: dict = Depends(require_gestor)):
    try:
        return service.atualizar(pid, body, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{pid}", status_code=204)
def excluir(pid: str, user: dict = Depends(require_gestor)):
    try:
        service.excluir(pid, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
