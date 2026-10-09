"""Regras de horas extras — ETAPA 10/13. Recalcular faz upsert (preserva id) + garante e-mail.

Upsert em vez de limpar-antes: mantém o id da HE para o vínculo do e-mail.
"""

import logging
from datetime import date as _date

from app.engine.regras.hora_extra import calcular_he
from app.modules.horas_extras import repository as repo

logger = logging.getLogger(__name__)


def _dow(data_str: str) -> int:
    d = _date.fromisoformat(data_str)
    return (d.weekday() + 1) % 7  # 0=dom..6=sáb (EXTRACT DOW)


def recalcular(funcionario_id: str, data_str: str) -> dict | None:
    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.feriados import repository as fe_repo

    carga = ap_repo.carga_prevista(funcionario_id, data_str)
    total = ap_repo.total_dia(funcionario_id, data_str)
    he = calcular_he(_dow(data_str), fe_repo.is_feriado(data_str), carga, total, repo.get_percentuais())
    existentes = repo.list_repo(data_str, None, None, funcionario_id, None)
    if not he:
        if existentes:
            from app.modules.emails import service as em_service

            repo.limpar_dia(funcionario_id, data_str)
            try:
                em_service.limpar_he_removida(funcionario_id, data_str, [r["id"] for r in existentes])
            except Exception as exc:
                logger.warning("limpeza de e-mails HE falhou: %s", exc)
        return None
    row = repo.upsert_repo(funcionario_id, data_str, he["qtd_horas"], he["percentual"])
    removidos = [r["id"] for r in existentes if r["id"] != row["id"]]
    for rid in removidos:
        repo.limpar_percentual(rid)
    try:
        from app.modules.emails import service as em_service

        em_service.garantir_para_he(row)
        if removidos:
            em_service.limpar_he_removida(funcionario_id, data_str, removidos)
    except Exception as exc:
        logger.warning("garantir e-mail HE falhou: %s", exc)
    return row


def recalcular_dia(data_str: str) -> dict:
    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.presencas import repository as pr_repo

    ids = {p["funcionario_id"] for p in pr_repo.list_repo(data_str, None, None, None, None)}
    ids |= {a["funcionario_id"] for a in ap_repo.list_repo(data_str, None, None, None, None)}
    feitas = []
    for fid in ids:
        try:
            r = recalcular(fid, data_str)
            if r:
                feitas.append(r)
        except RuntimeError:
            raise
        except Exception:
            continue
    return {"data": data_str, "recalculados": len(ids), "horas_extras": feitas}


def listar(data=None, de=None, ate=None, funcionario_id=None, percentual=None):
    return repo.list_repo(data, de, ate, funcionario_id, percentual)
