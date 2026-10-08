"""Ponto de entrada FastAPI — ETAPA 4 (auth)."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.absenteismo.router import router as absenteismo_router
from app.modules.ai.router import router as ai_router
from app.modules.apropriacoes.router import router as apropriacoes_router
from app.modules.auditoria.router import router as auditoria_router
from app.modules.auth.router import router as auth_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.emails.router import router as emails_router
from app.modules.feriados.router import router as feriados_router
from app.modules.funcionarios.router import router as funcionarios_router
from app.modules.horas_extras.router import router as he_router
from app.modules.jornadas.router import router as jornadas_router
from app.modules.motor.router import router as motor_router
from app.modules.ordens_servico.router import router as os_router
from app.modules.pendencias.router import router as pendencias_router
from app.modules.presencas.router import router as presencas_router
from app.modules.relatorios.router import router as relatorios_router
from app.modules.tarefas.router import router as tarefas_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ERP Estacao de Trabalho", version="0.1.0-etapa18")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringir em producao
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(funcionarios_router)
app.include_router(jornadas_router)
app.include_router(presencas_router)
app.include_router(os_router)
app.include_router(apropriacoes_router)
app.include_router(motor_router)
app.include_router(feriados_router)
app.include_router(he_router)
app.include_router(pendencias_router)
app.include_router(tarefas_router)
app.include_router(emails_router)
app.include_router(absenteismo_router)
app.include_router(dashboard_router)
app.include_router(relatorios_router)
app.include_router(auditoria_router)
app.include_router(ai_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "env": settings.ENV}


@app.get("/")
def root() -> dict:
    return {"app": "ERP Estacao de Trabalho", "etapa": 18, "docs": "/docs"}
