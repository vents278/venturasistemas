"""Entrada serverless (Vercel) — importa o FastAPI de backend/ e expõe via Mangum.

A Vercel encaminha /api/* para cá; o middleware remove o prefixo /api
para casar com as rotas do app (/auth, /funcionarios, ...).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi import Request  # noqa: E402
from mangum import Mangum  # noqa: E402

from app.main import app  # noqa: E402


@app.middleware("http")
async def strip_api_prefix(request: Request, call_next):
    path = request.scope.get("path", "")
    if path == "/api":
        request.scope["path"] = "/"
    elif path.startswith("/api/"):
        stripped = path[4:]
        request.scope["path"] = stripped
        raw = request.scope.get("raw_path")
        if isinstance(raw, (bytes, bytearray)):
            request.scope["raw_path"] = bytes(raw[4:])
    return await call_next(request)


handler = Mangum(app, lifespan="off")
