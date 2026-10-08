"""Regras feriados — ETAPA 10."""

from app.modules.feriados import repository as repo
from app.modules.feriados.schemas import TIPOS


def listar(ano=None):
    return repo.list_repo(ano)


def criar(body) -> dict:
    tipo = (body.tipo or "NACIONAL").upper()
    if tipo not in TIPOS:
        raise ValueError("Tipo inválido")
    payload = {"data": str(body.data), "descricao": body.descricao.strip(), "tipo": tipo}
    try:
        return repo.create_repo(payload)
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise ValueError("Feriado já cadastrado")
        raise


def excluir(data_str: str) -> None:
    if not repo.get_repo(data_str):
        raise KeyError("Feriado não encontrado")
    repo.delete_repo(data_str)
