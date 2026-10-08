"""Schemas motor — ETAPA 9 (dry-run, sem persistência)."""

from pydantic import BaseModel


class AvaliarIn(BaseModel):
    funcionario_id: str
    data: str


class AvaliarDiaIn(BaseModel):
    data: str
