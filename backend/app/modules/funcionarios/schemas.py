"""Schemas funcionários — ETAPA 5. Entidade central do ERP."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, field_validator


class FuncionarioIn(BaseModel):
    matricula: str
    nome: str
    cpf: str | None = None
    cargo: str | None = None
    area: str | None = None
    setor: str | None = None
    empresa: str | None = None
    admissao: date
    desligamento: date | None = None
    ativo: bool = True
    jornada_id: UUID | None = None
    supervisor_id: UUID | None = None
    observacoes: str | None = None

    @field_validator("matricula", "nome")
    @classmethod
    def _strip_obrigatorio(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("obrigatório")
        return v

    @field_validator("cpf")
    @classmethod
    def _cpf(cls, v: str | None) -> str | None:
        if v is None or str(v).strip() == "":
            return None
        d = "".join(ch for ch in str(v) if ch.isdigit())
        if len(d) != 11 or len(set(d)) == 1:
            raise ValueError("CPF inválido")
        return d


class FuncionarioUpdate(BaseModel):
    matricula: str | None = None
    nome: str | None = None
    cpf: str | None = None
    cargo: str | None = None
    area: str | None = None
    setor: str | None = None
    empresa: str | None = None
    admissao: date | None = None
    desligamento: date | None = None
    ativo: bool | None = None
    jornada_id: UUID | None = None
    supervisor_id: UUID | None = None
    observacoes: str | None = None


class FuncionarioOut(BaseModel):
    id: str
    matricula: str
    nome: str
    cpf: str | None = None
    cargo: str | None = None
    area: str | None = None
    setor: str | None = None
    empresa: str | None = None
    admissao: date
    desligamento: date | None = None
    ativo: bool
    jornada_id: str | None = None
    supervisor_id: str | None = None
    observacoes: str | None = None
