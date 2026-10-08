"""Regras de jornadas — ETAPA 6. Meia-noite e carga validadas aqui, nunca no router."""

from datetime import time

from app.modules.jornadas import repository as repo
from app.shared.auditoria import audit


def atravessa_esperado(inicio: time, fim: time) -> bool:
    return fim <= inicio


def duracao_horas(inicio: time, fim: time) -> float:
    ini = inicio.hour * 60 + inicio.minute
    end = fim.hour * 60 + fim.minute
    mins = (end - ini) if end > ini else (24 * 60 - ini + end)
    return round(mins / 60, 2)


def validar_horario(inicio: time, fim: time, carga: float, atravessa: bool) -> None:
    if inicio == fim:
        raise ValueError("Início igual ao fim")
    if atravessa != atravessa_esperado(inicio, fim):
        raise ValueError("atravessa_meia_noite inconsistente com inicio/fim (fim<=inicio exige true)")
    if carga > duracao_horas(inicio, fim) + 1e-9:
        raise ValueError(f"Carga {carga}h maior que a duração {duracao_horas(inicio, fim)}h")


def _parse_horario_row(row: dict):
    from datetime import time as _t

    def _p(v):
        h, m = str(v).split(":")[:2]
        return _t(int(h), int(m))

    return _p(row["inicio"]), _p(row["fim"]), float(row["carga_horas"]), bool(row["atravessa_meia_noite"])


def listar(ativo=None, com_horarios=False):
    return repo.list_jornadas(ativo, com_horarios)


def detalhar(jid: str, com_horarios=False) -> dict:
    row = repo.get_jornada(jid, com_horarios)
    if not row:
        raise KeyError("Jornada não encontrada")
    return row


def criar(body) -> dict:
    try:
        return repo.create_jornada(body.model_dump(exclude_unset=True))
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise ValueError("Código de jornada já existe")
        raise


def atualizar(jid: str, body, usuario_id: str | None = None) -> dict:
    atual = repo.get_jornada(jid)
    if not atual:
        raise KeyError("Jornada não encontrada")
    depois = repo.update_jornada(jid, body.model_dump(exclude_unset=True))
    audit(usuario_id, "jornadas", jid, "atualizar", atual, depois)
    return depois


def excluir(jid: str, usuario_id: str | None = None) -> None:
    atual = repo.get_jornada(jid)
    if not atual:
        raise KeyError("Jornada não encontrada")
    if repo.count_uso(jid) > 0:
        raise ValueError("Jornada em uso por funcionários")
    repo.delete_jornada(jid)
    audit(usuario_id, "jornadas", jid, "excluir", atual, None)


def criar_horario(jid: str, body) -> dict:
    if not repo.get_jornada(jid):
        raise KeyError("Jornada não encontrada")
    validar_horario(body.inicio, body.fim, body.carga_horas, body.atravessa_meia_noite)
    payload = body.model_dump()
    payload["jornada_id"] = jid
    payload["inicio"] = body.inicio.strftime("%H:%M")
    payload["fim"] = body.fim.strftime("%H:%M")
    try:
        return repo.create_horario(payload)
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise ValueError("Dia da semana já cadastrado nesta jornada")
        raise


def atualizar_horario(hid: str, body, usuario_id: str | None = None) -> dict:
    atual = repo.get_horario(hid)
    if not atual:
        raise KeyError("Horário não encontrado")
    patch = body.model_dump(exclude_unset=True)
    ini, fim, carga, atr = _parse_horario_row(atual)
    ini = body.inicio or ini
    fim = body.fim or fim
    carga = body.carga_horas if body.carga_horas is not None else carga
    atr = body.atravessa_meia_noite if body.atravessa_meia_noite is not None else atr
    validar_horario(ini, fim, carga, atr)
    if "inicio" in patch and hasattr(patch["inicio"], "strftime"):
        patch["inicio"] = patch["inicio"].strftime("%H:%M")
    if "fim" in patch and hasattr(patch["fim"], "strftime"):
        patch["fim"] = patch["fim"].strftime("%H:%M")
    depois = repo.update_horario(hid, patch)
    audit(usuario_id, "jornada_horarios", hid, "atualizar", atual, depois)
    return depois


def excluir_horario(hid: str, usuario_id: str | None = None) -> None:
    atual = repo.get_horario(hid)
    if not atual:
        raise KeyError("Horário não encontrado")
    repo.delete_horario(hid)
    audit(usuario_id, "jornada_horarios", hid, "excluir", atual, None)
