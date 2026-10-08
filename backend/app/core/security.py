"""Segurança JWT (Supabase Auth) — ETAPA 4, rev. ES256.

Projetos novos do Supabase assinam o access_token em ES256 (chave assimétrica,
validada via JWKS público); projetos legados usam HS256 com o JWT_SECRET.
Backend aceita os dois: tenta HS256 primeiro (cobre testes locais), senão ES256.
Extrai `sub` (auth.users.id) + email/role. Senhas nunca passam pelo nosso banco.
"""

import time
import urllib.request
from functools import lru_cache

import jwt
from fastapi import HTTPException, status

from app.core.config import settings


@lru_cache(maxsize=1)
def _jwks_keys() -> list:
    if not settings.SUPABASE_URL:
        return []
    url = settings.SUPABASE_URL.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            import json

            return json.load(r).get("keys", [])
    except Exception:
        return []


def _decode_es256(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    for key in _jwks_keys():
        if key.get("kid") == header.get("kid"):
            public_key = jwt.algorithms.ECAlgorithm.from_jwk(key)
            return jwt.decode(
                token,
                public_key,
                algorithms=["ES256"],
                audience="authenticated",
                options={"require": ["sub", "exp"]},
            )
    raise jwt.InvalidTokenError("kid fora do JWKS do projeto")


def decode_token(token: str) -> dict:
    if settings.JWT_SECRET and not settings.JWT_SECRET.startswith("dev-only"):
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"require": ["sub", "exp"]},
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            pass  # tenta ES256 abaixo
    try:
        return _decode_es256(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Token inválido: {exc}")


def encode_dev_token(sub: str, email: str = "dev@teste.com") -> str:
    """Apenas para testes locais — nunca expor em produção."""
    return jwt.encode(
        {
            "sub": sub,
            "email": email,
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )
