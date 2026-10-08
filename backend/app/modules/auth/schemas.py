"""Schemas do módulo auth — ETAPA 4."""

from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    senha: str


class UsuarioOut(BaseModel):
    id: str
    email: str
    nome: str | None = None
    perfil: str | None = None
    ativo: bool = True


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
