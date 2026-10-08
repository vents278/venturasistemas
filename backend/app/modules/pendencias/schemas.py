"""Schemas pendências — ETAPA 11."""

from pydantic import BaseModel


class SincronizarDiaIn(BaseModel):
    data: str
