"""Testes ETAPA 8 — teto 24h, vínculos e wiring (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.apropriacoes import repository as repo
from app.modules.apropriacoes import service
from app.modules.auth.dependencies import get_current_user


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "ADMIN"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_teto_24h(monkeypatch):
    monkeypatch.setattr(repo, "total_dia", lambda *a, **k: 23.0)
    with pytest.raises(ValueError):
        service._checar_teto("F", "2026-10-08", 2.0)


def test_os_inexistente(monkeypatch):
    monkeypatch.setattr(repo, "get_funcionario", lambda fid: {"id": fid, "ativo": True, "desligamento": None})
    monkeypatch.setattr(repo, "get_os", lambda oid: None)
    with pytest.raises(KeyError):
        service._validar_vinculos("F", "2026-10-08", "OS_X")


def test_saldo_wiring(admin_client, monkeypatch):
    monkeypatch.setattr(service, "saldo", lambda *a, **k: {"carga_prevista": 9, "total_apropriado": 8, "saldo": -1})
    r = admin_client.get("/apropriacoes/saldo?funcionario_id=F&data=2026-10-08")
    assert r.status_code == 200, r.text
    assert r.json()["saldo"] == -1


def test_lote_teto_wiring(admin_client, monkeypatch):
    monkeypatch.setattr(repo, "get_funcionario", lambda fid: {"id": fid, "ativo": True, "desligamento": None})
    monkeypatch.setattr(repo, "get_os", lambda oid: {"id": oid})
    monkeypatch.setattr(repo, "total_dia", lambda *a, **k: 0)
    monkeypatch.setattr(repo, "upsert_repo", lambda p: p)
    monkeypatch.setattr(repo, "carga_prevista", lambda *a, **k: 9.0)
    r = admin_client.post("/apropriacoes/lote", json={
        "funcionario_id": "00000000-0000-0000-0000-000000000001",
        "data": "2026-10-08",
        "itens": [
            {"os_id": "00000000-0000-0000-0000-000000000011", "horas": 20},
            {"os_id": "00000000-0000-0000-0000-000000000012", "horas": 5},
        ],
    })
    assert r.status_code == 400  # 25h > teto
