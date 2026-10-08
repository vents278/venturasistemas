"""Motor de pendências — ETAPA 11. Persiste achados de apropriação, idempotente.

HORA_EXTRA não vira pendência aqui (vira horas_extras na ETAPA 10;
e-mail pendente na ETAPA 13). EMAIL_HE_PENDENTE/FALTA_INFO entram nas próximas etapas.
"""

from datetime import datetime, timezone

from app.modules.pendencias import repository as pd_repo

TIPOS_APROPRIACAO = {"APROPRIACAO_INCOMPLETA", "SEM_APROPRIACAO"}


def _prioridade(achado: dict) -> str:
    if achado["tipo"] == "SEM_APROPRIACAO":
        return "ALTA"
    return "ALTA" if (achado.get("horas_faltantes") or 0) >= 4 else "MEDIA"


def gerar_pendencias(achados: list) -> list:
    geradas = []
    for a in achados:
        if a.get("tipo") not in TIPOS_APROPRIACAO:
            continue
        existente = pd_repo.find_aberta(a["tipo"], a["funcionario_id"], a["data_ref"])
        if existente:
            geradas.append(pd_repo.update_repo(existente["id"], {
                "descricao": a["descricao"],
                "prioridade": _prioridade(a),
                "origem_regra": a.get("origem_regra", "motor_regras.apropriacao"),
            }))
        else:
            geradas.append(pd_repo.create_repo({
                "tipo": a["tipo"],
                "funcionario_id": a["funcionario_id"],
                "data_ref": a["data_ref"],
                "descricao": a["descricao"],
                "prioridade": _prioridade(a),
                "status": "ABERTA",
                "origem_regra": a.get("origem_regra", "motor_regras.apropriacao"),
                "registro_tipo": "apropriacoes",
            }))
    return geradas


def sincronizar_dia(data_ref: str) -> dict:
    from app.engine import motor_regras

    avaliacao = motor_regras.avaliar_dia(data_ref)
    geradas = gerar_pendencias(avaliacao["achados"])
    com_pendencia = {(a["tipo"], a["funcionario_id"]) for a in avaliacao["achados"] if a.get("tipo") in TIPOS_APROPRIACAO}
    resolvidas = []
    for p in pd_repo.list_abertas_por_data(data_ref, sorted(TIPOS_APROPRIACAO)):
        if (p["tipo"], p["funcionario_id"]) not in com_pendencia:
            resolvidas.append(pd_repo.update_repo(p["id"], {"status": "RESOLVIDA", "resolved_at": datetime.now(timezone.utc).isoformat()}))
    return {"data": data_ref, "avaliados": avaliacao["avaliados"], "geradas": len(geradas), "resolvidas": len(resolvidas)}
