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
from app.modules.empresas.router import router as empresas_router
from app.modules.feriados.router import router as feriados_router
from app.modules.funcionarios.router import router as funcionarios_router
from app.modules.horas_extras.router import router as he_router
from app.modules.jornadas.router import router as jornadas_router
from app.modules.motor.router import router as motor_router
from app.modules.ordens_servico.router import router as os_router
from app.modules.pendencias.router import router as pendencias_router
from app.modules.presencas.router import router as presencas_router
from app.modules.preventivas.router import router as preventivas_router
from app.modules.relatorios.router import router as relatorios_router
from app.modules.tarefas.router import router as tarefas_router
from app.modules.usuarios.router import router as usuarios_router

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

from fastapi import Depends

from app.modules.auth.dependencies import require_admin, require_modulo

app.include_router(auth_router)
app.include_router(funcionarios_router, dependencies=[Depends(require_modulo("funcionarios"))])
# Jornadas: leitura (GET) liberada a qualquer autenticado (usada pela grade de presença);
# exigência do módulo "jornadas" mantida apenas na escrita (router do módulo).
app.include_router(jornadas_router)
app.include_router(presencas_router, dependencies=[Depends(require_modulo("presencas"))])
app.include_router(preventivas_router, dependencies=[Depends(require_modulo("preventivas"))])
app.include_router(os_router, dependencies=[Depends(require_modulo("apropriacoes"))])
app.include_router(apropriacoes_router, dependencies=[Depends(require_modulo("apropriacoes"))])
app.include_router(motor_router, dependencies=[Depends(require_modulo("motor"))])
app.include_router(feriados_router, dependencies=[Depends(require_modulo("horas-extras"))])
app.include_router(he_router, dependencies=[Depends(require_modulo("horas-extras"))])
app.include_router(pendencias_router, dependencies=[Depends(require_modulo("pendencias"))])
app.include_router(tarefas_router, dependencies=[Depends(require_modulo("tarefas"))])
app.include_router(emails_router, dependencies=[Depends(require_modulo("emails"))])
app.include_router(absenteismo_router, dependencies=[Depends(require_modulo("absenteismo"))])
app.include_router(dashboard_router, dependencies=[Depends(require_modulo("dashboard"))])
app.include_router(relatorios_router, dependencies=[Depends(require_modulo("relatorios"))])
app.include_router(auditoria_router, dependencies=[Depends(require_modulo("auditoria"))])
app.include_router(ai_router, dependencies=[Depends(require_modulo("ai"))])
app.include_router(empresas_router)
app.include_router(usuarios_router, dependencies=[Depends(require_admin)])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "env": settings.ENV}


@app.get("/")
def root() -> dict:
    return {"app": "ERP Estacao de Trabalho", "etapa": 18, "docs": "/docs"}
