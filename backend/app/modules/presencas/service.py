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


def montar_grade(de: str, ate: str, setor: str | None = None) -> dict:
    """Grade presença × dias: cada célula traz status, obs e apropriações do dia."""
    from datetime import date as _date
    from datetime import timedelta

    from app.modules.apropriacoes import repository as ap_repo

    ini, fim = _date.fromisoformat(de), _date.fromisoformat(ate)
    if ini > fim:
        raise ValueError("Período inválido (de > ate)")
    dias = [str(ini + timedelta(days=i)) for i in range((fim - ini).days + 1)]
    if len(dias) > 62:
        raise ValueError("Período máximo de 62 dias")

    pres = repo.list_repo(None, de, ate, None, None)
    aprs = ap_repo.list_repo(None, de, ate, None, None)
    fids = {p["funcionario_id"] for p in pres} | {a["funcionario_id"] for a in aprs}
    nomes = _nomes_funcionarios(fids, setor)

    por_func: dict = {fid: {} for fid in nomes}
    for p in pres:
        if p["funcionario_id"] in por_func:
            por_func[p["funcionario_id"]][p["data"]] = {
                "status": p["status_codigo"], "obs": p.get("obs"), "apropriacoes": [], "total": 0.0,
            }
    for a in aprs:
        fid = a["funcionario_id"]
        if fid not in por_func:
            continue
        cel = por_func[fid].setdefault(a["data"], {"status": None, "obs": None, "apropriacoes": [], "total": 0.0})
        cel["apropriacoes"].append({
            "os_id": a["os_id"],
            "os_codigo": (a.get("ordens_servico") or {}).get("codigo"),
            "horas": float(a["horas"]),
        })
        cel["total"] = round(cel["total"] + float(a["horas"]), 2)
    linhas = [{"funcionario": nomes[fid], "dias": por_func[fid]} for fid in sorted(nomes, key=lambda f: nomes[f]["nome"])]
    return {"de": de, "ate": ate, "dias": dias, "linhas": linhas}


def _nomes_funcionarios(fids: set, setor: str | None = None) -> dict:
    from app.core.supabase_client import get_supabase

    if not fids:
        return {}
    sb = get_supabase()
    rows = sb.table("funcionarios").select("id,matricula,nome,setor,ativo").in_("id", sorted(fids)).execute().data or []
    out = {}
    for r in rows:
        if setor and r.get("setor") != setor:
            continue
        out[r["id"]] = {"id": r["id"], "matricula": r.get("matricula"), "nome": r.get("nome"), "setor": r.get("setor")}
    return out
