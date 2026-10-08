"""Agregação do dashboard — ETAPA 15. Só leitura e soma; regra segue nos módulos/engine."""

from datetime import date as _date


def resumo(data_str: str | None = None) -> dict:
    from app.modules.absenteismo import service as ab_service
    from app.modules.emails import repository as em_repo
    from app.modules.funcionarios import repository as fn_repo
    from app.modules.horas_extras import repository as he_repo
    from app.modules.pendencias import repository as pd_repo
    from app.modules.presencas import repository as pr_repo
    from app.modules.tarefas import repository as ta_repo

    hoje = data_str or str(_date.today())
    pres = pr_repo.list_repo(hoje, None, None, None, None)
    por_status: dict = {}
    for p in pres:
        por_status[p["status_codigo"]] = por_status.get(p["status_codigo"], 0) + 1
    presentes = por_status.get("PRESENTE", 0) + por_status.get("DESLOCADO", 0)
    try:
        ativos = fn_repo.list_repo(None, True, None, None, None, 1, 1)["total"]
    except Exception:
        ativos = len(pres)
    sem_presenca = max(ativos - len(pres), 0)

    pend_abertas = pd_repo.list_repo("ABERTA", None, None, None, None)
    aprop_pend = [p for p in pend_abertas if p["tipo"] in ("APROPRIACAO_INCOMPLETA", "SEM_APROPRIACAO")]
    email_pend = [p for p in pend_abertas if p["tipo"] == "EMAIL_HE_PENDENTE"]

    he_dia = he_repo.list_repo(hoje, None, None, None, None)
    he_horas = round(sum(float(h["qtd_horas"]) for h in he_dia), 2)
    emails_pendentes = em_repo.list_repo("PENDENTE", None, None)

    tarefas = ta_repo.list_repo(None, None, None, None)
    vencidas = [t for t in tarefas if t.get("prazo") and t["prazo"] < hoje and t["status"] != "CONCLUIDO"]
    para_hoje = [t for t in tarefas if t.get("prazo") == hoje and t["status"] != "CONCLUIDO"]

    try:
        abs30 = ab_service.indicadores(None, hoje, None)
        taxa_abs = abs30["taxa_absenteismo"]
    except Exception:
        taxa_abs = 0.0

    def card(valor, link):
        return {"valor": valor, "link": link}

    return {
        "data": hoje,
        "presentes": card(presentes, f"presencas.html?data={hoje}"),
        "deslocados": card(por_status.get("DESLOCADO", 0), f"presencas.html?data={hoje}"),
        "sem_presenca": card(sem_presenca, f"presencas.html?data={hoje}"),
        "faltas": card(por_status.get("FALTA", 0), f"presencas.html?data={hoje}"),
        "apropriacoes_pendentes": card(len(aprop_pend), "pendencias.html?status=ABERTA"),
        "emails_pendentes": card(len(emails_pendentes), "emails.html"),
        "he_dia_horas": card(he_horas, f"horas_extras.html?data={hoje}"),
        "pendencias_abertas": card(len(pend_abertas), "pendencias.html?status=ABERTA"),
        "tarefas_vencidas": card(len(vencidas), "tarefas.html"),
        "tarefas_para_hoje": card(len(para_hoje), "tarefas.html"),
        "taxa_absenteismo_30d": card(taxa_abs, "absenteismo.html"),
    }
