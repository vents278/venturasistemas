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


def test_cpf_invalido():
    with pytest.raises(Exception):
        FuncionarioIn(matricula="1", nome="Joao", admissao=date(2026, 1, 1), cpf="11111111111")


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
    def boom(body):
        raise ValueError("Matrícula ou CPF já cadastrado")

    monkeypatch.setattr(service, "criar", boom)
    r = admin_client.post("/funcionarios", json={"matricula": "M1", "nome": "Joao", "admissao": "2026-01-01"})
    assert r.status_code == 400
