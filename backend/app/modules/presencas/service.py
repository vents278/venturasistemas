"""Regras de presença — ETAPA 7/17. Valida vínculo, status e snapshot da jornada."""

from app.modules.presencas import repository as repo
from app.shared.auditoria import audit

EXIGE_VINCULO_ATIVO = {"PRESENTE", "DESLOCADO"}


def _validar(func: dict, data_str: str, status: str) -> None:
    st = repo.get_status(status)
    if not st:
        raise ValueError(f"Status inválido: {status}")
    if func.get("desligamento") and str(data_str) > str(func["desligamento"]):
        raise ValueError("Data posterior ao desligamento")
    if not func.get("ativo", True) and status in EXIGE_VINCULO_ATIVO:
        raise ValueError("Funcionário inativo não pode ter PRESENTE/DESLOCADO")


def montar_payload(funcionario_id: str, data_str: str, status: str, jornada_id=None, obs=None) -> dict:
    func = repo.get_funcionario(funcionario_id)
    if not func:
        raise KeyError("Funcionário não encontrado")
    _validar(func, data_str, status)
    payload = {
        "funcionario_id": funcionario_id,
        "data": data_str,
        "status_codigo": status,
        "obs": obs,
        "jornada_id": str(jornada_id) if jornada_id else (str(func["jornada_id"]) if func.get("jornada_id") else None),
    }
    return {k: v for k, v in payload.items() if v is not None or k == "obs"}


def listar(data=None, de=None, ate=None, funcionario_id=None, status=None):
    return repo.list_repo(data, de, ate, funcionario_id, status)


def registrar(body) -> dict:
    payload = montar_payload(
        str(body.funcionario_id), str(body.data), body.status_codigo,
        body.jornada_id, body.obs,
    )
    return repo.upsert_repo(payload)


def registrar_lote(data_str: str, itens: list) -> dict:
    ok, erros = 0, []
    for it in itens:
        try:
            payload = montar_payload(str(it.funcionario_id), data_str, it.status_codigo.upper(), None, it.obs)
            repo.upsert_repo(payload)
            ok += 1
        except (KeyError, ValueError) as exc:
            erros.append({"funcionario_id": str(it.funcionario_id), "erro": str(exc)})
    return {"data": data_str, "ok": ok, "erros": erros}


def lancamento_diario(data_str: str, status_padrao: str = "PRESENTE") -> dict:
    """Rotina diária: quem está em treinamento ganha TREINAMENTO;
    demais ativos sem lançamento ganham o status padrão (base p/ ajustes e pendências)."""
    from app.modules.funcionarios import repository as fn_repo

    status_padrao = (status_padrao or "PRESENTE").upper()
    existentes = {p["funcionario_id"] for p in repo.list_repo(data_str, None, None, None, None)}
    presentes, treinamento, ja_existiam = 0, 0, 0

    def _vale(f) -> bool:
        return not (f.get("desligamento") and data_str > str(f["desligamento"]))

    for f in fn_repo.list_treinamento():
        if not _vale(f):
            continue
        if f["id"] in existentes:
            ja_existiam += 1
            continue
        repo.upsert_repo(montar_payload(f["id"], data_str, "TREINAMENTO", None, "automático: em treinamento"))
        treinamento += 1
    for f in fn_repo.list_ativos_full():
        if f.get("em_treinamento") or not _vale(f):
            continue
        if f["id"] in existentes:
            ja_existiam += 1
            continue
        try:
            repo.upsert_repo(montar_payload(f["id"], data_str, status_padrao, None, "automático: lançamento diário"))
            presentes += 1
        except (KeyError, ValueError):
            continue
    return {"data": data_str, "presentes": presentes, "treinamento": treinamento, "ja_existiam": ja_existiam}


def atualizar(pid: str, body, usuario_id: str | None = None) -> dict:
    atual = repo.get_repo(pid)
    if not atual:
        raise KeyError("Presença não encontrada")
    patch = body.model_dump(exclude_unset=True)
    if patch.get("status_codigo"):
        patch["status_codigo"] = patch["status_codigo"].upper()
        func = repo.get_funcionario(atual["funcionario_id"])
        _validar(func, atual["data"], patch["status_codigo"])
    if patch.get("jornada_id") is not None:
        patch["jornada_id"] = str(patch["jornada_id"])
    depois = repo.update_repo(pid, patch)
    audit(usuario_id, "presencas", pid, "atualizar", atual, depois)
    return depois


def excluir(pid: str, usuario_id: str | None = None) -> None:
    row = repo.get_repo(pid)
    if not row:
        raise KeyError("Presença não encontrada")
    repo.delete_repo(pid)
    audit(usuario_id, "presencas", pid, "excluir", row, None)


def montar_grade(de: str, ate: str, setor: str | None = None, q: str | None = None,
                 area: str | None = None, supervisor_id: str | None = None) -> dict:
    """Grade presença × dias: cada célula traz status, obs e apropriações do dia."""
    from datetime import date as _date
    from datetime import timedelta

    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.funcionarios import repository as fn_repo

    ini, fim = _date.fromisoformat(de), _date.fromisoformat(ate)
    if ini > fim:
        raise ValueError("Período inválido (de > ate)")
    dias = [str(ini + timedelta(days=i)) for i in range((fim - ini).days + 1)]
    if len(dias) > 62:
        raise ValueError("Período máximo de 62 dias")

    nomes = _base_funcionarios(fn_repo, q, area, setor, supervisor_id)
    pres = repo.list_repo(None, de, ate, None, None)
    aprs = ap_repo.list_repo(None, de, ate, None, None)

    por_func: dict = {fid: {} for fid in nomes}
    for p in pres:
        if p["funcionario_id"] in por_func:
            por_func[p["funcionario_id"]][p["data"]] = {
                "status": p["status_codigo"], "obs": p.get("obs"),
                "jornada_id": p.get("jornada_id"), "apropriacoes": [], "total": 0.0,
            }
    for a in aprs:
        fid = a["funcionario_id"]
        if fid not in por_func:
            continue
        cel = por_func[fid].setdefault(a["data"], {"status": None, "obs": None, "jornada_id": None, "apropriacoes": [], "total": 0.0})
        cel["apropriacoes"].append({
            "os_id": a["os_id"],
            "os_codigo": (a.get("ordens_servico") or {}).get("codigo"),
            "horas": float(a["horas"]),
        })
        cel["total"] = round(cel["total"] + float(a["horas"]), 2)
    linhas = [{"funcionario": nomes[fid], "dias": por_func[fid]} for fid in sorted(nomes, key=lambda f: nomes[f]["nome"])]
    return {"de": de, "ate": ate, "dias": dias, "linhas": linhas}


def _base_funcionarios(fn_repo, q, area, setor, supervisor_id) -> dict:
    """Base = ativos (com filtros) + quem tem lançamento no período."""
    out = {}
    for r in fn_repo.list_ativos_full():
        if setor and r.get("setor") != setor:
            continue
        if area and (r.get("area") or "") != area:
            continue
        if supervisor_id and str(r.get("supervisor_id") or "") != supervisor_id:
            continue
        if q and q.lower() not in f"{r.get('nome', '')} {r.get('matricula', '')}".lower():
            continue
        out[r["id"]] = {"id": r["id"], "matricula": r.get("matricula"), "nome": r.get("nome"),
                        "setor": r.get("setor"), "area": r.get("area"),
                        "supervisor_id": str(r["supervisor_id"]) if r.get("supervisor_id") else None,
                        "jornada_id": str(r["jornada_id"]) if r.get("jornada_id") else None}
    return out


def _nomes_funcionarios(fids: set, setor: str | None = None) -> dict:
    from app.modules.funcionarios import repository as fn_repo

    return {fid: f for fid, f in _base_funcionarios(fn_repo, None, None, setor, None).items() if fid in fids}
