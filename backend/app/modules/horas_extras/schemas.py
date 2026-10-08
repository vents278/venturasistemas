"""Schemas horas extras — ETAPA 10. Registro é DADO; e-mail pendente vem na ETAPA 13."""

from datetime import date

from pydantic import BaseModel


class RecalcularIn(BaseModel):
    funcionario_id: str
    data: date


class RecalcularDiaIn(BaseModel):
    data: date
