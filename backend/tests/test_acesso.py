"""Testes multi-empresa: matriz de acesso + wiring 403 (Supabase mockado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.shared import acesso


@pytest.fixture
def operador_restrito():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "U1", "email": "u@u.com", "perfil": "OPERADOR",
        "empresas": ["E1"], "modulos": ["dashboard", "presencas"]}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_pode_modulo_default_aberto():
    assert acesso.pode_modulo({"perfil": "OPERADOR", "modulos": []}, "tarefas") is True
    assert acesso.pode_modulo({"perfil": "ADMIN"}, "usuarios") is True
    assert acesso.pode_modulo({"perfil": "OPERADOR", "modulos": ["presencas"]}, "tarefas") is False


def test_empresa_no_escopo():
    u = {"perfil": "OPERADOR", "empresas": ["E1"]}
    assert acesso.empresa_no_escopo(u, "E1") is True
    assert acesso.empresa_no_escopo(u, "E9") is False
    assert acesso.empresa_no_escopo(u, None, "E1") is True
    assert acesso.empresa_no_escopo({"perfil": "OPERADOR", "empresas": []}, "E9") is True


def test_modulo_negado_403(operador_restrito):
    r = operador_restrito.get("/tarefas")
    assert r.status_code == 403


def test_empresa_fora_do_escopo_403(operador_restrito):
    r = operador_restrito.get("/presencas/grade?de=2026-10-01&ate=2026-10-08&empresa_id=E9")
    assert r.status_code == 403


def test_usuarios_exige_admin(operador_restrito):
    from app.modules.auth.dependencies import require_admin

    assert require_admin  # módulo existe; rota montada sob require_admin no main
    r = operador_restrito.get("/usuarios")
    assert r.status_code == 403
