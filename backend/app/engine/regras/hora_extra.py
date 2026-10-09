"""Regra de horas extras (pura, sem I/O).

Horas trabalhadas = total apropriado no dia.
- Feriado (qualquer dow) → percentual FERIADO sobre o total.
- Domingo → DOMINGO. Sábado → SABADO. Seg–sex → SEG_SEX sobre o excedente.
Percentuais vêm de parametros_he (configurável), com fallback 50/70/100.
"""

TOL = 0.005
PADRAO = {"SEG_SEX": 50, "SABADO": 70, "DOMINGO": 100, "FERIADO": 100}


def calcular_he(dow: int, eh_feriado: bool, carga: float, total: float, perc: dict | None = None) -> dict | None:
    p = {**PADRAO, **(perc or {})}
    if (total or 0) <= TOL:
        return None
    if eh_feriado:
        return {"qtd_horas": round(total, 2), "percentual": p["FERIADO"]}
    if dow == 0:
        return {"qtd_horas": round(total, 2), "percentual": p["DOMINGO"]}
    if dow == 6:
        return {"qtd_horas": round(total, 2), "percentual": p["SABADO"]}
    excedente = round(total - (carga or 0), 2)
    if excedente <= TOL:
        return None
    return {"qtd_horas": excedente, "percentual": p["SEG_SEX"]}
