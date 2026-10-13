"""Schemas empresas."""

from pydantic import BaseModel


class EmpresaIn(BaseModel):
    nome: str
    cnpj: str | None = None


class EmpresaUpdate(BaseModel):
    nome: str | None = None
    cnpj: str | None = None
    ativo: bool | None = None
