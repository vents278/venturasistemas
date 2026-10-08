"""Testes ETAPA 10 — regra HE pura + recálculo + wiring (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.engine.regras.hora_extra import calcular_he
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.horas_extras import service


@pytest.fixture
def gestor_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "GESTOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_sex_excedente_50():
    assert calcular_he(5, False, 8.0, 10.0) == {"qtd_horas": 2.0, "percentual": 50}


def test_sex_sem_excedente_none():
    assert calcular_he(3, False, 9.0, 9.0) is None


def test_sabado_70():
    assert calcular_he(6, False, 0, 5.0) == {"qtd_horas": 5.0, "percentual": 70}


def test_domingo_100():
    assert calcular_he(0, False, 0, 4.0) == {"qtd_horas": 4.0, "percentual": 100}


def test_feriado_prevalece_100():
    assert calcular_he(6, True, 0, 5.0) == {"qtd_horas": 5.0, "percentual": 100}
    assert calcular_he(3, True, 9.0, 9.0) == {"qtd_horas": 9.0, "percentual": 100}


def test_recalcular_grava_50(gestor_client, monkeypatch):
    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.feriados import repository as fe_repo
    from app.modules.horas_extras import repository as he_repo

    monkeypatch.setattr(ap_repo, "carga_prevista", lambda *a, **k: 8.0)
    monkeypatch.setattr(ap_repo, "total_dia", lambda *a, **k: 10.0)
    monkeypatch.setattr(fe_repo, "is_feriado", lambda d: False)
    monkeypatch.setattr(he_repo, "list_repo", lambda *a, **k: [])
    monkeypatch.setattr(he_repo, "limpar_dia", lambda *a, **k: None)
    monkeypatch.setattr(he_repo, "upsert_repo", lambda f, d, q, p: {"id": "HE1", "funcionario_id": f, "data": d, "qtd_horas": q, "percentual": p})
    from app.modules.emails import service as em_service

    monkeypatch.setattr(em_service, "garantir_para_he", lambda he: he)
    r = gestor_client.post("/horas-extras/recalcular", json={"funcionario_id": "F", "data": "2026-10-09"})
    assert r.status_code == 200, r.text
    assert r.json()["percentual"] == 50
