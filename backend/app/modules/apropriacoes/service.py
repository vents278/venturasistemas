"""Regras de apropriação — ETAPA 8. Soma do dia limitada a 24h; saldo previsto x realizado.

Geração de pendência NÃO acontece aqui (ETAPA 9, motor de regras).
"""

from app.modules.apropriacoes import repository as repo
from app.shared.auditoria import audit


def _validar_vinculos(funcionario_id: str, data_str: str, os_id: str) -> None:
    func = repo.get_funcionario(funcionario_id)
    if not func:
        raise KeyError("Funcionário não encontrado")
    if func.get("desligamento") and str(data_str) > str(func["desligamento"]):
        raise ValueError("Data posterior ao desligamento")
    if not func.get("ativo", True):
        raise ValueError("Funcionário inativo")
    if not repo.get_os(os_id):
        raise KeyError("OS não encontrada")


def _checar_teto(funcionario_id: str, data_str: str, horas_novas: float, ignorar_id=None, extra_atual=0.0) -> None:
    total = repo.total_dia(funcionario_id, data_str, ignorar_id) + horas_novas - extra_atual
    if total > 24 + 1e-9:
        raise ValueError(f"Soma do dia {total}h excede 24h")


def listar(data=None, de=None, ate=None, funcionario_id=None, os_id=None):
    return repo.list_repo(data, de, ate, funcionario_id, os_id)


def saldo(funcionario_id: str, data_str: str) -> dict:
    carga = repo.carga_prevista(funcionario_id, data_str)
    total = repo.total_dia(funcionario_id, data_str)
    return {
        "funcionario_id": funcionario_id,
        "data": data_str,
        "carga_prevista": carga,
        "total_apropriado": total,
        "saldo": round(total - carga, 2),
    }


def registrar(body) -> dict:
    fid, data_str, os_id = str(body.funcionario_id), str(body.data), str(body.os_id)
    _validar_vinculos(fid, data_str, os_id)
    _checar_teto(fid, data_str, body.horas)
    return repo.upsert_repo({"funcionario_id": fid, "data": data_str, "os_id": os_id, "horas": body.horas})


def registrar_lote(funcionario_id: str, data_str: str, itens: list) -> dict:
    _validar_vinculos(funcionario_id, data_str, str(itens[0].os_id) if itens else "")
    soma = round(sum(i.horas for i in itens), 2)
    _checar_teto(funcionario_id, data_str, soma)
    for it in itens:
        _validar_vinculos(funcionario_id, data_str, str(it.os_id))
        repo.upsert_repo({"funcionario_id": funcionario_id, "data": data_str, "os_id": str(it.os_id), "horas": it.horas})
    return {**saldo(funcionario_id, data_str), "lancados": len(itens)}


def atualizar(ap_id: str, horas: float, usuario_id: str | None = None) -> dict:
    atual = repo.get_repo(ap_id)
    if not atual:
        raise KeyError("Apropriação não encontrada")
    _checar_teto(atual["funcionario_id"], atual["data"], horas, ignorar_id=ap_id)
    depois = repo.update_repo(ap_id, {"horas": horas})
    audit(usuario_id, "apropriacoes", ap_id, "atualizar", atual, depois)
    return depois


def excluir(ap_id: str, usuario_id: str | None = None) -> None:
    atual = repo.get_repo(ap_id)
    if not atual:
        raise KeyError("Apropriação não encontrada")
    repo.delete_repo(ap_id)
    audit(usuario_id, "apropriacoes", ap_id, "excluir", atual, None)
