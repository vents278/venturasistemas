"""Gestão de usuários (ADMIN): criar login + vínculo + empresas + módulos."""

from uuid import UUID

from pydantic import BaseModel, EmailStr


class UsuarioCreateIn(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: str = "OPERADOR"
    empresas: list[UUID] = []
    modulos: list[str] = []


class AcessosIn(BaseModel):
    perfil: str | None = None
    empresas: list[UUID] | None = None
    modulos: list[str] | None = None
