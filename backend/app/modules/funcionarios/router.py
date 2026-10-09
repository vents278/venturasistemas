"""Rotas funcionários — ETAPA 5. Leitura p/ autenticado, escrita p/ GESTOR/ADMIN."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.auth.dependencies import get_current_user, require_gestor
from app.modules.funcionarios import service
from app.modules.funcionarios.schemas import FuncionarioIn, FuncionarioOut, FuncionarioUpdate

router = APIRouter(prefix="/funcionarios", tags=["funcionarios"])


def _to_out(row: dict) -> FuncionarioOut:
    row = dict(row)
    row.pop("jornadas", None)
    for k in ("jornada_id", "supervisor_id", "id"):
        if row.get(k) is not None:
            row[k] = str(row[k])
    if row.get("em_treinamento") is None:
        row["em_treinamento"] = False
    if row.get("ativo") is None:
        row["ativo"] = True
    return FuncionarioOut(**{k: row.get(k) for k in FuncionarioOut.model_fields})


@router.get("")
def listar(
    q: str | None = None,
    ativo: bool | None = None,
    setor: str | None = None,
    area: str | None = None,
    jornada_id: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
):
    try:
        data = service.listar(q, ativo, setor, area, jornada_id, page, limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"items": [_to_out(r) for r in data["items"]], "total": data["total"], "page": page}


@router.get("/{func_id}", response_model=FuncionarioOut)
def detalhar(func_id: str, _: dict = Depends(get_current_user)):
    try:
        return _to_out(service.detalhar(func_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", response_model=FuncionarioOut, status_code=201)
def criar(body: FuncionarioIn, user: dict = Depends(require_gestor)):
    try:
        return _to_out(service.criar(body, user.get("id")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{func_id}", response_model=FuncionarioOut)
def atualizar(func_id: str, body: FuncionarioUpdate, user: dict = Depends(require_gestor)):
    try:
        return _to_out(service.atualizar(func_id, body, user.get("id")))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{func_id}", response_model=FuncionarioOut)
def inativar(func_id: str, user: dict = Depends(require_gestor)):
    """Exclusão lógica: ativo=false (preserva histórico de presença/apropriação)."""
    try:
        return _to_out(service.inativar(func_id, user.get("id")))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
