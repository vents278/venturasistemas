"""Schemas IA — ETAPA 18. Somente leitura; a IA nunca escreve no operacional."""

from pydantic import BaseModel


class ResumoDiaIn(BaseModel):
    data: str


class PerguntarIn(BaseModel):
    pergunta: str
