"""Schemas jornadas — ETAPA 6. dia_semana 0=dom..6=sáb (EXTRACT DOW)."""

from datetime import time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class JornadaIn(BaseModel):
    codigo: str
    nome: str
    descricao: str | None = None
    ativo: bool = True

    @field_validator("codigo")
    @classmethod
    def _cod(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if not v:
            raise ValueError("obrigatório")
        return v


class JornadaUpdate(BaseModel):
    codigo: str | None = None
    nome: str | None = None
    descricao: str | None = None
    ativo: bool | None = None


class JornadaOut(BaseModel):
    id: str
    codigo: str
    nome: str
    descricao: str | None = None
    ativo: bool


class HorarioIn(BaseModel):
    dia_semana: int = Field(ge=0, le=6)
    inicio: time
    fim: time
    carga_horas: float = Field(gt=0, le=24)
    intervalo_min: int = Field(default=60, ge=0)
    atravessa_meia_noite: bool = False
    exige_apropriacao: bool = True


class HorarioUpdate(BaseModel):
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    inicio: time | None = None
    fim: time | None = None
    carga_horas: float | None = Field(default=None, gt=0, le=24)
    intervalo_min: int | None = Field(default=None, ge=0)
    atravessa_meia_noite: bool | None = None
    exige_apropriacao: bool | None = None


class HorarioOut(BaseModel):
    id: str
    jornada_id: str
    dia_semana: int
    inicio: str
    fim: str
    carga_horas: float
    intervalo_min: int
    atravessa_meia_noite: bool
    exige_apropriacao: bool
