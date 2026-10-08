"""Testes ETAPA 7 — regras de vínculo + wiring (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.presencas import service
from app.modules.presencas import repository as repo


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "ADMIN"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_inativo_nao_pode_presente(monkeypatch):
    monkeypatch.setattr(repo, "get_status", lambda c: {"codigo": c})
    with pytest.raises(ValueError):
        service._validar({"ativo": False, "desligamento": None}, "2026-10-08", "PRESENTE")


def test_data_apos_desligamento_bloqueia(monkeypatch):
    monkeypatch.setattr(repo, "get_status", lambda c: {"codigo": c})
    with pytest.raises(ValueError):
        service._validar({"ativo": True, "desligamento": "2026-01-01"}, "2026-10-08", "FOLGA")


def test_snapshot_usa_jornada_do_funcionario(monkeypatch):
    monkeypatch.setattr(repo, "get_status", lambda c: {"codigo": c})
    monkeypatch.setattr(repo, "get_funcionario", lambda fid: {"id": fid, "ativo": True, "desligamento": None, "jornada_id": "JJJ"})
    p = service.montar_payload("FFF", "2026-10-08", "PRESENTE", None, None)
    assert p["jornada_id"] == "JJJ"


def test_lote_wiring(admin_client, monkeypatch):
    monkeypatch.setattr(service, "registrar_lote", lambda *a, **k: {"data": "2026-10-08", "ok": 2, "erros": []})
    r = admin_client.post("/presencas/lote", json={"data": "2026-10-08", "itens": [
        {"funcionario_id": "00000000-0000-0000-0000-000000000001", "status_codigo": "PRESENTE"},
        {"funcionario_id": "00000000-0000-0000-0000-000000000002", "status_codigo": "FOLGA"},
    ]})
    assert r.status_code == 201, r.text
    assert r.json()["ok"] == 2
