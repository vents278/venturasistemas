"""Regras de apropriação. Criação nunca sobrescreve (UNIQUE func/data/os);
edição é explícita via PATCH. Split normal/extra cronológico e auditável."""

from app.modules.apropriacoes import repository as repo
from app.shared.auditoria import audit

MSG_DUPLICADA = ("Este funcionário já possui apropriação nesta ordem de serviço "
                 "nesta data. Utilize a opção Editar para alterar as horas.")


def _validar_vinculos(funcionario_id: str, data_str: str, os_id: str) -> None:
    func = repo.get_funcionario(funcionario_id)
    if not func:
        raise KeyError("Funcionário não encontrado")
    if func.get("desligamento") and str(data_str) > str(func["desligamento"]):
        raise ValueError("Data posterior ao desligamento")
    if not func.get("ativo", True):
        raise ValueError("Funcionário inativo")
    if not repo.get_os(os_id):
        raise KeyError("OS não encontrada")


def _checar_teto(funcionario_id: str, data_str: str, horas_novas: float, ignorar_id=None, extra_atual=0.0) -> None:
    total = repo.total_dia(funcionario_id, data_str, ignorar_id) + horas_novas - extra_atual
    if total > 24 + 1e-9:
        raise ValueError(f"Soma do dia {total}h excede 24h")


def listar(data=None, de=None, ate=None, funcionario_id=None, os_id=None):
    return repo.list_repo(data, de, ate, funcionario_id, os_id)


def saldo(funcionario_id: str, data_str: str) -> dict:
    carga = repo.carga_prevista(funcionario_id, data_str)
    total = repo.total_dia(funcionario_id, data_str)
    return {
        "funcionario_id": funcionario_id,
        "data": data_str,
        "carga_prevista": carga,
        "total_apropriado": total,
        "saldo": round(total - carga, 2),
    }


def distribuir(funcionario_id: str, data_str: str) -> dict:
    """Divide o dia em normal/extra pela ordem cronológica de criação.
    Persiste o split por linha (auditável) e retorna o consolidado."""
    carga = repo.carga_prevista(funcionario_id, data_str)
    linhas = repo.linhas_dia(funcionario_id, data_str)
    restante, normais, extras, out = carga, 0.0, 0.0, []
    for ln in linhas:
        h = float(ln["horas"])
        n = round(min(h, max(restante, 0)), 2)
        e = round(h - n, 2)
        restante, normais, extras = round(restante - n, 2), round(normais + n, 2), round(extras + e, 2)
        repo.update_repo(ln["id"], {"horas_normais": n, "horas_extras": e})
        out.append({**ln, "horas_normais": n, "horas_extras": e})
    total = round(normais + extras, 2)
    return {"funcionario_id": funcionario_id, "data": data_str, "carga_prevista": carga,
            "total": total, "normais": normais, "extras": extras,
            "contem_extras": extras > 0, "linhas": out}


def _criar_linha(fid: str, data_str: str, os_id: str, horas: float, usuario_id=None) -> dict:
    if repo.exists_repo(fid, data_str, os_id):
        raise ValueError(MSG_DUPLICADA)
    row = repo.create_repo({"funcionario_id": fid, "data": data_str, "os_id": os_id, "horas": horas})
    distribuir(fid, data_str)
    audit(usuario_id, "apropriacoes", row.get("id"), "criar", None, row)
    return repo.get_repo(row.get("id")) or row


def registrar(body, usuario_id: str | None = None) -> dict:
    fid, data_str, os_id = str(body.funcionario_id), str(body.data), str(body.os_id)
    _validar_vinculos(fid, data_str, os_id)
    _checar_teto(fid, data_str, body.horas)
    return _criar_linha(fid, data_str, os_id, body.horas, usuario_id)


def registrar_lote(funcionario_id: str, data_str: str, itens: list, usuario_id: str | None = None) -> dict:
    _validar_vinculos(funcionario_id, data_str, str(itens[0].os_id) if itens else "")
    soma = round(sum(i.horas for i in itens), 2)
    _checar_teto(funcionario_id, data_str, soma)
    ok, erros = 0, []
    for it in itens:
        try:
            _validar_vinculos(funcionario_id, data_str, str(it.os_id))
            _criar_linha(funcionario_id, data_str, str(it.os_id), it.horas, usuario_id)
            ok += 1
        except (KeyError, ValueError) as exc:
            erros.append({"os_id": str(it.os_id), "erro": str(exc)})
    return {**saldo(funcionario_id, data_str), "lancados": ok, "erros": erros}


def registrar_lote_os(data_str: str, os_id: str, itens: list, usuario_id: str | None = None) -> dict:
    """Apropriação em massa: uma ordem distribuída em N funcionários (aparece na grade)."""
    if not repo.get_os(os_id):
        raise KeyError("OS não encontrada")
    ok, erros = 0, []
    for it in itens:
        fid = str(it.funcionario_id)
        try:
            _validar_vinculos(fid, data_str, os_id)
            _checar_teto(fid, data_str, it.horas)
            _criar_linha(fid, data_str, os_id, it.horas, usuario_id)
            ok += 1
        except (KeyError, ValueError) as exc:
            erros.append({"funcionario_id": fid, "erro": str(exc)})
    return {"data": data_str, "os_id": os_id, "ok": ok, "erros": erros}


def atualizar(ap_id: str, horas: float, usuario_id: str | None = None) -> dict:
    atual = repo.get_repo(ap_id)
    if not atual:
        raise KeyError("Apropriação não encontrada")
    _checar_teto(atual["funcionario_id"], atual["data"], horas, ignorar_id=ap_id)
    depois = repo.update_repo(ap_id, {"horas": horas})
    distribuir(atual["funcionario_id"], atual["data"])
    audit(usuario_id, "apropriacoes", ap_id, "atualizar", atual, depois)
    return depois


def excluir(ap_id: str, usuario_id: str | None = None) -> None:
    atual = repo.get_repo(ap_id)
    if not atual:
        raise KeyError("Apropriação não encontrada")
    repo.delete_repo(ap_id)
    distribuir(atual["funcionario_id"], atual["data"])
    audit(usuario_id, "apropriacoes", ap_id, "excluir", atual, None)


def consulta_funcionario(funcionario_id: str, de: str | None = None, ate: str | None = None,
                         os_codigo: str | None = None, so_extras: bool = False) -> dict:
    from app.modules.funcionarios import repository as fn_repo

    func = fn_repo.get_repo(funcionario_id)
    if not func:
        raise KeyError("Funcionário não encontrado")
    rows = repo.list_repo(None, de, ate, funcionario_id, None)
    if os_codigo:
        rows = [r for r in rows if ((r.get("ordens_servico") or {}).get("codigo") or "").upper() == os_codigo.upper()]
    linhas, dias = [], {}
    for r in sorted(rows, key=lambda x: (x.get("data", ""), str(x.get("created_at", "")))):
        n = float(r.get("horas_normais") or 0)
        e = float(r.get("horas_extras") or 0)
        if n == 0 and e == 0 and float(r.get("horas", 0)) > 0:
            n, e = _split_live(funcionario_id, r)  # linha antiga, sem split persistido
        if so_extras and e <= 0:
            continue
        osinfo = r.get("ordens_servico") or {}
        linhas.append({"id": r["id"], "data": r.get("data"), "os_id": r.get("os_id"),
                        "os_codigo": osinfo.get("codigo"), "descricao": osinfo.get("descricao"),
                        "normal": n, "extra": e, "total": round(n + e, 2)})
        dias.setdefault(r.get("data"), {"carga": 0.0, "total": 0.0})
        dias[r["data"]]["total"] = round(dias[r["data"]]["total"] + n + e, 2)
    for d in dias:
        dias[d]["carga"] = repo.carga_prevista(funcionario_id, d)
    resumo = {
        "ordens_distintas": len({(l["os_id"]) for l in linhas}),
        "dias": len(dias),
        "normais": round(sum(l["normal"] for l in linhas), 2),
        "extras": round(sum(l["extra"] for l in linhas), 2),
        "total": round(sum(l["total"] for l in linhas), 2),
        "dias_incompletos": sum(1 for d, v in dias.items() if v["carga"] > 0 and v["total"] < v["carga"] - 0.005),
    }
    return {"funcionario": {"id": func["id"], "nome": func.get("nome"), "matricula": func.get("matricula"),
                            "cargo": func.get("cargo"), "area": func.get("area")},
            "linhas": linhas, "resumo": resumo}


def _split_live(funcionario_id: str, row: dict) -> tuple[float, float]:
    """Fallback p/ linhas antigas sem split: rateia pela ordem cronológica do dia."""
    dist = distribuir(funcionario_id, row.get("data"))
    for ln in dist["linhas"]:
        if ln["id"] == row["id"]:
            return float(ln["horas_normais"]), float(ln["horas_extras"])
    return float(row.get("horas", 0)), 0.0
