"""Rotas apropriação — ETAPA 8. /saldo e /lote antes de /{id}."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.apropriacoes import service
from app.modules.apropriacoes.schemas import ApropriacaoIn, ApropriacaoLoteIn, ApropriacaoLoteOSIn, ApropriacaoUpdate
from app.modules.auth.dependencies import get_current_user, require_gestor
from app.shared.acesso import empresa_no_escopo

router = APIRouter(prefix="/apropriacoes", tags=["apropriacoes"])


def _func_ok(user: dict, fid: str) -> None:
    from app.modules.apropriacoes import repository as repo

    func = repo.get_funcionario(fid)
    if func and func.get("empresa_id") and not empresa_no_escopo(user, None, str(func["empresa_id"])):
        raise HTTPException(status_code=403, detail="Sem acesso à empresa do funcionário")


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


@router.get("/consulta")
def consulta(funcionario_id: str, de: str | None = None, ate: str | None = None,
             os_codigo: str | None = None, so_extras: bool = False,
             _: dict = Depends(get_current_user)):
    try:
        return service.consulta_funcionario(funcionario_id, de, ate, os_codigo, so_extras)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
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
def registrar(body: ApropriacaoIn, user: dict = Depends(require_gestor)):
    _func_ok(user, str(body.funcionario_id))
    try:
        return service.registrar(body, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/lote", status_code=201)
def registrar_lote(body: ApropriacaoLoteIn, user: dict = Depends(require_gestor)):
    _func_ok(user, str(body.funcionario_id))
    try:
        return service.registrar_lote(str(body.funcionario_id), str(body.data), body.itens, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/lote-os", status_code=201)
def registrar_lote_os(body: ApropriacaoLoteOSIn, user: dict = Depends(require_gestor)):
    for it in body.itens:
        _func_ok(user, str(it.funcionario_id))
    try:
        return service.registrar_lote_os(str(body.data), str(body.os_id), body.itens, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{ap_id}")
def atualizar(ap_id: str, body: ApropriacaoUpdate, user: dict = Depends(require_gestor)):
    from app.modules.apropriacoes import repository as repo

    atual = repo.get_repo(ap_id)
    if atual:
        _func_ok(user, atual["funcionario_id"])
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
