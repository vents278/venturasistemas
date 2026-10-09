"""Schemas presença — ETAPA 7. data + funcionario únicos; status vem de status_presenca."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, field_validator


class PresencaIn(BaseModel):
    funcionario_id: UUID
    data: date
    status_codigo: str
    jornada_id: UUID | None = None
    obs: str | None = None

    @field_validator("status_codigo")
    @classmethod
    def _upper(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if not v:
            raise ValueError("obrigatório")
        return v


class PresencaUpdate(BaseModel):
    status_codigo: str | None = None
    jornada_id: UUID | None = None
    obs: str | None = None


class PresencaOut(BaseModel):
    id: str
    funcionario_id: str
    data: date
    status_codigo: str
    jornada_id: str | None = None
    obs: str | None = None


class LoteItem(BaseModel):
    funcionario_id: UUID
    status_codigo: str
    obs: str | None = None


class LoteIn(BaseModel):
    data: date
    itens: list[LoteItem]


class LancamentoDiarioIn(BaseModel):
    data: date
    status_padrao: str = "PRESENTE"
