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
