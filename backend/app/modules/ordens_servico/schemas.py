"""Schemas OS — ETAPA 8."""

from uuid import UUID

from pydantic import BaseModel, field_validator

STATUS_OS = {"ABERTA", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA"}


class OSIn(BaseModel):
    codigo: str
    descricao: str | None = None
    status: str = "ABERTA"
    responsavel_id: UUID | None = None

    @field_validator("codigo")
    @classmethod
    def _cod(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if not v:
            raise ValueError("obrigatório")
        return v

    @field_validator("status")
    @classmethod
    def _st(cls, v: str) -> str:
        v = (v or "ABERTA").strip().upper()
        if v not in STATUS_OS:
            raise ValueError(f"Status inválido: {v}")
        return v


class OSUpdate(BaseModel):
    descricao: str | None = None
    status: str | None = None
    responsavel_id: UUID | None = None


class OSOut(BaseModel):
    id: str
    codigo: str
    descricao: str | None = None
    status: str
    responsavel_id: str | None = None
