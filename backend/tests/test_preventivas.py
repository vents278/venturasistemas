"""Testes preventivas — status derivado, duplicidade e pendências (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.pendencias import repository as pd_repo
from app.modules.preventivas import repository as repo
from app.modules.preventivas import service


@pytest.fixture
def gestor_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "GESTOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def _pf(programado=True, compareceu=False, os_completa=False):
    return {"programado": programado, "compareceu": compareceu, "os_completa": os_completa}


# ---------------- status individual ----------------
def test_status_individual_transicoes():
    hoje = "2026-10-15"
    assert service.status_funcionario(_pf(), [], "2026-10-15", "2026-10-14") == "PROGRAMADO"
    assert service.status_funcionario(_pf(), [], "2026-10-15", "2026-10-16") == "NAO_COMPARECEU"
    pres = _pf(compareceu=True)
    assert service.status_funcionario(pres, [], hoje, hoje) == "AGUARDANDO_OS"
    assert service.status_funcionario({**pres, "os_completa": True}, [], hoje, hoje) == "REGULARIZADO"
    assert service.status_funcionario(pres, [{"recebida": False}], hoje, hoje) == "OS_PENDENTE"
    assert service.status_funcionario(pres, [{"recebida": True}, {"recebida": False}], hoje, hoje) == "PARCIALMENTE_REGULARIZADO"
    assert service.status_funcionario(pres, [{"recebida": True}], hoje, hoje) == "REGULARIZADO"


# ---------------- status da preventiva ----------------
def _linha(compareceu=True, programado=True, os_total=1, os_recebidas=1, os_completa=True, status="REGULARIZADO"):
    return {"compareceu": compareceu, "programado": programado, "os_total": os_total,
            "os_recebidas": os_recebidas, "os_completa": os_completa, "status": status}


def test_status_preventiva_concluida_so_com_tudo_regularizado():
    prev = {"status": "PROGRAMADA"}
    assert service.status_preventiva(prev, [_linha()]) == "CONCLUIDA"
    # pendente => parcial
    assert service.status_preventiva(prev, [_linha(os_total=2, os_recebidas=1, status="PARCIALMENTE_REGULARIZADO")]) == "PARCIALMENTE_CONCLUIDA"
    # sem recebimento => aguardando OS
    assert service.status_preventiva(prev, [_linha(os_total=2, os_recebidas=0, status="OS_PENDENTE")]) == "AGUARDANDO_OS"
    # compareceu mas sem OS e sem confirmação => aguardando OS
    assert service.status_preventiva(prev, [_linha(os_total=0, os_recebidas=0, os_completa=False, status="AGUARDANDO_OS")]) == "AGUARDANDO_OS"
    # ninguém presente => programada
    assert service.status_preventiva(prev, [_linha(compareceu=False, status="NAO_COMPARECEU")]) == "PROGRAMADA"
    # cancelada nunca é sobrescrita
    assert service.status_preventiva({"status": "CANCELADA"}, [_linha()]) == "CANCELADA"


def test_status_manual_tem_precedencia_sobre_calculo():
    manual = {"status": "EM_ANDAMENTO", "status_manual": True}
    assert service.status_preventiva(manual, [_linha()]) == "EM_ANDAMENTO"
    automatico = {"status": "EM_ANDAMENTO", "status_manual": False}
    assert service.status_preventiva(automatico, [_linha()]) == "CONCLUIDA"
    cancelada = {"status": "CANCELADA", "status_manual": True}
    assert service.status_preventiva(cancelada, [_linha()]) == "CANCELADA"


def test_atualizar_define_e_limpa_status_manual(monkeypatch):
    updates = []
    monkeypatch.setattr(repo, "get_repo", lambda pid: {
        "id": pid, "status": "PROGRAMADA", "status_manual": False, "data": "2026-10-15"})
    monkeypatch.setattr(repo, "list_funcionarios", lambda pid: [])
    monkeypatch.setattr(repo, "list_os", lambda pid: [])
    monkeypatch.setattr(repo, "update_repo", lambda pid, p: updates.append(p) or {"id": pid})
    monkeypatch.setattr(service, "montar_detalhe", lambda pid: {"ok": True})
    monkeypatch.setattr(service, "audit", lambda *a, **k: None)

    class Body:
        def model_dump(self, exclude_unset=True):
            return {"status": "CONCLUIDA"}

    service.atualizar("P1", Body())
    assert updates[0]["status"] == "CONCLUIDA" and updates[0]["status_manual"] is True

    class BodyAuto:
        def model_dump(self, exclude_unset=True):
            return {"status": "AUTO"}

    service.atualizar("P1", BodyAuto())
    assert updates[1]["status_manual"] is False
    assert updates[1]["status"] == "PROGRAMADA"  # derivado, sem funcionários presentes


# ---------------- duplicidades ----------------
def test_adicionar_funcionario_duplicado(monkeypatch):
    monkeypatch.setattr(repo, "get_repo", lambda pid: {"id": pid})
    monkeypatch.setattr(repo, "get_funcionario", lambda fid: {"id": fid})
    monkeypatch.setattr(repo, "find_funcionario", lambda pid, fid: {"id": "EXISTE"})

    class In:
        funcionario_id = "00000000-0000-0000-0000-000000000001"
    with pytest.raises(ValueError):
        service.adicionar_funcionario("P1", In())


def test_adicionar_os_duplicada(monkeypatch):
    monkeypatch.setattr(repo, "get_funcionario_row", lambda pf: {"id": pf, "preventiva_id": "P1"})
    monkeypatch.setattr(repo, "find_os_dup", lambda pf, codigo: {"id": "OSEXISTE"})

    class In:
        os_codigo = "1054"
        os_id = None
    with pytest.raises(ValueError):
        service.adicionar_os("P1", "PF1", In())


def test_adicionar_os_marca_presenca_e_recebimento(monkeypatch):
    criados, updates, audits = [], [], []
    monkeypatch.setattr(repo, "get_funcionario_row", lambda pf: {"id": pf, "preventiva_id": "P1", "funcionario_id": "F1", "compareceu": False})
    monkeypatch.setattr(repo, "find_os_dup", lambda pf, codigo: None)
    monkeypatch.setattr(repo, "achar_os_por_codigo", lambda codigo: {"id": "OSID-1"})
    monkeypatch.setattr(repo, "get_os_cadastrada", lambda oid: {"id": oid})
    monkeypatch.setattr(repo, "create_os", lambda p: criados.append(p) or {"id": "ROW1"})
    monkeypatch.setattr(repo, "update_funcionario", lambda pf, p: updates.append((pf, p)) or {})
    monkeypatch.setattr(service, "montar_detalhe", lambda pid: {"ok": True})
    monkeypatch.setattr(service, "recalcular", lambda pid: {})
    monkeypatch.setattr(service, "audit", lambda *a, **k: audits.append(a))

    class In:
        os_codigo = "1054"
        os_id = None
        descricao = "Bomba"
        data_execucao = None
        horas = 3
        recebida = False
        observacoes = None
        anexo_url = None
    service.adicionar_os("P1", "PF1", In(), usuario_id="U1")
    assert criados[0]["os_codigo"] == "1054"
    assert criados[0]["os_id"] == "OSID-1"  # vinculada automaticamente pelo código
    assert updates and updates[0][1] == {"compareceu": True}


# ---------------- pendências ----------------
def test_sincronizar_pendencias_cria_e_resolve(monkeypatch):
    prev = {"id": "P1", "data": "2026-10-15", "area": "Filtragem"}
    funcs = [{"id": "PF1", "funcionario_id": "F1", "compareceu": True, "os_completa": False,
              "funcionarios": {"nome": "João"}}]
    oss = [
        {"id": "O1", "preventiva_funcionario_id": "PF1", "os_id": None, "os_codigo": "1054", "horas": 3, "recebida": True},
        {"id": "O2", "preventiva_funcionario_id": "PF1", "os_id": None, "os_codigo": "1055", "horas": 4, "recebida": False},
    ]
    monkeypatch.setattr(repo, "get_repo", lambda pid: prev)
    monkeypatch.setattr(repo, "list_funcionarios", lambda pid: funcs)
    monkeypatch.setattr(repo, "list_os", lambda pid: oss)
    abertas = {}
    monkeypatch.setattr(pd_repo, "find_aberta_reg", lambda t, f, d, r: abertas.get((t, r)))
    monkeypatch.setattr(pd_repo, "create_repo", lambda p: abertas.__setitem__((p["tipo"], p["registro_id"]), p) or p)
    monkeypatch.setattr(pd_repo, "update_repo", lambda i, p: abertas.__setitem__(i, p) or p)
    monkeypatch.setattr(pd_repo, "list_abertas_por_data", lambda d, tipos: [])

    out = service.sincronizar_pendencias("P1")
    assert out["pendencias_abertas"] == 1
    assert ("PREVENTIVA_OS_PENDENTE", "PF1") in abertas

    # agora tudo recebido => resolve
    oss[1]["recebida"] = True
    monkeypatch.setattr(pd_repo, "list_abertas_por_data",
                        lambda d, tipos: [{"id": "PD1", "registro_id": "PF1", "registro_tipo": "preventiva_funcionarios",
                                           "tipo": "PREVENTIVA_OS_PENDENTE"}])
    resolvidas = []
    monkeypatch.setattr(pd_repo, "update_repo",
                        lambda i, p: resolvidas.append(p) or {**p, "id": i})
    out = service.sincronizar_pendencias("P1")
    assert out["pendencias_abertas"] == 0
    assert any(p.get("status") == "RESOLVIDA" for p in resolvidas)


def test_rota_criar_preventiva_wiring(gestor_client, monkeypatch):
    monkeypatch.setattr(service, "criar", lambda *a, **k: {"preventiva": {"id": "P1"}, "funcionarios": [], "agregados": {}})
    r = gestor_client.post("/preventivas", json={
        "data": "2026-10-15", "area": "Filtragem", "descricao": "Troca de filtros"})
    assert r.status_code == 201, r.text
    assert r.json()["preventiva"]["id"] == "P1"
