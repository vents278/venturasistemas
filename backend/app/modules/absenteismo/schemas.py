"""Schemas absenteísmo — ETAPA 14. Anexo via URL (Storage real em Documentos)."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, field_validator

PERIODOS = {"MANHA", "TARDE", "INTEGRAL"}


class TipoIn(BaseModel):
    codigo: str
    descricao: str


class AbsenteismoIn(BaseModel):
    funcionario_id: UUID
    data: date
    tipo_id: int
    motivo: str | None = None
    periodo: str = "INTEGRAL"
    anexo_url: str | None = None
    observacao: str | None = None

    @field_validator("periodo")
    @classmethod
    def _per(cls, v: str) -> str:
        v = (v or "INTEGRAL").upper()
        if v not in PERIODOS:
            raise ValueError("Período inválido")
        return v


class AbsenteismoUpdate(BaseModel):
    tipo_id: int | None = None
    motivo: str | None = None
    periodo: str | None = None
    anexo_url: str | None = None
    observacao: str | None = None
