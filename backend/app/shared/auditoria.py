"""Auditoria central — ETAPA 17. Fire-and-forget: nunca quebra a operação principal.

Uso nos services: audit(usuario_id, "apropriacoes", ap_id, "atualizar", antes, depois).
"""

import logging

logger = logging.getLogger(__name__)


def audit(usuario_id: str | None, tabela: str, registro_id: str | None, acao: str, antes: dict | None, depois: dict | None) -> None:
    if not usuario_id:
        return
    try:
        from app.core.supabase_client import get_supabase

        sb = get_supabase()
        sb.table("historico_alteracoes").insert({
            "usuario_id": usuario_id,
            "tabela": tabela,
            "registro_id": registro_id,
            "acao": acao,
            "antes": antes,
            "depois": depois,
        }).execute()
    except Exception as exc:
        logger.warning("auditoria %s %s falhou: %s", tabela, acao, exc)
