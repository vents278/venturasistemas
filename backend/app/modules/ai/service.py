"""Assistente operacional — ETAPA 18. Somente leitura dos módulos existentes.

resumo_dia: retrato do dia (presença, pendências, HE, tarefas).
perguntar: intenções por palavra-chave; desconhecida → capacidades (sem alucinar).
"""

from datetime import date as _date
from datetime import timedelta


def resumo_dia(data_str: str) -> dict:
    from app.modules.dashboard import service as db_service
    from app.modules.pendencias import service as pd_service

    dash = db_service.resumo(data_str)
    pend = pd_service.listar("ABERTA", None, None, data_str, data_str)
    he_total = dash["he_dia_horas"]["valor"]
    texto = (
        f"Dia {data_str}: {dash['presentes']['valor']} presentes, "
        f"{dash['sem_presenca']['valor']} sem presença, {dash['faltas']['valor']} faltas. "
        f"{len(pend)} pendências abertas no dia, {he_total}h extras. "
        f"{dash['tarefas_vencidas']['valor']} tarefas vencidas, {dash['tarefas_para_hoje']['valor']} para hoje."
    )
    return {"data": data_str, "resumo": texto,
            "destaques": [p["descricao"] for p in pend[:5]],
            "dashboard": {k: v["valor"] for k, v in dash.items() if k != "data"}}


def perguntar(pergunta: str) -> dict:
    from app.modules.absenteismo import service as ab_service
    from app.modules.dashboard import service as db_service
    from app.modules.horas_extras import service as he_service
    from app.modules.pendencias import service as pd_service
    from app.modules.tarefas import service as ta_service

    q = (pergunta or "").lower()
    hoje = str(_date.today())

    if "pendencia" in q or "pendência" in q:
        abertas = pd_service.listar("ABERTA", None, None, None, None)
        return {"resposta": f"Há {len(abertas)} pendências abertas.",
                "dados": [p["descricao"] for p in abertas[:10]]}
    if "hora extra" in q or q.strip() in ("he",) or "horas extras" in q:
        semana = he_service.listar(None, str(_date.today() - timedelta(days=6)), hoje, None, None)
        total = round(sum(float(h["qtd_horas"]) for h in semana), 2)
        return {"resposta": f"Últimos 7 dias: {total}h extras em {len(semana)} lançamentos.", "dados": semana[:10]}
    if "absente" in q or "falta" in q:
        ind = ab_service.indicadores(None, hoje, None)
        return {"resposta": f"Absenteísmo 30d: {ind['taxa_absenteismo']}% ({ind['dias_perdidos']} dias perdidos).",
                "dados": ind["por_tipo"]}
    if "tarefa" in q:
        todas = ta_service.listar(None, None, None, None)
        abertas = [t for t in todas if t["status"] != "CONCLUIDO"]
        return {"resposta": f"Há {len(abertas)} tarefas não concluídas.", "dados": [t["titulo"] for t in abertas[:10]]}
    if "presen" in q:
        dash = db_service.resumo(None)
        return {"resposta": f"Hoje: {dash['presentes']['valor']} presentes, {dash['sem_presenca']['valor']} sem presença.",
                "dados": {}}
    return {"resposta": ("Posso responder sobre: pendências, horas extras, absenteísmo, tarefas e presença. "
                         "Ex: 'pendências abertas?' ou 'horas extras da semana?'"),
            "dados": {}}
