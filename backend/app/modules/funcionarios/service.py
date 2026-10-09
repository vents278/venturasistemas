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
    if d.get("admissao") is not None:
        d["admissao"] = str(d["admissao"])
    if d.get("desligamento") is not None:
        d["desligamento"] = str(d["desligamento"])
    return d


def _gerar_matricula() -> str:
    import random

    for _ in range(5):
        cand = f"M{random.randint(100000, 999999)}"
        if not repo.exists_matricula(cand):
            return cand
    raise ValueError("Não foi possível gerar matrícula única")


def listar(q=None, ativo=None, setor=None, area=None, jornada_id=None, page=1, limit=20):
    return repo.list_repo(q, ativo, setor, area, jornada_id, page, limit)


def detalhar(func_id: str) -> dict:
    row = repo.get_repo(func_id)
    if not row:
        raise KeyError("Funcionário não encontrado")
    return row


def criar(body, usuario_id: str | None = None) -> dict:
    validar_datas(body.admissao, body.desligamento)
    payload = _payload(body)
    from datetime import date as _date

    payload.setdefault("admissao", str(_date.today()))
    if not payload.get("matricula"):
        payload["matricula"] = _gerar_matricula()
    if payload.get("supervisor_id") == "":
        payload.pop("supervisor_id", None)
    try:
        depois = repo.create_repo(payload)
    except Exception as exc:
        msg = str(exc).lower()
        if "duplicate" in msg or "unique" in msg:
            raise ValueError("Matrícula já cadastrada")
        raise
    audit(usuario_id, "funcionarios", depois.get("id"), "criar", None, depois)
    return depois


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
    if patch.get("ativo") is True:
        patch["em_treinamento"] = False  # ativou → sai do treinamento automático
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
