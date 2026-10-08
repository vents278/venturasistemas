"""Schemas tarefas — ETAPA 12. Tarefa é manual; pendência é automática (link opcional)."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, field_validator

STATUS = {"A_FAZER", "EM_ANDAMENTO", "AGUARDANDO", "CONCLUIDO"}
PRIORIDADES = {"ALTA", "MEDIA", "BAIXA"}


class TarefaIn(BaseModel):
    titulo: str
    descricao: str | None = None
    status: str = "A_FAZER"
    prioridade: str = "MEDIA"
    responsavel_id: UUID | None = None
    prazo: date | None = None
    categoria: str | None = None

    @field_validator("titulo")
    @classmethod
    def _tit(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("obrigatório")
        return v


class TarefaUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    status: str | None = None
    prioridade: str | None = None
    responsavel_id: UUID | None = None
    prazo: date | None = None
    categoria: str | None = None


class ChecklistIn(BaseModel):
    titulo: str


class ChecklistUpdate(BaseModel):
    titulo: str | None = None
    feito: bool | None = None


class ComentarioIn(BaseModel):
    texto: str


class AnexoIn(BaseModel):
    arquivo_url: str
    nome: str | None = None


class APartirDePendenciaIn(BaseModel):
    titulo: str | None = None
    responsavel_id: UUID | None = None
    prioridade: str | None = None
