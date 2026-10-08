"""Leitura de auditoria — ETAPA 17 (somente GESTOR)."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.supabase_client import get_supabase
from app.modules.auth.dependencies import require_gestor

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("")
def listar(
    tabela: str | None = None,
    registro_id: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    _: dict = Depends(require_gestor),
):
    try:
        sb = get_supabase()
        q = sb.table("historico_alteracoes").select("*")
        if tabela:
            q = q.eq("tabela", tabela)
        if registro_id:
            q = q.eq("registro_id", registro_id)
        if de:
            q = q.gte("data_hora", de)
        if ate:
            q = q.lte("data_hora", ate)
        return (q.order("data_hora", desc=True).limit(200).execute().data) or []
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
