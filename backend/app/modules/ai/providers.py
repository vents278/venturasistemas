"""Provedores de IA — ETAPA 18. Interface plugável; `local` é heurístico e offline.

Futuro: implementar LLMProvider lendo AI_PROVIDER/AI_API_KEY, mantendo o
contrato (pergunta + contexto serializado → texto). Nada nos routers muda.
"""

from app.core.config import settings


class LocalProvider:
    nome = "local"

    def completar(self, pergunta: str, contexto: dict) -> str:
        linhas = [f"{k}: {v}" for k, v in contexto.items()]
        return f"[assistente local] {pergunta}\n" + "\n".join(linhas)


def get_provider():
    if (settings.AI_PROVIDER or "local").lower() == "local":
        return LocalProvider()
    raise ValueError(f"Provider de IA não implementado: {settings.AI_PROVIDER}")
