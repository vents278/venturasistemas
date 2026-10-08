"""Schemas e-mails — ETAPA 13. Envio real via SMTP do .env; sem SMTP, 400 sem fingir envio."""

from pydantic import BaseModel


class GarantirDiaIn(BaseModel):
    data: str


class EnviarIn(BaseModel):
    destinatario: str | None = None
