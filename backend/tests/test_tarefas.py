"""Testes ETAPA 12 — conclusão, transformação e wiring (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.tarefas import service
from app.modules.tarefas import repository as repo


@pytest.fixture
def user_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "U1", "email": "u@u.com", "perfil": "OPERADOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def gestor_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "U9", "email": "g@g.com", "perfil": "GESTOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_concluir_carimba_e_reabrir_limpa(monkeypatch):
    monkeypatch.setattr(repo, "get_repo", lambda tid: {"id": tid})
    seen = []
    monkeypatch.setattr(repo, "update_repo", lambda tid, p: seen.append(p) or {"id": tid, **p})
    from app.modules.tarefas.schemas import TarefaUpdate

    service.atualizar("T1", TarefaUpdate(status="CONCLUIDO"))
    assert seen[-1]["conclusao_em"] is not None
    service.atualizar("T1", TarefaUpdate(status="A_FAZER"))
    assert seen[-1]["conclusao_em"] is None


def test_transformar_duplicada_bloqueia(monkeypatch):
    from app.modules.pendencias import repository as pd_repo
    from app.modules.tarefas.schemas import APartirDePendenciaIn

    monkeypatch.setattr(pd_repo, "get_repo", lambda pid: {"id": pid, "tipo": "SEM_APROPRIACAO", "descricao": "x", "data_ref": "D", "prioridade": "ALTA", "responsavel_id": None})
    monkeypatch.setattr(repo, "find_por_pendencia", lambda pid: {"id": "T9"})
    with pytest.raises(ValueError):
        service.a_partir_de_pendencia("P1", APartirDePendenciaIn(), "U1")


def test_transformar_wiring(gestor_client, monkeypatch):
    monkeypatch.setattr(service, "a_partir_de_pendencia", lambda *a, **k: {"id": "T1", "titulo": "x"})
    r = gestor_client.post("/tarefas/a-partir-de-pendencia/P1", json={})
    assert r.status_code == 201, r.text


def test_mover_coluna_wiring(user_client, monkeypatch):
    monkeypatch.setattr(service, "atualizar", lambda *a, **k: {"id": "T1", "status": "EM_ANDAMENTO"})
    r = user_client.patch("/tarefas/T1", json={"status": "EM_ANDAMENTO"})
    assert r.status_code == 200, r.text
