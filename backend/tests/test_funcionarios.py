"""Testes ETAPA 5 — validação + wiring das rotas (Supabase mockado)."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.funcionarios import service
from app.modules.funcionarios.schemas import FuncionarioIn

client = TestClient(app)


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "ADMIN"}
    yield client
    app.dependency_overrides.pop(get_current_user, None)


def test_nome_obrigatorio():
    with pytest.raises(Exception):
        FuncionarioIn(nome="  ")


def test_supervisor_precisa_cargo_supervisao(monkeypatch):
    from app.modules.funcionarios import repository as repo

    monkeypatch.setattr(repo, "exists_matricula", lambda m: False)
    monkeypatch.setattr(repo, "get_repo", lambda fid: {"id": fid, "cargo": "Operador"})
    with pytest.raises(ValueError):
        service.criar(FuncionarioIn(nome="Joao", supervisor_id="00000000-0000-0000-0000-000000000009"), "U1")


def test_criar_aceita_supervisor_com_cargo(monkeypatch):
    from app.modules.funcionarios import repository as repo

    monkeypatch.setattr(repo, "exists_matricula", lambda m: False)
    monkeypatch.setattr(repo, "get_repo", lambda fid: {"id": fid, "cargo": "Supervisor de Produção"})
    monkeypatch.setattr(repo, "create_repo", lambda p: {"id": "F1", **p})
    out = service.criar(FuncionarioIn(nome="Joao", supervisor_id="00000000-0000-0000-0000-000000000009"), "U1")
    assert out["supervisor_id"] == "00000000-0000-0000-0000-000000000009"


def test_atualizar_valida_supervisor_apenas_se_mudar(monkeypatch):
    from app.modules.funcionarios import repository as repo
    from app.modules.funcionarios.schemas import FuncionarioUpdate

    atual = {"id": "F1", "supervisor_id": "00000000-0000-0000-0000-000000000002", "cargo": "Operador"}
    monkeypatch.setattr(repo, "get_repo", lambda fid: atual if fid == "F1" else {"id": fid, "cargo": "Operador"})
    monkeypatch.setattr(repo, "update_repo", lambda fid, p: {"id": fid, **p})
    # mantém vínculo legado sem cargo de supervisão (não revalida)
    service.atualizar("F1", FuncionarioUpdate(supervisor_id="00000000-0000-0000-0000-000000000002"), "U1")
    # troca para outro sem cargo de supervisão => bloqueia
    with pytest.raises(ValueError):
        service.atualizar("F1", FuncionarioUpdate(supervisor_id="00000000-0000-0000-0000-000000000003"), "U1")


def test_matricula_auto_quando_vazia(monkeypatch):
    from app.modules.funcionarios import repository as repo

    monkeypatch.setattr(repo, "exists_matricula", lambda m: False)
    monkeypatch.setattr(repo, "create_repo", lambda p: {"id": "F1", **p})
    out = service.criar(FuncionarioIn(nome="Joao"), "U1")
    assert out["matricula"].startswith("M") and out["admissao"] == str(date.today())


def test_ativar_limpa_treinamento(monkeypatch):
    from app.modules.funcionarios import repository as repo
    from app.modules.funcionarios.schemas import FuncionarioUpdate

    monkeypatch.setattr(repo, "get_repo", lambda fid: {"id": fid, "em_treinamento": True})
    seen = {}
    monkeypatch.setattr(repo, "update_repo", lambda fid, p: seen.setdefault("p", p) or {"id": fid})
    service.atualizar("F1", FuncionarioUpdate(ativo=True), "U1")
    assert seen["p"]["em_treinamento"] is False


def test_ficha(admin_client, monkeypatch):
    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.funcionarios import repository as repo
    from app.modules.presencas import repository as pr_repo

    monkeypatch.setattr(repo, "get_repo", lambda fid: {"id": fid, "nome": "Joao", "matricula": "M1"})
    monkeypatch.setattr(pr_repo, "list_repo", lambda *a, **k: [
        {"data": "2026-10-08", "status_codigo": "PRESENTE", "obs": ""}])
    monkeypatch.setattr(ap_repo, "list_repo", lambda *a, **k: [
        {"data": "2026-10-08", "horas": 9.0}])
    r = admin_client.get("/funcionarios/F1/ficha")
    assert r.status_code == 200, r.text
    assert r.json()["historico"][0]["horas"] == 9.0


def test_desligamento_antes_admissao():
    with pytest.raises(ValueError):
        service.validar_datas(date(2026, 5, 1), date(2026, 4, 1))


def test_listar_usa_repositorio_mockado(monkeypatch, admin_client):
    monkeypatch.setattr(
        service, "listar", lambda *a, **k: {"items": [{"id": "1", "matricula": "M1", "nome": "Joao", "admissao": "2026-01-01", "ativo": True}], "total": 1}
    )
    r = admin_client.get("/funcionarios?q=joao")
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 1


def test_criar_400_quando_duplicado(monkeypatch, admin_client):
    def boom(body, *a):
        raise ValueError("Matrícula já cadastrada")

    monkeypatch.setattr(service, "criar", boom)
    r = admin_client.post("/funcionarios", json={"matricula": "M1", "nome": "Joao", "admissao": "2026-01-01"})
    assert r.status_code == 400


def test_rota_repassa_filtro_cargo(monkeypatch, admin_client):
    seen = {}
    monkeypatch.setattr(service, "listar",
                        lambda *a, **k: seen.update({"a": a, "k": k}) or {"items": [], "total": 0})
    r = admin_client.get("/funcionarios?ativo=true&cargo=supervisor")
    assert r.status_code == 200, r.text
    assert "supervisor" in (seen["a"] + tuple(seen["k"].values()))


def test_repo_list_repo_aplica_cargo_ilike(monkeypatch):
    from app.modules.funcionarios import repository as repo

    class _FakeQuery:
        def __init__(self):
            self.calls = []

        def select(self, *a, **k):
            self.calls.append(("select", a, k)); return self

        def or_(self, *a, **k):
            self.calls.append(("or_", a, k)); return self

        def eq(self, *a, **k):
            self.calls.append(("eq", a, k)); return self

        def ilike(self, *a, **k):
            self.calls.append(("ilike", a, k)); return self

        def order(self, *a, **k):
            return self

        def range(self, *a, **k):
            return self

        def execute(self):
            return type("R", (), {"data": [], "count": 0})()

    fq = _FakeQuery()
    monkeypatch.setattr(repo, "get_supabase",
                        lambda: type("SB", (), {"table": staticmethod(lambda n: fq)})())
    repo.list_repo(ativo=True, cargo="supervisor")
    assert ("ilike", ("cargo", "%supervisor%"), {}) in fq.calls

