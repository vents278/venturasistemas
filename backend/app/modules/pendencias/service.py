"""Regras de pendências — ETAPA 11. Resolver/cancelar é manual; gerar é do motor."""

from datetime import datetime, timezone

from app.engine import motor_pendencias
from app.modules.pendencias import repository as repo
from app.shared.auditoria import audit


def listar(status=None, tipo=None, funcionario_id=None, de=None, ate=None):
    return repo.list_repo(status, tipo, funcionario_id, de, ate)


def sincronizar_dia(data_ref: str) -> dict:
    return motor_pendencias.sincronizar_dia(data_ref)


def resolver(pid: str, usuario_id: str | None = None) -> dict:
    row = repo.get_repo(pid)
    if not row:
        raise KeyError("Pendência não encontrada")
    if row["status"] != "ABERTA":
        raise ValueError("Só pendência ABERTA pode ser resolvida")
    depois = repo.update_repo(pid, {"status": "RESOLVIDA", "resolved_at": datetime.now(timezone.utc).isoformat()})
    audit(usuario_id, "pendencias", pid, "resolver", row, depois)
    return depois


def cancelar(pid: str, usuario_id: str | None = None) -> dict:
    row = repo.get_repo(pid)
    if not row:
        raise KeyError("Pendência não encontrada")
    if row["status"] != "ABERTA":
        raise ValueError("Só pendência ABERTA pode ser cancelada")
    depois = repo.update_repo(pid, {"status": "CANCELADA", "resolved_at": datetime.now(timezone.utc).isoformat()})
    audit(usuario_id, "pendencias", pid, "cancelar", row, depois)
    return depois
