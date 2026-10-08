"""Schemas feriados — ETAPA 10."""

from datetime import date

from pydantic import BaseModel

TIPOS = {"NACIONAL", "ESTADUAL", "MUNICIPAL", "FACULTATIVO"}


class FeriadoIn(BaseModel):
    data: date
    descricao: str
    tipo: str = "NACIONAL"


class FeriadoOut(BaseModel):
    data: date
    descricao: str
    tipo: str
