"""Regras de funcionários — ETAPA 5/17. Router nunca valida; tudo passa aqui."""

from app.modules.funcionarios import repository as repo
from app.shared.auditoria import audit


def validar_datas(admissao, desligamento) -> None:
    if admissao and desligamento and desligamento < admissao:
        raise ValueError("Desligamento anterior à admissão")


def _payload(body) -> dict:
    d = body.model_dump(exclude_unset=True)
    for k in ("jornada_id", "supervisor_id"):
        if d.get(k) is not None:
            d[k] = str(d[k])
    return d


def listar(q=None, ativo=None, setor=None, area=None, jornada_id=None, page=1, limit=20):
    return repo.list_repo(q, ativo, setor, area, jornada_id, page, limit)


def detalhar(func_id: str) -> dict:
    row = repo.get_repo(func_id)
    if not row:
        raise KeyError("Funcionário não encontrado")
    return row


def criar(body) -> dict:
    validar_datas(body.admissao, body.desligamento)
    if body.supervisor_id is not None and str(body.supervisor_id) == "":
        body.supervisor_id = None  # type: ignore
    try:
        return repo.create_repo(_payload(body))
    except Exception as exc:
        msg = str(exc).lower()
        if "duplicate" in msg or "unique" in msg:
            raise ValueError("Matrícula ou CPF já cadastrado")
        raise


def atualizar(func_id: str, body, usuario_id: str | None = None) -> dict:
    atual = repo.get_repo(func_id)
    if not atual:
        raise KeyError("Funcionário não encontrado")
    patch = _payload(body)
    validar_datas(
        body.admissao or atual.get("admissao"),
        body.desligamento if "desligamento" in patch else atual.get("desligamento"),
    )
    if patch.get("supervisor_id") == func_id:
        raise ValueError("Supervisor não pode ser o próprio funcionário")
    depois = repo.update_repo(func_id, patch)
    audit(usuario_id, "funcionarios", func_id, "atualizar", atual, depois)
    return depois


def inativar(func_id: str, usuario_id: str | None = None) -> dict:
    row = repo.get_repo(func_id)
    if not row:
        raise KeyError("Funcionário não encontrado")
    depois = repo.set_ativo_repo(func_id, False)
    audit(usuario_id, "funcionarios", func_id, "inativar", row, depois)
    return depois
