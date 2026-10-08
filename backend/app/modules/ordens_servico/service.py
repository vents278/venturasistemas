"""Regras OS — ETAPA 8."""

from app.core.supabase_client import get_supabase
from app.modules.ordens_servico import repository as repo
from app.modules.ordens_servico.schemas import STATUS_OS
from app.shared.auditoria import audit


def _responsavel_existe(responsavel_id: str | None) -> None:
    if not responsavel_id:
        return
    sb = get_supabase()
    r = sb.table("funcionarios").select("id").eq("id", responsavel_id).limit(1).execute()
    if not r.data:
        raise ValueError("Responsável não encontrado")


def listar(q=None, status=None):
    return repo.list_repo(q, status.upper() if status else None)


def detalhar(os_id: str) -> dict:
    row = repo.get_repo(os_id)
    if not row:
        raise KeyError("OS não encontrada")
    return row


def criar(body) -> dict:
    _responsavel_existe(str(body.responsavel_id) if body.responsavel_id else None)
    payload = body.model_dump(exclude_unset=True)
    if payload.get("responsavel_id"):
        payload["responsavel_id"] = str(payload["responsavel_id"])
    try:
        return repo.create_repo(payload)
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise ValueError("Código de OS já existe")
        raise


def atualizar(os_id: str, body, usuario_id: str | None = None) -> dict:
    atual = repo.get_repo(os_id)
    if not atual:
        raise KeyError("OS não encontrada")
    patch = body.model_dump(exclude_unset=True)
    if patch.get("status") and patch["status"].upper() not in STATUS_OS:
        raise ValueError("Status inválido")
    if patch.get("status"):
        patch["status"] = patch["status"].upper()
    if patch.get("responsavel_id"):
        _responsavel_existe(str(patch["responsavel_id"]))
        patch["responsavel_id"] = str(patch["responsavel_id"])
    depois = repo.update_repo(os_id, patch)
    audit(usuario_id, "ordens_servico", os_id, "atualizar", atual, depois)
    return depois


def excluir(os_id: str, usuario_id: str | None = None) -> None:
    atual = repo.get_repo(os_id)
    if not atual:
        raise KeyError("OS não encontrada")
    if repo.count_uso(os_id) > 0:
        raise ValueError("OS possui apropriações")
    repo.delete_repo(os_id)
    audit(usuario_id, "ordens_servico", os_id, "excluir", atual, None)
