"""Testes ETAPA 16 — bytes de cada formato + erros (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.relatorios import service


@pytest.fixture
def user_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "OPERADOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_csv_tem_cabecalho(monkeypatch, user_client):
    from app.modules.funcionarios import repository as r

    monkeypatch.setattr(r, "list_repo", lambda *a, **k: {"items": [{"matricula": "M1", "nome": "Joao", "cargo": "OP", "setor": "O", "empresa": "E", "admissao": "2026-01-01", "ativo": True}], "total": 1})
    req = user_client.get("/relatorios/funcionarios.csv")
    assert req.status_code == 200, req.text
    assert req.text.startswith("\ufeffmatricula,nome") and "Joao" in req.text


def test_xlsx_magic(monkeypatch, user_client):
    from app.modules.pendencias import repository as r

    monkeypatch.setattr(r, "list_repo", lambda *a, **k: [])
    monkeypatch.setattr(service, "_nomes", lambda ids: {})
    req = user_client.get("/relatorios/pendencias.xlsx")
    assert req.status_code == 200
    assert req.content[:2] == b"PK"


def test_pdf_magic(monkeypatch):
    from app.modules.tarefas import repository as r

    monkeypatch.setattr(r, "list_repo", lambda *a, **k: [])
    monkeypatch.setattr(service, "_nomes", lambda ids: {})
    data, mime, nome = service.gerar("tarefas", "pdf", {})
    assert data[:4] == b"%PDF" and nome == "tarefas.pdf"


def test_recurso_invalido_404(user_client):
    assert user_client.get("/relatorios/xxx.csv").status_code == 404


def test_formato_invalido_400(user_client):
    assert user_client.get("/relatorios/tarefas.doc").status_code in (400, 404)
