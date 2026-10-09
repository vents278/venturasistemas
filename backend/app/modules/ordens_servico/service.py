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


def detalhe_completo(os_id: str, de: str | None = None, ate: str | None = None) -> dict:
    """OS + datas de execução + funcionários (cargo) + HH normal/extra/total."""
    from app.modules.apropriacoes import repository as ap_repo

    os_row = repo.get_repo(os_id)
    if not os_row:
        raise KeyError("OS não encontrada")
    linhas = ap_repo.por_os(os_id, de, ate)
    funcs: dict = {}
    normais, extras, datas = 0.0, 0.0, set()
    for ln in linhas:
        fn = ln.get("funcionarios") or {}
        fid = ln["funcionario_id"]
        f = funcs.setdefault(fid, {"funcionario_id": fid, "nome": fn.get("nome"),
                                   "matricula": fn.get("matricula"), "cargo": fn.get("cargo"),
                                   "normais": 0.0, "extras": 0.0, "total": 0.0, "dias": set()})
        n, e = float(ln.get("horas_normais") or 0), float(ln.get("horas_extras") or 0)
        f["normais"] = round(f["normais"] + n, 2)
        f["extras"] = round(f["extras"] + e, 2)
        f["total"] = round(f["total"] + n + e, 2)
        f["dias"].add(ln.get("data"))
        normais, extras = round(normais + n, 2), round(extras + e, 2)
        datas.add(ln.get("data"))
    funcionarios = [{**f, "dias": sorted(f["dias"])} for f in funcs.values()]
    return {"os": os_row, "datas_execucao": sorted(datas),
            "qtd_funcionarios": len(funcionarios), "funcionarios": funcionarios,
            "resumo": {"normais": normais, "extras": extras, "total": round(normais + extras, 2)}}


def criar(body) -> dict:
    _responsavel_existe(str(body.responsavel_id) if body.responsavel_id else None)
    payload = body.model_dump(exclude_unset=True)
    if payload.get("responsavel_id"):
        payload["responsavel_id"] = str(payload["responsavel_id"])
    if payload.get("data_execucao"):
        payload["data_execucao"] = str(payload["data_execucao"])
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
    if patch.get("data_execucao"):
        patch["data_execucao"] = str(patch["data_execucao"])
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
