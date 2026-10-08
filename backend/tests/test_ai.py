"""Testes ETAPA 18 — resumo e intenções (serviços mockados, sem I/O)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.ai import service
from app.modules.auth.dependencies import get_current_user


@pytest.fixture
def user_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "OPERADOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_resumo_dia(monkeypatch, user_client):
    from app.modules.dashboard import service as db
    from app.modules.pendencias import service as pd

    monkeypatch.setattr(db, "resumo", lambda d: {
        "presentes": {"valor": 3}, "sem_presenca": {"valor": 1}, "faltas": {"valor": 0},
        "he_dia_horas": {"valor": 2.5}, "tarefas_vencidas": {"valor": 1},
        "tarefas_para_hoje": {"valor": 0}, "x": {"valor": 0}})
    monkeypatch.setattr(pd, "listar", lambda *a, **k: [{"descricao": "Joao 1h"}])
    r = user_client.post("/ai/resumo-dia", json={"data": "2026-10-08"})
    assert r.status_code == 200, r.text
    assert "3 presentes" in r.json()["resumo"]


def test_pergunta_desconhecida_lista_capacidades(user_client):
    r = user_client.post("/ai/perguntar", json={"pergunta": "qual o sentido da vida?"})
    assert r.status_code == 200 and "pendências" in r.json()["resposta"]


def test_pergunta_he(monkeypatch, user_client):
    from app.modules.horas_extras import service as he

    monkeypatch.setattr(he, "listar", lambda *a, **k: [{"qtd_horas": 2.0}])
    r = user_client.post("/ai/perguntar", json={"pergunta": "horas extras da semana?"})
    assert "2.0h" in r.json()["resposta"]
    assert service.perguntar  # contrato estável p/ futuro LLMProvider
