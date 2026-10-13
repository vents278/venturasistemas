"""Regra de apropriação — ETAPA 9 (pura, sem I/O; testável isolada).

Contrato (seção 7/8 do spec):
- Só cobra quando há presença com status que exige apropriação (PRESENTE/DESLOCADO).
- Sem carga prevista (folga de escala, feriado, desligado) → sem cobrança.
- total >= carga (tolerância 0.005) → OK, sem achado.
"""

TOLERANCIA = 0.005


def avaliar_apropriacao(
    funcionario_id: str,
    data_ref: str,
    tem_presenca: bool,
    exige_apropriacao: bool,
    carga: float,
    total: float,
    status_codigo: str | None = None,
) -> dict | None:
    if not tem_presenca or not exige_apropriacao:
        return None
    if (carga or 0) <= 0 and (total or 0) > 0:
        return None
    if (total or 0) <= TOLERANCIA:
        deslocado = (status_codigo or "").upper() == "DESLOCADO"
        if not deslocado and (carga or 0) <= 0:
            return None  # sem jornada prevista e nada feito: nada a cobrar
        tipo = "DESLOCADO_SEM_OS" if deslocado else "SEM_APROPRIACAO"
        desc = (f"Deslocado sem lançamento de OS ({data_ref})" if tipo == "DESLOCADO_SEM_OS"
                else f"Sem apropriação: {carga}h previstas em {data_ref}")
        return {
            "tipo": tipo,
            "funcionario_id": funcionario_id,
            "data_ref": data_ref,
            "descricao": desc,
            "horas_faltantes": round(carga or 0, 2),
            "carga_prevista": carga,
            "total_apropriado": total,
            "origem_regra": "motor_regras.apropriacao",
        }
    faltantes = round(carga - (total or 0), 2)
    if faltantes <= TOLERANCIA:
        return None
    tipo = "SEM_APROPRIACAO" if (total or 0) <= 0 else "APROPRIACAO_INCOMPLETA"
    return {
        "tipo": tipo,
        "funcionario_id": funcionario_id,
        "data_ref": data_ref,
        "descricao": f"Apropriação incompleta: {faltantes}h pendentes (carga {carga}h x apropriado {total}h)",
        "horas_faltantes": faltantes,
        "carga_prevista": carga,
        "total_apropriado": total,
        "origem_regra": "motor_regras.apropriacao",
    }
