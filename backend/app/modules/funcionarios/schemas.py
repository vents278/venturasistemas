"""Schemas funcionários. Cadastro: nome, cargo, área, supervisor (+ matrícula/admissão automáticas)."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FuncionarioIn(BaseModel):
    nome: str
    cargo: str | None = None
    area: str | None = None
    supervisor_id: UUID | None = None
    matricula: str | None = None
    admissao: date = Field(default_factory=date.today)
    setor: str | None = None
    desligamento: date | None = None
    ativo: bool = True
    em_treinamento: bool = False
    jornada_id: UUID | None = None  # jornada padrão (a do dia é lançada na grade)
    observacoes: str | None = None

    @field_validator("nome")
    @classmethod
    def _nome(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("obrigatório")
        return v

    @field_validator("matricula")
    @classmethod
    def _mat(cls, v: str | None) -> str | None:
        v = (v or "").strip() if v else None
        return v or None


class FuncionarioUpdate(BaseModel):
    nome: str | None = None
    cargo: str | None = None
    area: str | None = None
    supervisor_id: UUID | None = None
    matricula: str | None = None
    admissao: date | None = None
    setor: str | None = None
    desligamento: date | None = None
    ativo: bool | None = None
    em_treinamento: bool | None = None
    jornada_id: UUID | None = None
    observacoes: str | None = None


class FuncionarioOut(BaseModel):
    id: str
    matricula: str
    nome: str
    cargo: str | None = None
    area: str | None = None
    setor: str | None = None
    supervisor_id: str | None = None
    admissao: date
    desligamento: date | None = None
    ativo: bool
    em_treinamento: bool = False
    jornada_id: str | None = None
    observacoes: str | None = None
