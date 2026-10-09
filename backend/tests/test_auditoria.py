"""Testes ETAPA 17 — auditoria registra antes/depois e nunca quebra a operação."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.shared import auditoria


@pytest.fixture
def gestor_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "U9", "email": "g@g.com", "perfil": "GESTOR"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_atualizar_apropriacao_audita(monkeypatch):
    from app.modules.apropriacoes import repository as repo
    from app.modules.apropriacoes import service

    antes = {"id": "A1", "horas": 7.0, "funcionario_id": "F", "data": "2026-10-08"}
    monkeypatch.setattr(repo, "get_repo", lambda aid: antes)
    monkeypatch.setattr(repo, "total_dia", lambda *a, **k: 0)
    monkeypatch.setattr(repo, "update_repo", lambda aid, p: {"id": aid, "horas": 9.0})
    chamadas = []
    monkeypatch.setattr(service, "audit", lambda *a, **k: chamadas.append((a, k)))
    monkeypatch.setattr(service, "distribuir", lambda *a, **k: {})
    out = service.atualizar("A1", 9.0, "U9")
    assert out["horas"] == 9.0
    assert len(chamadas) == 1 and chamadas[0][0][1] == "apropriacoes"


def test_falha_na_auditoria_nao_quebra(monkeypatch):
    from app.modules.apropriacoes import repository as repo
    from app.modules.apropriacoes import service

    monkeypatch.setattr(repo, "get_repo", lambda aid: {"id": aid, "horas": 1, "funcionario_id": "F", "data": "D"})
    monkeypatch.setattr(repo, "total_dia", lambda *a, **k: 0)
    monkeypatch.setattr(repo, "update_repo", lambda aid, p: {"id": aid, "horas": 2.0})

    def boom():
        raise RuntimeError("supabase fora")

    from app.core import supabase_client
    from app.modules.apropriacoes import service as ap_service

    monkeypatch.setattr(supabase_client, "get_supabase", boom)
    monkeypatch.setattr(ap_service, "distribuir", lambda *a, **k: {})
    assert service.atualizar("A1", 2.0, "U9")["horas"] == 2.0


def test_listar_wiring(gestor_client, monkeypatch):
    import app.modules.auditoria.router as rt

    monkeypatch.setattr(rt, "get_supabase", lambda: FakeSb())
    r = gestor_client.get("/auditoria?tabela=apropriacoes")
    assert r.status_code == 200, r.text
    assert r.json() == [{"tabela": "apropriacoes"}]


class FakeSb:
    def table(self, name):
        assert name == "historico_alteracoes"
        return self

    def select(self, *a):
        return self

    def eq(self, *a):
        return self

    def gte(self, *a):
        return self

    def lte(self, *a):
        return self

    def order(self, *a, **k):
        return self

    def limit(self, *a):
        return self

    def execute(self):
        return type("R", (), {"data": [{"tabela": "apropriacoes"}]})()
