"""Regras de tarefas — ETAPA 12. Conclusão carimba conclusao_em; reabrir limpa."""

from datetime import datetime, timezone

from app.modules.tarefas import repository as repo
from app.modules.tarefas.schemas import PRIORIDADES, STATUS
from app.shared.auditoria import audit


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def listar(status=None, responsavel_id=None, prioridade=None, q=None):
    return repo.list_repo(status, responsavel_id, prioridade, q)


def detalhar(tid: str) -> dict:
    row = repo.detalhar_repo(tid)
    if not row:
        raise KeyError("Tarefa não encontrada")
    return row


def criar(body, criador_id: str | None) -> dict:
    status = (body.status or "A_FAZER").upper()
    prioridade = (body.prioridade or "MEDIA").upper()
    if status not in STATUS:
        raise ValueError("Status inválido")
    if prioridade not in PRIORIDADES:
        raise ValueError("Prioridade inválida")
    payload = {
        "titulo": body.titulo.strip(),
        "descricao": body.descricao,
        "status": status,
        "prioridade": prioridade,
        "responsavel_id": str(body.responsavel_id) if body.responsavel_id else None,
        "prazo": str(body.prazo) if body.prazo else None,
        "categoria": body.categoria,
        "criador_id": criador_id,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    if status == "CONCLUIDO":
        payload["conclusao_em"] = _agora()
    try:
        return repo.create_repo(payload)
    except Exception as exc:
        msg = str(exc).lower()
        if "foreign key" in msg or "violates" in msg:
            raise ValueError("Responsável/criador sem vínculo — confira funcionário e /auth/vincular")
        raise


def atualizar(tid: str, body, usuario_id: str | None = None) -> dict:
    atual = repo.get_repo(tid)
    if not atual:
        raise KeyError("Tarefa não encontrada")
    patch = body.model_dump(exclude_unset=True)
    if patch.get("status"):
        patch["status"] = patch["status"].upper()
        if patch["status"] not in STATUS:
            raise ValueError("Status inválido")
        patch["conclusao_em"] = _agora() if patch["status"] == "CONCLUIDO" else None
    if patch.get("prioridade"):
        patch["prioridade"] = patch["prioridade"].upper()
        if patch["prioridade"] not in PRIORIDADES:
            raise ValueError("Prioridade inválida")
    if patch.get("responsavel_id") is not None:
        patch["responsavel_id"] = str(patch["responsavel_id"])
    if patch.get("prazo") is not None:
        patch["prazo"] = str(patch["prazo"])
    depois = repo.update_repo(tid, patch)
    audit(usuario_id, "tarefas", tid, "atualizar", atual, depois)
    return depois


def excluir(tid: str, usuario_id: str | None = None) -> None:
    atual = repo.get_repo(tid)
    if not atual:
        raise KeyError("Tarefa não encontrada")
    repo.delete_repo(tid)
    audit(usuario_id, "tarefas", tid, "excluir", atual, None)


def a_partir_de_pendencia(pid: str, body, criador_id: str | None) -> dict:
    from app.modules.pendencias import repository as pd_repo

    pend = pd_repo.get_repo(pid)
    if not pend:
        raise KeyError("Pendência não encontrada")
    if repo.find_por_pendencia(pid):
        raise ValueError("Pendência já transformada em tarefa")
    prioridade = (body.prioridade or pend.get("prioridade") or "MEDIA").upper()
    payload = {
        "titulo": (body.titulo or f"Corrigir: {pend['descricao']}")[:200],
        "descricao": f"Origem pendência {pend['tipo']} ref {pend.get('data_ref')}: {pend['descricao']}",
        "status": "A_FAZER",
        "prioridade": prioridade,
        "responsavel_id": str(body.responsavel_id) if body.responsavel_id else pend.get("responsavel_id"),
        "criador_id": criador_id,
        "pendencia_origem_id": pid,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return repo.create_repo(payload)
