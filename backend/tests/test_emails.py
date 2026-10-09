"""Testes ETAPA 13 — idempotência do e-mail + envio resolve pendência (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.emails import repository as em_repo
from app.modules.emails import service
from app.modules.pendencias import repository as pd_repo


@pytest.fixture
def gestor_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "GESTOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def _he():
    return {"id": "HE1", "funcionario_id": "F1", "data": "2026-10-10", "qtd_horas": 2.0, "percentual": 70}


def test_enviado_nao_recria(monkeypatch):
    monkeypatch.setattr(em_repo, "find_por_he", lambda hid: {"id": "E1", "status": "ENVIADO"})
    monkeypatch.setattr(service, "_funcionario", lambda fid: {"nome": "Joao", "matricula": "M1"})
    monkeypatch.setattr(em_repo, "create_repo", lambda p: (_ for _ in ()).throw(AssertionError("não deve criar")))
    assert service.garantir_para_he(_he())["id"] == "E1"


def test_pendente_atualiza_sem_duplicar(monkeypatch):
    monkeypatch.setattr(em_repo, "find_por_he", lambda hid: {"id": "E1", "status": "PENDENTE"})
    monkeypatch.setattr(service, "_funcionario", lambda fid: {"nome": "Joao", "matricula": "M1"})
    monkeypatch.setattr(service, "_ordens_do_dia", lambda *a, **k: "100")
    monkeypatch.setattr(em_repo, "update_repo", lambda eid, p: {"id": eid, **p})
    monkeypatch.setattr(em_repo, "create_repo", lambda p: (_ for _ in ()).throw(AssertionError("não deve criar")))
    out = service.garantir_para_he(_he())
    assert out["id"] == "E1" and "70%" in out["assunto"]


def test_enviar_sem_smtp_registra_erro(monkeypatch, gestor_client):
    settings.SMTP_HOST = ""
    monkeypatch.setattr(em_repo, "get_repo", lambda eid: {"id": eid, "destinatario": "rh@x.com", "assunto": "a", "corpo": "c", "status": "PENDENTE"})
    marcadas = []
    monkeypatch.setattr(em_repo, "update_repo", lambda eid, p: marcadas.append(p) or {"id": eid, **p})
    r = gestor_client.post("/emails/E1/enviar", json={})
    assert r.status_code == 400, r.text
    assert marcadas and marcadas[0]["status"] == "ERRO"


def test_enviar_ok_resolve_pendencia(monkeypatch, gestor_client):
    settings.SMTP_HOST = "smtp.teste.com"
    monkeypatch.setattr(em_repo, "get_repo", lambda eid: {"id": eid, "destinatario": "rh@x.com", "assunto": "a", "corpo": "c", "status": "PENDENTE"})
    monkeypatch.setattr(service, "_smtp_send", lambda *a, **k: None)
    monkeypatch.setattr(em_repo, "update_repo", lambda eid, p: {"id": eid, "destinatario": "rh@x.com", **p})
    monkeypatch.setattr(pd_repo, "list_repo", lambda *a, **k: [{"id": "P1", "registro_id": "E1"}])
    resolvidas = []
    monkeypatch.setattr(pd_repo, "update_repo", lambda pid, p: resolvidas.append(pid) or {"id": pid})
    r = gestor_client.post("/emails/E1/enviar", json={})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ENVIADO" and resolvidas == ["P1"]
    settings.SMTP_HOST = ""
