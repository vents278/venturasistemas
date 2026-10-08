"""Regras de absenteísmo — ETAPA 14. Peso: INTEGRAL=1, meio período=0.5.

Taxa simplificada: dias_perdidos / (ativos × dias_úteis) × 100.
Dias úteis = seg–sex menos feriados (sem escala individual nesta etapa).
"""

from datetime import date as _date
from datetime import timedelta

from app.modules.absenteismo import repository as repo
from app.modules.absenteismo.schemas import PERIODOS
from app.shared.auditoria import audit

PESO = {"INTEGRAL": 1.0, "MANHA": 0.5, "TARDE": 0.5}


def peso(periodo: str) -> float:
    return PESO.get((periodo or "INTEGRAL").upper(), 1.0)


def listar(de=None, ate=None, funcionario_id=None, tipo_id=None, setor=None):
    return repo.list_repo(de, ate, funcionario_id, tipo_id, setor)


def criar(body) -> dict:
    func = repo.get_funcionario(str(body.funcionario_id))
    if not func:
        raise KeyError("Funcionário não encontrado")
    if func.get("desligamento") and str(body.data) > str(func["desligamento"]):
        raise ValueError("Data posterior ao desligamento")
    if not repo.get_tipo(body.tipo_id):
        raise KeyError("Tipo de ausência não encontrado")
    payload = {
        "funcionario_id": str(body.funcionario_id),
        "data": str(body.data),
        "tipo_id": body.tipo_id,
        "motivo": body.motivo,
        "periodo": body.periodo,
        "anexo_url": body.anexo_url,
        "observacao": body.observacao,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    try:
        return repo.create_repo(payload)
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise ValueError("Ausência já lançada (funcionário/data/tipo)")
        raise


def atualizar(aid: str, body, usuario_id: str | None = None) -> dict:
    atual = repo.get_repo(aid)
    if not atual:
        raise KeyError("Ausência não encontrada")
    patch = body.model_dump(exclude_unset=True)
    if patch.get("periodo") and patch["periodo"].upper() not in PERIODOS:
        raise ValueError("Período inválido")
    if patch.get("tipo_id") and not repo.get_tipo(patch["tipo_id"]):
        raise KeyError("Tipo de ausência não encontrado")
    depois = repo.update_repo(aid, patch)
    audit(usuario_id, "absenteismo", aid, "atualizar", atual, depois)
    return depois


def excluir(aid: str, usuario_id: str | None = None) -> None:
    atual = repo.get_repo(aid)
    if not atual:
        raise KeyError("Ausência não encontrada")
    repo.delete_repo(aid)
    audit(usuario_id, "absenteismo", aid, "excluir", atual, None)


def indicadores(de: str | None, ate: str | None, setor: str | None = None) -> dict:
    from app.modules.feriados import repository as fe_repo

    fim = _date.fromisoformat(ate) if ate else _date.today()
    ini = _date.fromisoformat(de) if de else fim - timedelta(days=29)
    if ini > fim:
        raise ValueError("Período inválido (de > ate)")
    feriados = {f["data"] for f in fe_repo.list_repo(None)}
    dias_uteis = sum(
        1 for i in range((fim - ini).days + 1)
        if (d := ini + timedelta(days=i)).weekday() < 5 and str(d) not in feriados
    )
    rows = repo.list_repo(str(ini), str(fim), None, None, setor)
    por_tipo: dict = {}
    por_func: dict = {}
    por_setor: dict = {}
    dias_perdidos = 0.0
    for r in rows:
        p = peso(r.get("periodo"))
        dias_perdidos += p
        tipo = ((r.get("tipos_ausencia") or {}).get("codigo")) or str(r.get("tipo_id"))
        por_tipo[tipo] = round(por_tipo.get(tipo, 0) + p, 2)
        func = r.get("funcionarios") or {}
        nome = func.get("nome") or r.get("funcionario_id")
        por_func[nome] = round(por_func.get(nome, 0) + p, 2)
        por_setor[func.get("setor") or "-"] = round(por_setor.get(func.get("setor") or "-", 0) + p, 2)
    ativos = len(repo.list_ativos(setor))
    denom = ativos * dias_uteis
    taxa = round(dias_perdidos / denom * 100, 2) if denom else 0.0
    return {
        "de": str(ini), "ate": str(fim), "setor": setor,
        "dias_perdidos": round(dias_perdidos, 2),
        "dias_uteis": dias_uteis, "funcionarios_ativos": ativos,
        "taxa_absenteismo": taxa,
        "por_tipo": por_tipo,
        "por_setor": por_setor,
        "por_funcionario": dict(sorted(por_func.items(), key=lambda kv: kv[1], reverse=True)[:20]),
    }
