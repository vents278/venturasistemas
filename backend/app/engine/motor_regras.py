"""Motor de regras — ETAPA 10. Apropriação (ETAPA 9) + hora extra (ETAPA 10).

Dry-run: retorna achados SEM persistir pendências (Etapa 11 persiste)
e SEM gravar horas_extras (POST /horas-extras/recalcular persiste).
"""

from datetime import date as _date

from app.engine.regras.apropriacao import avaliar_apropriacao
from app.engine.regras.hora_extra import calcular_he


def _dow(data_ref: str) -> int:
    return (_date.fromisoformat(data_ref).weekday() + 1) % 7


def avaliar(funcionario_id: str, data_ref: str) -> list:
    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.feriados import repository as fe_repo
    from app.modules.horas_extras import repository as he_repo
    from app.modules.presencas import repository as pr_repo

    achados: list = []
    pres = pr_repo.list_repo(data_ref, None, None, funcionario_id, None)
    presenca = pres[0] if pres else None
    carga = ap_repo.carga_prevista(funcionario_id, data_ref)
    total = ap_repo.total_dia(funcionario_id, data_ref)

    if presenca:
        st = pr_repo.get_status(presenca["status_codigo"])
        exige = bool(st and st.get("exige_apropriacao"))
        a = avaliar_apropriacao(funcionario_id, data_ref, True, exige, carga, total)
        if a:
            achados.append(a)

    he = calcular_he(_dow(data_ref), fe_repo.is_feriado(data_ref), carga, total, he_repo.get_percentuais())
    if he:
        achados.append({
            "tipo": "HORA_EXTRA",
            "funcionario_id": funcionario_id,
            "data_ref": data_ref,
            "descricao": f"Hora extra: {he['qtd_horas']}h a {he['percentual']}%",
            "qtd_horas": he["qtd_horas"],
            "percentual": he["percentual"],
            "origem_regra": "motor_regras.hora_extra",
        })
    return achados


def avaliar_dia(data_ref: str) -> dict:
    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.presencas import repository as pr_repo

    presencas = pr_repo.list_repo(data_ref, None, None, None, None)
    ids = {p["funcionario_id"] for p in presencas}
    ids |= {a["funcionario_id"] for a in ap_repo.list_repo(data_ref, None, None, None, None)}
    achados: list = []
    for fid in ids:
        try:
            achados.extend(avaliar(fid, data_ref))
        except RuntimeError:
            raise
        except Exception:
            continue
    return {"data": data_ref, "avaliados": len(ids), "achados": achados}
