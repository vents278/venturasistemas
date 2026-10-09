"""Testes grade de presença — estrutura da matriz + limites (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.presencas import service


@pytest.fixture
def user_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "OPERADOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_grade_agrupa(monkeypatch):
    from app.modules.apropriacoes import repository as ap_repo
    from app.modules.presencas import repository as pr_repo

    monkeypatch.setattr(pr_repo, "list_repo", lambda *a, **k: [
        {"funcionario_id": "F1", "data": "2026-10-08", "status_codigo": "PRESENTE", "obs": "ok"}])
    monkeypatch.setattr(ap_repo, "list_repo", lambda *a, **k: [
        {"funcionario_id": "F1", "data": "2026-10-08", "os_id": "O1", "horas": 5.0, "ordens_servico": {"codigo": "OS1"}}])
    monkeypatch.setattr(service, "_nomes_funcionarios", lambda fids, setor: {"F1": {"id": "F1", "matricula": "M1", "nome": "Joao", "setor": "O"}})
    g = service.montar_grade("2026-10-01", "2026-10-08", None)
    assert g["dias"][0] == "2026-10-01" and len(g["dias"]) == 8
    cel = g["linhas"][0]["dias"]["2026-10-08"]
    assert cel["status"] == "PRESENTE" and cel["obs"] == "ok"
    assert cel["total"] == 5.0 and cel["apropriacoes"][0]["os_codigo"] == "OS1"


def test_grade_periodo_grande_400(user_client):
    r = user_client.get("/presencas/grade?de=2026-01-01&ate=2026-12-31")
    assert r.status_code == 400


def test_grade_wiring(user_client, monkeypatch):
    monkeypatch.setattr(service, "montar_grade", lambda *a, **k: {"dias": [], "linhas": []})
    r = user_client.get("/presencas/grade?de=2026-10-01&ate=2026-10-08")
    assert r.status_code == 200, r.text
