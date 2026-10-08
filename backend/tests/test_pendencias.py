"""Testes ETAPA 11 — idempotência, auto-resolve e wiring (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.engine import motor_pendencias
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.pendencias import repository as pd_repo


@pytest.fixture
def gestor_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "GESTOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def _achado():
    return {"tipo": "APROPRIACAO_INCOMPLETA", "funcionario_id": "F1", "data_ref": "2026-10-08",
            "descricao": "x", "horas_faltantes": 1.0, "origem_regra": "motor_regras.apropriacao"}


def test_idempotente_atualiza_em_vez_de_duplicar(monkeypatch):
    calls = {}
    monkeypatch.setattr(pd_repo, "find_aberta", lambda *a, **k: {"id": "P1"})
    monkeypatch.setattr(pd_repo, "update_repo", lambda pid, p: calls.setdefault("upd", (pid, p)) or {"id": pid})
    monkeypatch.setattr(pd_repo, "create_repo", lambda p: (_ for _ in ()).throw(AssertionError("não deve criar")))
    out = motor_pendencias.gerar_pendencias([_achado()])
    assert len(out) == 1 and calls["upd"][0] == "P1"


def test_hora_extra_nao_vira_pendencia(monkeypatch):
    monkeypatch.setattr(pd_repo, "create_repo", lambda p: (_ for _ in ()).throw(AssertionError("não deve criar")))
    assert motor_pendencias.gerar_pendencias([{"tipo": "HORA_EXTRA", "funcionario_id": "F", "data_ref": "D"}]) == []


def test_sincronizar_resolve_normalizadas(monkeypatch, gestor_client):
    from app.engine import motor_regras

    monkeypatch.setattr(motor_regras, "avaliar_dia", lambda d: {"data": d, "avaliados": 2, "achados": [_achado()]})
    monkeypatch.setattr(motor_pendencias, "gerar_pendencias", lambda a: [{"id": "P1"}])
    monkeypatch.setattr(pd_repo, "list_abertas_por_data", lambda d, t: [
        {"id": "P1", "tipo": "APROPRIACAO_INCOMPLETA", "funcionario_id": "F1"},
        {"id": "P2", "tipo": "SEM_APROPRIACAO", "funcionario_id": "F9"},
    ])
    resolvidas = []
    monkeypatch.setattr(pd_repo, "update_repo", lambda pid, p: resolvidas.append(pid) or {"id": pid})
    r = gestor_client.post("/pendencias/sincronizar-dia", json={"data": "2026-10-08"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["geradas"] == 1 and body["resolvidas"] == 1 and resolvidas == ["P2"]
