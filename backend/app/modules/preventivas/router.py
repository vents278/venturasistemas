"""Rotas preventivas — programação, checklist de presença e controle de OS."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import empresa_ctx, get_current_user, require_gestor
from app.modules.preventivas import service
from app.modules.preventivas.schemas import (
    FuncionarioProgramadoIn,
    FuncionarioProgramadoUpdate,
    PreventivaIn,
    PreventivaOSIn,
    PreventivaOSUpdate,
    PreventivaUpdate,
)

router = APIRouter(prefix="/preventivas", tags=["preventivas"])


def _handle(exc: Exception):
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, RuntimeError):
        raise HTTPException(status_code=500, detail=str(exc))
    raise exc


@router.get("/indicadores")
def indicadores(
    data: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    area: str | None = None,
    status: str | None = None,
    funcionario_id: str | None = None,
    funcionario: str | None = None,
    cargo: str | None = None,
    os_codigo: str | None = None,
    situacao: str | None = None,
    _: dict = Depends(get_current_user),
    empresa: str | None = Depends(empresa_ctx),
):
    try:
        return service.indicadores(
            data=data, de=de, ate=ate, area=area, status=status,
            funcionario_id=funcionario_id, funcionario=funcionario, cargo=cargo,
            os_codigo=os_codigo, situacao=situacao, empresa_id=empresa)
    except RuntimeError as exc:
        _handle(exc)


@router.get("")
def listar(
    data: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    area: str | None = None,
    status: str | None = None,
    funcionario_id: str | None = None,
    funcionario: str | None = None,
    cargo: str | None = None,
    os_codigo: str | None = None,
    situacao: str | None = None,
    _: dict = Depends(get_current_user),
    empresa: str | None = Depends(empresa_ctx),
):
    try:
        return service.listar(
            data=data, de=de, ate=ate, area=area, status=status,
            funcionario_id=funcionario_id, funcionario=funcionario, cargo=cargo,
            os_codigo=os_codigo, situacao=situacao, empresa_id=empresa)
    except RuntimeError as exc:
        _handle(exc)


@router.get("/{pid}")
def detalhar(pid: str, _: dict = Depends(get_current_user)):
    try:
        return service.montar_detalhe(pid)
    except KeyError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.post("", status_code=201)
def criar(body: PreventivaIn, user: dict = Depends(require_gestor),
          empresa: str | None = Depends(empresa_ctx)):
    try:
        return service.criar(body, user.get("id"), empresa)
    except KeyError as exc:
        _handle(exc)
    except ValueError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.patch("/{pid}")
def atualizar(pid: str, body: PreventivaUpdate, user: dict = Depends(require_gestor)):
    try:
        return service.atualizar(pid, body, user.get("id"))
    except KeyError as exc:
        _handle(exc)
    except ValueError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.delete("/{pid}", status_code=204)
def excluir(pid: str, user: dict = Depends(require_gestor)):
    try:
        service.excluir(pid, user.get("id"))
    except KeyError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.post("/{pid}/funcionarios", status_code=201)
def adicionar_funcionario(pid: str, body: FuncionarioProgramadoIn,
                          user: dict = Depends(require_gestor)):
    try:
        return service.adicionar_funcionario(pid, body, user.get("id"))
    except KeyError as exc:
        _handle(exc)
    except ValueError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.patch("/{pid}/funcionarios/{pf_id}")
def atualizar_funcionario(pid: str, pf_id: str, body: FuncionarioProgramadoUpdate,
                          user: dict = Depends(require_gestor)):
    try:
        return service.atualizar_funcionario(pid, pf_id, body, user.get("id"))
    except KeyError as exc:
        _handle(exc)
    except ValueError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.delete("/{pid}/funcionarios/{pf_id}")
def remover_funcionario(pid: str, pf_id: str, user: dict = Depends(require_gestor)):
    try:
        return service.remover_funcionario(pid, pf_id, user.get("id"))
    except KeyError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.post("/{pid}/funcionarios/{pf_id}/os", status_code=201)
def adicionar_os(pid: str, pf_id: str, body: PreventivaOSIn,
                 user: dict = Depends(require_gestor)):
    try:
        return service.adicionar_os(pid, pf_id, body, user.get("id"))
    except KeyError as exc:
        _handle(exc)
    except ValueError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.patch("/{pid}/funcionarios/{pf_id}/os/{osrow_id}")
def atualizar_os(pid: str, pf_id: str, osrow_id: str, body: PreventivaOSUpdate,
                 user: dict = Depends(require_gestor)):
    try:
        return service.atualizar_os(pid, pf_id, osrow_id, body, user.get("id"))
    except KeyError as exc:
        _handle(exc)
    except ValueError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.delete("/{pid}/funcionarios/{pf_id}/os/{osrow_id}")
def remover_os(pid: str, pf_id: str, osrow_id: str, user: dict = Depends(require_gestor)):
    try:
        return service.remover_os(pid, pf_id, osrow_id, user.get("id"))
    except KeyError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)


@router.post("/{pid}/sincronizar-pendencias")
def sincronizar_pendencias(pid: str, _: dict = Depends(require_gestor)):
    try:
        return service.sincronizar_pendencias(pid)
    except KeyError as exc:
        _handle(exc)
    except RuntimeError as exc:
        _handle(exc)
