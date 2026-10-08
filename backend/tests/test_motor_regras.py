"""Testes ETAPA 9 — regra pura + wiring do motor (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.engine.regras.apropriacao import avaliar_apropriacao
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.engine import motor_regras


@pytest.fixture
def gestor_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "GESTOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_ok_quando_total_igual_carga():
    assert avaliar_apropriacao("F", "2026-10-08", True, True, 9.0, 9.0) is None


def test_pendencia_1h():
    a = avaliar_apropriacao("F", "2026-10-08", True, True, 9.0, 8.0)
    assert a["tipo"] == "APROPRIACAO_INCOMPLETA" and a["horas_faltantes"] == 1.0


def test_sem_apropriacao():
    a = avaliar_apropriacao("F", "2026-10-08", True, True, 9.0, 0)
    assert a["tipo"] == "SEM_APROPRIACAO"


def test_folga_nao_cobra():
    assert avaliar_apropriacao("F", "2026-10-08", True, False, 9.0, 0) is None


def test_sem_carga_nao_cobra():
    assert avaliar_apropriacao("F", "2026-10-08", True, True, 0, 0) is None


def test_avaliar_dia_wiring(gestor_client, monkeypatch):
    from app.modules.presencas import repository as pr_repo
    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.feriados import repository as fe_repo

    monkeypatch.setattr(pr_repo, "list_repo", lambda *a, **k: [{"funcionario_id": "F1", "status_codigo": "PRESENTE"}])
    monkeypatch.setattr(pr_repo, "get_status", lambda c: {"codigo": c, "exige_apropriacao": True})
    monkeypatch.setattr(ap_repo, "carga_prevista", lambda *a, **k: 9.0)
    monkeypatch.setattr(ap_repo, "total_dia", lambda *a, **k: 7.0)
    monkeypatch.setattr(ap_repo, "list_repo", lambda *a, **k: [])
    monkeypatch.setattr(fe_repo, "is_feriado", lambda d: False)
    r = gestor_client.post("/motor/avaliar-dia", json={"data": "2026-10-08"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["avaliados"] == 1 and len(body["achados"]) == 1
    assert body["achados"][0]["horas_faltantes"] == 2.0
