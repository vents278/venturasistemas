"""Rotas tarefas — ETAPA 12. Leitura autenticada; escrita autenticada; excluir exige GESTOR."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.auth.dependencies import get_current_user, require_gestor
from app.modules.tarefas import service
from app.modules.tarefas.schemas import (
    AnexoIn,
    APartirDePendenciaIn,
    ChecklistIn,
    ChecklistUpdate,
    ComentarioIn,
    TarefaIn,
    TarefaUpdate,
)

router = APIRouter(prefix="/tarefas", tags=["tarefas"])


@router.get("")
def listar(
    status: str | None = None,
    responsavel_id: str | None = None,
    prioridade: str | None = None,
    q: str | None = None,
    _: dict = Depends(get_current_user),
):
    try:
        return service.listar(status.upper() if status else None, responsavel_id, prioridade.upper() if prioridade else None, q)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{tid}")
def detalhar(tid: str, _: dict = Depends(get_current_user)):
    try:
        return service.detalhar(tid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("", status_code=201)
def criar(body: TarefaIn, user: dict = Depends(get_current_user)):
    try:
        return service.criar(body, user.get("id"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/a-partir-de-pendencia/{pid}", status_code=201)
def a_partir_de_pendencia(pid: str, body: APartirDePendenciaIn, user: dict = Depends(require_gestor)):
    try:
        return service.a_partir_de_pendencia(pid, body, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{tid}")
def atualizar(tid: str, body: TarefaUpdate, user: dict = Depends(get_current_user)):
    try:
        return service.atualizar(tid, body, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{tid}", status_code=204)
def excluir(tid: str, user: dict = Depends(require_gestor)):
    try:
        service.excluir(tid, user.get("id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{tid}/checklists", status_code=201)
def add_checklist(tid: str, body: ChecklistIn, _: dict = Depends(get_current_user)):
    from app.modules.tarefas import repository as repo

    if not repo.get_repo(tid):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return repo.add_checklist(tid, body.titulo.strip())


@router.patch("/checklists/{cid}")
def upd_checklist(cid: str, body: ChecklistUpdate, _: dict = Depends(get_current_user)):
    from app.modules.tarefas import repository as repo

    return repo.update_checklist(cid, body.model_dump(exclude_unset=True))


@router.delete("/checklists/{cid}", status_code=204)
def del_checklist(cid: str, _: dict = Depends(get_current_user)):
    from app.modules.tarefas import repository as repo

    repo.delete_checklist(cid)


@router.post("/{tid}/comentarios", status_code=201)
def add_comentario(tid: str, body: ComentarioIn, user: dict = Depends(get_current_user)):
    from app.modules.tarefas import repository as repo

    if not repo.get_repo(tid):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return repo.add_comentario(tid, user.get("id"), body.texto.strip())


@router.delete("/comentarios/{mid}", status_code=204)
def del_comentario(mid: str, _: dict = Depends(require_gestor)):
    from app.modules.tarefas import repository as repo

    repo.delete_comentario(mid)


@router.post("/{tid}/anexos", status_code=201)
def add_anexo(tid: str, body: AnexoIn, _: dict = Depends(get_current_user)):
    from app.modules.tarefas import repository as repo

    if not repo.get_repo(tid):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return repo.add_anexo(tid, body.arquivo_url.strip(), body.nome)


@router.delete("/anexos/{aid}", status_code=204)
def del_anexo(aid: str, _: dict = Depends(require_gestor)):
    from app.modules.tarefas import repository as repo

    repo.delete_anexo(aid)
