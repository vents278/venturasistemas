"""Regra de horas extras — ETAPA 10 (pura, sem I/O).

Horas trabalhadas = total apropriado no dia (ETAPA 8).
- Feriado (qualquer dow) → 100% sobre o total.
- Domingo → 100% sobre o total. Sábado → 70% sobre o total.
- Seg–sex → 50% sobre o excedente (total − carga).
"""

TOL = 0.005


def calcular_he(dow: int, eh_feriado: bool, carga: float, total: float) -> dict | None:
    if (total or 0) <= TOL:
        return None
    if eh_feriado:
        return {"qtd_horas": round(total, 2), "percentual": 100}
    if dow == 0:
        return {"qtd_horas": round(total, 2), "percentual": 100}
    if dow == 6:
        return {"qtd_horas": round(total, 2), "percentual": 70}
    excedente = round(total - (carga or 0), 2)
    if excedente <= TOL:
        return None
    return {"qtd_horas": excedente, "percentual": 50}
