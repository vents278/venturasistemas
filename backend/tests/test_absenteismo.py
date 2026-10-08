"""Testes ETAPA 14 — peso meio período, taxa e wiring (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.absenteismo import service
from app.modules.auth.dependencies import get_current_user


@pytest.fixture
def user_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "OPERADOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_peso_meio_periodo():
    assert service.peso("MANHA") == 0.5
    assert service.peso("TARDE") == 0.5
    assert service.peso("INTEGRAL") == 1.0


def test_indicadores_taxa(monkeypatch):
    from app.modules.absenteismo import repository as repo
    from app.modules.feriados import repository as fe_repo

    monkeypatch.setattr(fe_repo, "list_repo", lambda *a, **k: [])
    monkeypatch.setattr(repo, "list_repo", lambda *a, **k: [
        {"periodo": "INTEGRAL", "tipos_ausencia": {"codigo": "FALTA"}, "funcionarios": {"nome": "Joao", "setor": "OBRA"}, "funcionario_id": "F1"},
        {"periodo": "MANHA", "tipos_ausencia": {"codigo": "ATESTADO"}, "funcionarios": {"nome": "Ana", "setor": "OBRA"}, "funcionario_id": "F2"},
    ])
    monkeypatch.setattr(repo, "list_ativos", lambda *a, **k: [{"id": "F1"}, {"id": "F2"}])
    # 2026-10-05 (seg) a 2026-10-09 (sex): 5 dias úteis, 2 ativos → denom 10; perdidos 1.5 → 15%
    out = service.indicadores("2026-10-05", "2026-10-09", None)
    assert out["dias_perdidos"] == 1.5 and out["taxa_absenteismo"] == 15.0
    assert out["por_tipo"] == {"FALTA": 1.0, "ATESTADO": 0.5}


def test_indicadores_wiring(user_client, monkeypatch):
    monkeypatch.setattr(service, "indicadores", lambda *a, **k: {"taxa_absenteismo": 0})
    r = user_client.get("/absenteismo/indicadores?de=2026-10-01&ate=2026-10-08")
    assert r.status_code == 200, r.text
