"""Schemas apropriação — ETAPA 8. Um funcionário pode dividir o dia em várias OS."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ApropriacaoIn(BaseModel):
    funcionario_id: UUID
    data: date
    os_id: UUID
    horas: float = Field(gt=0, le=24)


class ApropriacaoUpdate(BaseModel):
    horas: float = Field(gt=0, le=24)


class ApropriacaoOut(BaseModel):
    id: str
    funcionario_id: str
    data: date
    os_id: str
    horas: float


class ApropriacaoItem(BaseModel):
    os_id: UUID
    horas: float = Field(gt=0, le=24)


class ApropriacaoLoteIn(BaseModel):
    funcionario_id: UUID
    data: date
    itens: list[ApropriacaoItem]


class ApropriacaoLoteOSItem(BaseModel):
    funcionario_id: UUID
    horas: float = Field(gt=0, le=24)


class ApropriacaoLoteOSIn(BaseModel):
    data: date
    os_id: UUID
    itens: list[ApropriacaoLoteOSItem]
