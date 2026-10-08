"""Testes ETAPA 4 — JWT local + /auth/me sem Supabase (modo payload)."""

import uuid

from fastapi.testclient import TestClient

from app.core.config import settings

# Garante segredo de teste (não mexe no .env real)
settings.JWT_SECRET = "teste-etapa4-segredo-suficientemente-longo"

from app.core.security import encode_dev_token  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.auth.dependencies import get_current_user as _gcu  # noqa: E402

app.dependency_overrides.pop(_gcu, None)

client = TestClient(app)


def test_me_com_token_valido():
    app.dependency_overrides.pop(_gcu, None)
    token = encode_dev_token(str(uuid.uuid4()), "ana@teste.com")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "ana@teste.com"


def test_me_sem_token_403():
    r = client.get("/auth/me")
    assert r.status_code in (401, 403)
