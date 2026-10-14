"""Schemas de preventivas — programação + checklist de OS.

os_codigo é texto (preserva zeros à esquerda e formatos alfanuméricos).
os_id é o vínculo opcional com a OS já cadastrada em ordens_servico.
"""

from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field

STATUS_PREVENTIVA = {
    "PROGRAMADA", "EM_ANDAMENTO", "AGUARDANDO_OS",
    "PARCIALMENTE_CONCLUIDA", "CONCLUIDA", "CANCELADA",
}


class PreventivaIn(BaseModel):
    data: date
    area: str
    equipamento: str | None = None
    descricao: str
    responsavel_id: UUID | None = None
    hora_inicio: time | None = None
    hora_fim: time | None = None
    observacoes: str | None = None
    status: str | None = None
    empresa_id: UUID | None = None


class PreventivaUpdate(BaseModel):
    data: date | None = None
    area: str | None = None
    equipamento: str | None = None
    descricao: str | None = None
    responsavel_id: UUID | None = None
    hora_inicio: time | None = None
    hora_fim: time | None = None
    observacoes: str | None = None
    status: str | None = None
    os_completa: bool | None = None


class FuncionarioProgramadoIn(BaseModel):
    funcionario_id: UUID
    programado: bool = True
    compareceu: bool = False
    hora_prev_inicio: time | None = None
    hora_prev_fim: time | None = None
    hora_efet_inicio: time | None = None
    hora_efet_fim: time | None = None
    os_completa: bool = False
    observacoes: str | None = None


class FuncionarioProgramadoUpdate(BaseModel):
    programado: bool | None = None
    compareceu: bool | None = None
    hora_prev_inicio: time | None = None
    hora_prev_fim: time | None = None
    hora_efet_inicio: time | None = None
    hora_efet_fim: time | None = None
    os_completa: bool | None = None
    observacoes: str | None = None


class PreventivaOSIn(BaseModel):
    os_codigo: str
    os_id: UUID | None = None
    descricao: str | None = None
    data_execucao: date | None = None
    horas: float = Field(default=0, ge=0, le=24)
    recebida: bool = False
    observacoes: str | None = None
    anexo_url: str | None = None


class PreventivaOSUpdate(BaseModel):
    os_codigo: str | None = None
    os_id: UUID | None = None
    descricao: str | None = None
    data_execucao: date | None = None
    horas: float | None = Field(default=None, ge=0, le=24)
    recebida: bool | None = None
    observacoes: str | None = None
    anexo_url: str | None = None
