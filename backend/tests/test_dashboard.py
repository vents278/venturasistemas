"""Testes ETAPA 15 — agregação com repositórios mockados."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.dashboard import service


@pytest.fixture
def user_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "OPERADOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_resumo_soma(monkeypatch, user_client):
    from app.modules.absenteismo import service as ab_service
    from app.modules.emails import repository as em_repo
    from app.modules.funcionarios import repository as fn_repo
    from app.modules.horas_extras import repository as he_repo
    from app.modules.pendencias import repository as pd_repo
    from app.modules.presencas import repository as pr_repo
    from app.modules.tarefas import repository as ta_repo

    monkeypatch.setattr(pr_repo, "list_repo", lambda *a, **k: [
        {"status_codigo": "PRESENTE"}, {"status_codigo": "DESLOCADO"}, {"status_codigo": "FALTA"}])
    monkeypatch.setattr(fn_repo, "list_repo", lambda *a, **k: {"items": [], "total": 5})
    monkeypatch.setattr(pd_repo, "list_repo", lambda *a, **k: [
        {"tipo": "SEM_APROPRIACAO"}, {"tipo": "EMAIL_HE_PENDENTE"}])
    monkeypatch.setattr(he_repo, "list_repo", lambda *a, **k: [{"qtd_horas": 2.5}])
    monkeypatch.setattr(em_repo, "list_repo", lambda *a, **k: [{}, {}])
    monkeypatch.setattr(ta_repo, "list_repo", lambda *a, **k: [
        {"prazo": "2026-01-01", "status": "A_FAZER"},
        {"prazo": "2026-10-08", "status": "A_FAZER"},
        {"prazo": "2026-10-08", "status": "CONCLUIDO"},
    ])
    monkeypatch.setattr(ab_service, "indicadores", lambda *a, **k: {"taxa_absenteismo": 3.5})

    r = user_client.get("/dashboard/resumo?data=2026-10-08")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["presentes"]["valor"] == 2 and d["sem_presenca"]["valor"] == 2
    assert d["apropriacoes_pendentes"]["valor"] == 1 and d["emails_pendentes"]["valor"] == 2
    assert d["he_dia_horas"]["valor"] == 2.5
    assert d["tarefas_vencidas"]["valor"] == 1 and d["tarefas_para_hoje"]["valor"] == 1
    assert d["taxa_absenteismo_30d"]["valor"] == 3.5
    assert service.resumo  # agregador central existe
