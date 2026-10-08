"""Rotas absenteísmo — ETAPA 14. /tipos e /indicadores antes de /{id}."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.absenteismo import service
from app.modules.absenteismo.schemas import AbsenteismoIn, AbsenteismoUpdate, TipoIn
from app.modules.auth.dependencies import get_current_user, require_gestor

router = APIRouter(prefix="/absenteismo", tags=["absenteismo"])


@router.get("/tipos")
def tipos(_: dict = Depends(get_current_user)):
    from app.modules.absenteismo import repository as repo

    try:
        return repo.list_tipos()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/tipos", status_code=201)
def criar_tipo(body: TipoIn, _: dict = Depends(require_gestor)):
    from app.modules.absenteismo import repository as repo

    try:
        return repo.create_tipo({"codigo": body.codigo.strip().upper(), "descricao": body.descricao.strip()})
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(status_code=400, detail="Código já existe")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/tipos/{tid}", status_code=204)
def excluir_tipo(tid: int, _: dict = Depends(require_gestor)):
    from app.modules.absenteismo import repository as repo

    if repo.count_uso_tipo(tid) > 0:
        raise HTTPException(status_code=400, detail="Tipo em uso")
    repo.delete_tipo(tid)


@router.get("/indicadores")
def indicadores(de: str | None = None, ate: str | None = None, setor: str | None = None, _: dict = Depends(get_current_user)):
    try:
        return service.indicadores(de, ate, setor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("")
def listar(
    de: str | None = None, ate: str | None = None, funcionario_id: str | None = None,
    tipo_id: int | None = None, setor: str | None = None, _: dict = Depends(get_current_user),
):
    try:
        return service.listar(de, ate, funcionario_id, tipo_id, setor)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{aid}")
def detalhar(aid: str, _: dict = Depends(get_current_user)):
    from app.modules.absenteismo import repository as repo

    row = repo.get_repo(aid)
    if not row:
        raise HTTPException(status_code=404, detail="Ausência não encontrada")
    return row


@router.post("", status_code=201)
def criar(body: AbsenteismoIn, _: dict = Depends(require_gestor)):
    try:
        return service.criar(body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{aid}")
def atualizar(aid: str, body: AbsenteismoUpdate, user: dict = Depends(require_gestor)):
    try:
        return service.atualizar(aid, body, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{aid}", status_code=204)
def excluir(aid: str, user: dict = Depends(require_gestor)):
    try:
        service.excluir(aid, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
