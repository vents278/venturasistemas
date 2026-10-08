"""Testes ETAPA 6 — meia-noite, carga e wiring (Supabase mockado)."""

from datetime import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.jornadas import service
from app.modules.jornadas.schemas import HorarioIn


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "x", "email": "a@a.com", "perfil": "ADMIN"}
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_atravessa_consistente():
    assert service.atravessa_esperado(time(23, 0), time(7, 20)) is True
    assert service.atravessa_esperado(time(7, 0), time(17, 0)) is False


def test_carga_maior_que_duracao_rejeita():
    with pytest.raises(ValueError):
        service.validar_horario(time(7, 0), time(8, 0), 5.0, False)


def test_flag_inconsistente_rejeita():
    with pytest.raises(ValueError):
        service.validar_horario(time(23, 0), time(7, 20), 7.33, False)
    with pytest.raises(ValueError):
        service.validar_horario(time(7, 0), time(17, 0), 9.0, True)


def test_seed_adm_e_noturno_passam():
    service.validar_horario(time(7, 0), time(17, 0), 9.0, False)
    service.validar_horario(time(7, 0), time(16, 0), 8.0, False)
    service.validar_horario(time(15, 0), time(23, 20), 7.33, False)
    service.validar_horario(time(23, 0), time(7, 20), 7.33, True)


def test_criar_horario_400_quando_service_falha(admin_client, monkeypatch):
    def boom(jid, body):
        raise ValueError("Dia da semana já cadastrado nesta jornada")

    monkeypatch.setattr(service, "criar_horario", boom)
    r = admin_client.post(
        "/jornadas/xxx/horarios",
        json={"dia_semana": 1, "inicio": "07:00", "fim": "17:00", "carga_horas": 9, "atravessa_meia_noite": False},
    )
    assert r.status_code == 400


def test_excluir_bloqueada_em_uso(admin_client, monkeypatch):
    monkeypatch.setattr(service, "excluir", lambda jid, *a, **k: (_ for _ in ()).throw(ValueError("em uso")))
    r = admin_client.delete("/jornadas/xxx")
    assert r.status_code == 400
