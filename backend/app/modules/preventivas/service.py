"""Regras de programação/controle de preventivas.

Status individual e da preventiva são derivados automaticamente dos dados
(programação × presença × OS recebidas). O status da preventiva é persistido a
cada mutação (exceto CANCELADA), alimentando filtros, cards e relatórios.

Pendências documentais são sincronizadas de forma idempotente na tabela
public.pendencias (tipos PREVENTIVA_*), separadas da apropriação de horas.
"""

from datetime import date, datetime, timezone

from app.modules.pendencias import repository as pd_repo
from app.modules.preventivas import repository as repo
from app.modules.preventivas.schemas import STATUS_PREVENTIVA
from app.shared.auditoria import audit

# situações individuais (derivadas, não persistidas)
SIT_NAO_PROGRAMADO = "NAO_PROGRAMADO"
SIT_PROGRAMADO = "PROGRAMADO"
SIT_NAO_COMPARECEU = "NAO_COMPARECEU"
SIT_AGUARDANDO_OS = "AGUARDANDO_OS"
SIT_OS_PENDENTE = "OS_PENDENTE"
SIT_PARCIAL = "PARCIALMENTE_REGULARIZADO"
SIT_REGULARIZADO = "REGULARIZADO"

TIPOS_PEND_PREVENTIVA = [
    "PREVENTIVA_SEM_OS", "PREVENTIVA_OS_PENDENTE",
    "PREVENTIVA_DOC_INCOMPLETA", "PREVENTIVA_HORAS_DIVERGENTES",
]


def _hoje() -> str:
    return date.today().isoformat()


def _t(v) -> str | None:
    """time → 'HH:MM:SS' (Supabase). Aceita None/str já pronto."""
    if v is None:
        return None
    return v if isinstance(v, str) else str(v)


# --------------------------------------------------------------------------
# Status derivados
# --------------------------------------------------------------------------
def status_funcionario(pf: dict, oss: list, data_prev: str, hoje: str) -> str:
    if not pf.get("programado") and not pf.get("compareceu"):
        return SIT_NAO_PROGRAMADO
    if not pf.get("compareceu"):
        return SIT_NAO_COMPARECEU if str(data_prev) < hoje else SIT_PROGRAMADO
    total = len(oss)
    recebidas = sum(1 for o in oss if o.get("recebida"))
    if total == 0:
        return SIT_REGULARIZADO if pf.get("os_completa") else SIT_AGUARDANDO_OS
    if recebidas == total:
        return SIT_REGULARIZADO
    if recebidas == 0:
        return SIT_OS_PENDENTE
    return SIT_PARCIAL


def status_preventiva(prev: dict, linhas: list) -> str:
    if prev.get("status") == "CANCELADA":
        return "CANCELADA"
    presentes = [l for l in linhas if l["compareceu"]]
    if not presentes:
        return "PROGRAMADA"
    programados = [l for l in linhas if l["programado"]]
    total_os = sum(l["os_total"] for l in linhas)
    recebidas = sum(l["os_recebidas"] for l in linhas)
    pendentes = total_os - recebidas
    tudo_confirmado = all(l["os_completa"] for l in presentes)
    if tudo_confirmado and pendentes == 0 and all(l["status"] == SIT_REGULARIZADO for l in presentes):
        return "CONCLUIDA"
    if len(presentes) < len(programados):
        return "EM_ANDAMENTO"
    if total_os == 0:
        return "AGUARDANDO_OS"
    if pendentes > 0 and recebidas > 0:
        return "PARCIALMENTE_CONCLUIDA"
    if pendentes > 0:
        return "AGUARDANDO_OS"
    return "CONCLUIDA"


# --------------------------------------------------------------------------
# Montagem de detalhe / linhas
# --------------------------------------------------------------------------
def _linha_funcionario(pf: dict, oss: list, data_prev: str, hoje: str) -> dict:
    fn = pf.get("funcionarios") or {}
    jornada = fn.get("jornadas") or {}
    recebidas = sum(1 for o in oss if o.get("recebida"))
    return {
        "id": pf["id"],
        "funcionario_id": pf["funcionario_id"],
        "funcionario": {
            "id": pf["funcionario_id"],
            "nome": fn.get("nome"),
            "matricula": fn.get("matricula"),
            "cargo": fn.get("cargo"),
            "area": fn.get("area"),
            "setor": fn.get("setor"),
            "escala": jornada.get("codigo") if isinstance(jornada, dict) else None,
        },
        "programado": bool(pf.get("programado")),
        "compareceu": bool(pf.get("compareceu")),
        "hora_prev_inicio": pf.get("hora_prev_inicio"),
        "hora_prev_fim": pf.get("hora_prev_fim"),
        "hora_efet_inicio": pf.get("hora_efet_inicio"),
        "hora_efet_fim": pf.get("hora_efet_fim"),
        "os_completa": bool(pf.get("os_completa")),
        "observacoes": pf.get("observacoes"),
        "status": status_funcionario(pf, oss, data_prev, hoje),
        "os": oss,
        "os_total": len(oss),
        "os_recebidas": recebidas,
        "os_pendentes": len(oss) - recebidas,
        "os_recebida_geral": len(oss) > 0 and recebidas == len(oss),
    }


def _montar_linhas(prev: dict, funcs: list, oss: list, hoje: str) -> list:
    por_pf: dict = {}
    for o in oss:
        por_pf.setdefault(o["preventiva_funcionario_id"], []).append(o)
    return [_linha_funcionario(pf, por_pf.get(pf["id"], []), prev["data"], hoje) for pf in funcs]


def _agregados(prev: dict, linhas: list) -> dict:
    total_os = sum(l["os_total"] for l in linhas)
    recebidas = sum(l["os_recebidas"] for l in linhas)
    return {
        "programados": sum(1 for l in linhas if l["programado"]),
        "presentes": sum(1 for l in linhas if l["compareceu"]),
        "funcionarios_pendentes": sum(1 for l in linhas if l["status"] in (SIT_AGUARDANDO_OS, SIT_OS_PENDENTE, SIT_PARCIAL)),
        "os_total": total_os,
        "os_recebidas": recebidas,
        "os_pendentes": total_os - recebidas,
    }


def montar_detalhe(pid: str) -> dict:
    prev = repo.get_repo(pid)
    if not prev:
        raise KeyError("Preventiva não encontrada")
    funcs = repo.list_funcionarios(pid)
    oss = repo.list_os(pid)
    linhas = _montar_linhas(prev, funcs, oss, _hoje())
    agregados = _agregados(prev, linhas)
    resp = prev.get("funcionarios") or {}
    prev_out = {**prev, "status_calc": status_preventiva(prev, linhas),
                "responsavel_nome": resp.get("nome") if isinstance(resp, dict) else None}
    return {"preventiva": prev_out, "funcionarios": linhas, "agregados": agregados}


def _recalcular_status(pid: str) -> str:
    detalhe = montar_detalhe(pid)
    novo = detalhe["preventiva"]["status_calc"]
    if detalhe["preventiva"].get("status") != "CANCELADA" and novo != detalhe["preventiva"].get("status"):
        repo.update_repo(pid, {"status": novo})
    return novo


# --------------------------------------------------------------------------
# Listagem + indicadores
# --------------------------------------------------------------------------
def _resumo(prev: dict, linhas: list) -> dict:
    ag = _agregados(prev, linhas)
    resp = prev.get("funcionarios") or {}
    return {
        "id": prev["id"],
        "data": prev.get("data"),
        "area": prev.get("area"),
        "equipamento": prev.get("equipamento"),
        "descricao": prev.get("descricao"),
        "status": prev.get("status_calc") or prev.get("status"),
        "hora_inicio": prev.get("hora_inicio"),
        "hora_fim": prev.get("hora_fim"),
        "observacoes": prev.get("observacoes"),
        "responsavel_id": prev.get("responsavel_id"),
        "responsavel_nome": resp.get("nome") if isinstance(resp, dict) else None,
        "os_completa": prev.get("os_completa"),
        **ag,
    }


def listar(data=None, de=None, ate=None, area=None, status=None, funcionario_id=None,
           funcionario=None, cargo=None, os_codigo=None, situacao=None, empresa_id=None) -> list:
    prevs = repo.list_repo(de=de, ate=ate, data=data, area=area, status=status)
    if empresa_id:
        prevs = [p for p in prevs if not p.get("empresa_id") or str(p["empresa_id"]) == empresa_id]
    ids = [p["id"] for p in prevs]
    funcs = repo.list_funcionarios_por(ids)
    oss = repo.list_os_por(ids)
    f_by: dict = {}
    o_by: dict = {}
    for f in funcs:
        f_by.setdefault(f["preventiva_id"], []).append(f)
    for o in oss:
        o_by.setdefault(o["preventiva_id"], []).append(o)
    hoje = _hoje()
    out = []
    for p in prevs:
        linhas = _montar_linhas(p, f_by.get(p["id"], []), o_by.get(p["id"], []), hoje)
        linha_resumo = _resumo({**p, "status_calc": status_preventiva(p, linhas)}, linhas)
        if not _passa_filtros(linha_resumo, linhas, funcionario_id, funcionario, cargo, os_codigo, situacao):
            continue
        linha_resumo["funcionarios"] = [
            {"id": l["funcionario"]["id"], "nome": l["funcionario"]["nome"],
             "cargo": l["funcionario"]["cargo"], "status": l["status"],
             "compareceu": l["compareceu"], "os_total": l["os_total"], "os_recebidas": l["os_recebidas"]}
            for l in linhas
        ]
        out.append(linha_resumo)
    return out


def _passa_filtros(r: dict, linhas: list, funcionario_id, funcionario, cargo, os_codigo, situacao) -> bool:
    if funcionario_id and not any(l["funcionario_id"] == funcionario_id for l in linhas):
        return False
    if funcionario:
        alvo = funcionario.strip().lower()
        if not any(alvo in f"{l['funcionario'].get('nome') or ''} {l['funcionario'].get('matricula') or ''}".lower()
                   for l in linhas):
            return False
    if cargo and not any((l["funcionario"]["cargo"] or "").lower().find(cargo.lower()) >= 0 for l in linhas):
        return False
    if os_codigo:
        alvo = os_codigo.strip().lower()
        if not any(alvo in (o.get("os_codigo") or "").lower() for l in linhas for o in l["os"]):
            return False
    if situacao == "PENDENTE" and r["os_pendentes"] <= 0:
        return False
    if situacao == "REGULARIZADO" and not (r["os_total"] > 0 and r["os_pendentes"] == 0):
        return False
    if situacao == "SEM_OS" and r["os_total"] != 0:
        return False
    return True


def indicadores(**filtros) -> dict:
    itens = listar(**filtros)
    return {
        "total_preventivas": len(itens),
        "em_andamento": sum(1 for i in itens if i["status"] == "EM_ANDAMENTO"),
        "aguardando_os": sum(1 for i in itens if i["status"] in ("AGUARDANDO_OS", "PARCIALMENTE_CONCLUIDA")),
        "funcionarios_programados": sum(i["programados"] for i in itens),
        "funcionarios_compareceram": sum(i["presentes"] for i in itens),
        "os_total": sum(i["os_total"] for i in itens),
        "os_recebidas": sum(i["os_recebidas"] for i in itens),
        "os_pendentes": sum(i["os_pendentes"] for i in itens),
    }


# --------------------------------------------------------------------------
# CRUD preventiva
# --------------------------------------------------------------------------
def _validar_status(status: str | None) -> None:
    if status and status.upper() not in STATUS_PREVENTIVA:
        raise ValueError(f"Status inválido: {status}")


def criar(body, usuario_id: str | None = None, empresa_id: str | None = None) -> dict:
    _validar_status(body.status)
    if body.responsavel_id and not repo.get_funcionario(str(body.responsavel_id)):
        raise KeyError("Responsável não encontrado")
    payload = {
        "data": str(body.data),
        "area": body.area.strip(),
        "equipamento": (body.equipamento or None),
        "descricao": body.descricao.strip(),
        "responsavel_id": str(body.responsavel_id) if body.responsavel_id else None,
        "hora_inicio": _t(body.hora_inicio),
        "hora_fim": _t(body.hora_fim),
        "observacoes": body.observacoes or None,
        "status": (body.status or "PROGRAMADA").upper(),
        "empresa_id": str(body.empresa_id) if body.empresa_id else empresa_id,
        "created_by": usuario_id,
    }
    row = repo.create_repo(payload)
    audit(usuario_id, "preventivas", row.get("id"), "criar", None, row)
    return montar_detalhe(row["id"])


def atualizar(pid: str, body, usuario_id: str | None = None) -> dict:
    atual = repo.get_repo(pid)
    if not atual:
        raise KeyError("Preventiva não encontrada")
    patch = body.model_dump(exclude_unset=True)
    if patch.get("status"):
        _validar_status(patch["status"])
        patch["status"] = patch["status"].upper()
    if patch.get("responsavel_id"):
        if not repo.get_funcionario(str(patch["responsavel_id"])):
            raise KeyError("Responsável não encontrado")
        patch["responsavel_id"] = str(patch["responsavel_id"])
    for campo in ("data",):
        if patch.get(campo) is not None:
            patch[campo] = str(patch[campo])
    for campo in ("hora_inicio", "hora_fim"):
        if campo in patch:
            patch[campo] = _t(patch[campo])
    depois = repo.update_repo(pid, patch)
    audit(usuario_id, "preventivas", pid, "atualizar", atual, depois)
    return montar_detalhe(pid)


def excluir(pid: str, usuario_id: str | None = None) -> None:
    atual = repo.get_repo(pid)
    if not atual:
        raise KeyError("Preventiva não encontrada")
    repo.delete_repo(pid)
    _resolver_pendencias(pid, atual)
    audit(usuario_id, "preventivas", pid, "excluir", atual, None)


# --------------------------------------------------------------------------
# Funcionários programados
# --------------------------------------------------------------------------
def adicionar_funcionario(pid: str, body, usuario_id: str | None = None) -> dict:
    prev = repo.get_repo(pid)
    if not prev:
        raise KeyError("Preventiva não encontrada")
    fid = str(body.funcionario_id)
    if not repo.get_funcionario(fid):
        raise KeyError("Funcionário não encontrado")
    if repo.find_funcionario(pid, fid):
        raise ValueError("Funcionário já está programado nesta preventiva")
    payload = {
        "preventiva_id": pid,
        "funcionario_id": fid,
        "programado": body.programado,
        "compareceu": body.compareceu,
        "hora_prev_inicio": _t(body.hora_prev_inicio),
        "hora_prev_fim": _t(body.hora_prev_fim),
        "hora_efet_inicio": _t(body.hora_efet_inicio),
        "hora_efet_fim": _t(body.hora_efet_fim),
        "os_completa": body.os_completa,
        "observacoes": body.observacoes or None,
    }
    row = repo.create_funcionario(payload)
    audit(usuario_id, "preventiva_funcionarios", row.get("id"), "criar", None, row)
    recalcular(pid)
    return montar_detalhe(pid)


def atualizar_funcionario(pid: str, pf_id: str, body, usuario_id: str | None = None) -> dict:
    atual = _pf_do_pid(pid, pf_id)
    patch = body.model_dump(exclude_unset=True)
    for campo in ("hora_prev_inicio", "hora_prev_fim", "hora_efet_inicio", "hora_efet_fim"):
        if campo in patch:
            patch[campo] = _t(patch[campo])
    depois = repo.update_funcionario(pf_id, patch)
    audit(usuario_id, "preventiva_funcionarios", pf_id, "atualizar", atual, depois)
    recalcular(pid)
    return montar_detalhe(pid)


def remover_funcionario(pid: str, pf_id: str, usuario_id: str | None = None) -> dict:
    atual = _pf_do_pid(pid, pf_id)
    repo.delete_funcionario(pf_id)
    _resolver_pendencia_funcionario(atual)
    audit(usuario_id, "preventiva_funcionarios", pf_id, "excluir", atual, None)
    recalcular(pid)
    return montar_detalhe(pid)


def _pf_do_pid(pid: str, pf_id: str) -> dict:
    pf = repo.get_funcionario_row(pf_id)
    if not pf or str(pf.get("preventiva_id")) != str(pid):
        raise KeyError("Funcionário programado não encontrado")
    return pf


# --------------------------------------------------------------------------
# OS por funcionário
# --------------------------------------------------------------------------
def adicionar_os(pid: str, pf_id: str, body, usuario_id: str | None = None) -> dict:
    pf = _pf_do_pid(pid, pf_id)
    codigo = (body.os_codigo or "").strip()
    if not codigo:
        raise ValueError("Número da OS é obrigatório")
    if repo.find_os_dup(pf_id, codigo):
        raise ValueError(f"OS {codigo} já lançada para este funcionário — edite as horas em vez de duplicar.")
    os_id = _resolver_os_id(body.os_id, codigo)
    recebida = bool(body.recebida)
    payload = {
        "preventiva_id": pid,
        "preventiva_funcionario_id": pf_id,
        "funcionario_id": pf["funcionario_id"],
        "os_codigo": codigo,
        "os_id": os_id,
        "descricao": body.descricao or None,
        "data_execucao": str(body.data_execucao) if body.data_execucao else None,
        "horas": float(body.horas or 0),
        "recebida": recebida,
        "data_recebimento": _hoje() if recebida else None,
        "recebido_por": usuario_id if recebida else None,
        "observacoes": body.observacoes or None,
        "anexo_url": body.anexo_url or None,
    }
    row = repo.create_os(payload)
    # paridade com apropriação: registrar OS implica presença do funcionário
    if not pf.get("compareceu"):
        repo.update_funcionario(pf_id, {"compareceu": True})
    audit(usuario_id, "preventiva_os", row.get("id"), "criar", None, row)
    recalcular(pid)
    return montar_detalhe(pid)


def atualizar_os(pid: str, pf_id: str, osrow_id: str, body, usuario_id: str | None = None) -> dict:
    row = _os_do_pf(pf_id, osrow_id)
    patch = body.model_dump(exclude_unset=True)
    if "os_codigo" in patch:
        novo = (patch["os_codigo"] or "").strip()
        if not novo:
            raise ValueError("Número da OS é obrigatório")
        dup = repo.find_os_dup(pf_id, novo)
        if dup and dup["id"] != osrow_id:
            raise ValueError(f"OS {novo} já lançada para este funcionário")
        patch["os_codigo"] = novo
    if "os_id" in patch:
        patch["os_id"] = _resolver_os_id(patch["os_id"], patch.get("os_codigo") or row["os_codigo"])
    if patch.get("data_execucao") is not None:
        patch["data_execucao"] = str(patch["data_execucao"])
    if "horas" in patch and patch["horas"] is not None:
        patch["horas"] = float(patch["horas"])
    if "recebida" in patch:
        if patch["recebida"] and not row.get("recebida"):
            patch["data_recebimento"] = _hoje()
            patch["recebido_por"] = usuario_id
        elif not patch["recebida"]:
            patch["data_recebimento"] = None
            patch["recebido_por"] = None
    depois = repo.update_os(osrow_id, patch)
    audit(usuario_id, "preventiva_os", osrow_id, "atualizar", row, depois)
    recalcular(pid)
    return montar_detalhe(pid)


def remover_os(pid: str, pf_id: str, osrow_id: str, usuario_id: str | None = None) -> dict:
    row = _os_do_pf(pf_id, osrow_id)
    repo.delete_os(osrow_id)
    audit(usuario_id, "preventiva_os", osrow_id, "excluir", row, None)
    recalcular(pid)
    return montar_detalhe(pid)


def _os_do_pf(pf_id: str, osrow_id: str) -> dict:
    row = repo.get_os_row(osrow_id)
    if not row or str(row.get("preventiva_funcionario_id")) != str(pf_id):
        raise KeyError("OS não encontrada para este funcionário")
    return row


def _resolver_os_id(os_id, codigo: str):
    """Vincula a OS já cadastrada no ERP quando existir (por id informado ou pelo código)."""
    if os_id:
        cad = repo.get_os_cadastrada(str(os_id))
        if not cad:
            raise KeyError("OS informada não encontrada no cadastro")
        return str(os_id)
    cad = repo.achar_os_por_codigo(codigo)
    return str(cad["id"]) if cad else None


# --------------------------------------------------------------------------
# Pendências automáticas (idempotentes)
# --------------------------------------------------------------------------
def _upsert_pendencia(tipo: str, funcionario_id: str, data_ref: str, registro_id: str,
                      descricao: str, prioridade: str) -> None:
    existente = pd_repo.find_aberta_reg(tipo, funcionario_id, data_ref, registro_id)
    if existente:
        pd_repo.update_repo(existente["id"], {"descricao": descricao, "prioridade": prioridade})
    else:
        pd_repo.create_repo({
            "tipo": tipo,
            "funcionario_id": funcionario_id,
            "data_ref": data_ref,
            "descricao": descricao,
            "prioridade": prioridade,
            "status": "ABERTA",
            "origem_regra": "preventivas.checklist",
            "registro_tipo": "preventiva_funcionarios",
            "registro_id": registro_id,
        })


def _resolver_tipo(tipo: str, funcionario_id: str, data_ref: str, registro_id: str) -> None:
    existente = pd_repo.find_aberta_reg(tipo, funcionario_id, data_ref, registro_id)
    if existente:
        pd_repo.update_repo(existente["id"], {
            "status": "RESOLVIDA", "resolved_at": datetime.now(timezone.utc).isoformat()})


def _resolver_pendencia_funcionario(pf: dict) -> None:
    data_ref = pf.get("data_prev")
    for tipo in TIPOS_PEND_PREVENTIVA:
        existente = pd_repo.find_aberta_reg(tipo, pf["funcionario_id"], data_ref, pf["id"])
        if existente:
            pd_repo.update_repo(existente["id"], {
                "status": "RESOLVIDA", "resolved_at": datetime.now(timezone.utc).isoformat()})


def _resolver_pendencias(pid: str, prev: dict) -> None:
    for pf in repo.list_funcionarios(pid):
        for tipo in TIPOS_PEND_PREVENTIVA:
            existente = pd_repo.find_aberta_reg(tipo, pf["funcionario_id"], prev.get("data"), pf["id"])
            if existente:
                pd_repo.update_repo(existente["id"], {
                    "status": "RESOLVIDA", "resolved_at": datetime.now(timezone.utc).isoformat()})


def sincronizar_pendencias(pid: str) -> dict:
    """Recalcula pendências documentais da preventiva. Idempotente.

    Regras: ausentes não geram pendência de OS; OS pendentes e ausência de
    lançamento geram pendência; divergência de horas vs. apropriação gera pendência.
    """
    prev = repo.get_repo(pid)
    if not prev:
        raise KeyError("Preventiva não encontrada")
    funcs = repo.list_funcionarios(pid)
    oss = repo.list_os(pid)
    por_pf: dict = {}
    for o in oss:
        por_pf.setdefault(o["preventiva_funcionario_id"], []).append(o)
    data_ref = prev["data"]
    ativos: set = set()
    geradas = 0
    for pf in funcs:
        if not pf.get("compareceu"):
            _resolver_pendencia_funcionario({**pf, "data_prev": data_ref})
            continue
        oss_pf = por_pf.get(pf["id"], [])
        total = len(oss_pf)
        recebidas = sum(1 for o in oss_pf if o.get("recebida"))
        fn = pf.get("funcionarios") or {}
        nome = fn.get("nome") or pf["funcionario_id"]
        if total == 0 and not pf.get("os_completa"):
            _upsert_pendencia("PREVENTIVA_SEM_OS", pf["funcionario_id"], data_ref, pf["id"],
                              f"{nome}: compareceu mas nenhuma OS foi lançada ({prev.get('area')} {data_ref}).", "ALTA")
            ativos.add(("PREVENTIVA_SEM_OS", pf["id"]))
        elif total > 0 and recebidas < total:
            _upsert_pendencia("PREVENTIVA_OS_PENDENTE", pf["funcionario_id"], data_ref, pf["id"],
                              f"{nome}: {recebidas} de {total} OS recebidas — pendente {total - recebidas} OS.",
                              "ALTA" if recebidas == 0 else "MEDIA")
            ativos.add(("PREVENTIVA_OS_PENDENTE", pf["id"]))
        divergencia = _divergencia_horas(pf, oss_pf, data_ref)
        if divergencia is not None:
            _upsert_pendencia("PREVENTIVA_HORAS_DIVERGENTES", pf["funcionario_id"], data_ref, pf["id"],
                              f"{nome}: horas lançadas nas OS ({divergencia['os']}h) divergem "
                              f"da apropriação ({divergencia['apropriado']}h).", "MEDIA")
            ativos.add(("PREVENTIVA_HORAS_DIVERGENTES", pf["id"]))
    # resolve as que não são mais válidas
    for tipo in TIPOS_PEND_PREVENTIVA:
        for p in pd_repo.list_abertas_por_data(data_ref, [tipo]):
            reg = p.get("registro_id")
            if (p.get("registro_tipo") == "preventiva_funcionarios" and reg
                    and (tipo, reg) not in ativos and any(str(x["id"]) == str(reg) for x in funcs)):
                pd_repo.update_repo(p["id"], {"status": "RESOLVIDA", "resolved_at": datetime.now(timezone.utc).isoformat()})
    return {"preventiva_id": pid, "pendencias_abertas": len(ativos)}


def _divergencia_horas(pf: dict, oss_pf: list, data_ref: str):
    """Compara horas das OS vinculadas (os_id) com a apropriação do dia. None se não comparável."""
    vinculadas = [o for o in oss_pf if o.get("os_id")]
    if not vinculadas:
        return None
    total_os = round(sum(float(o.get("horas") or 0) for o in vinculadas), 2)
    aps = repo.apropriacoes_func_data(pf["funcionario_id"], data_ref)
    if not aps:
        return None
    apropriado = round(sum(float(a.get("horas") or 0) for a in aps), 2)
    if abs(total_os - apropriado) > 0.01:
        return {"os": total_os, "apropriado": apropriado}
    return None


def recalcular(pid: str) -> dict:
    """Persiste o status derivado e sincroniza pendências. Usado após cada mutação."""
    status = _recalcular_status(pid)
    try:
        sincronizar_pendencias(pid)
    except Exception:
        pass  # pendência é acessória; nunca trava a operação principal
    return {"preventiva_id": pid, "status": status}
