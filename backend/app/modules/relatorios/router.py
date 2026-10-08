"""Rotas relatórios — ETAPA 16. Download com Content-Disposition (autenticado)."""

from fastapi import APIRouter, Depends, Query, Response

from app.modules.auth.dependencies import get_current_user
from app.modules.relatorios import service

router = APIRouter(prefix="/relatorios", tags=["relatorios"])


@router.get("/{recurso}.{formato}")
def baixar(
    recurso: str,
    formato: str,
    data: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    funcionario_id: str | None = None,
    responsavel_id: str | None = None,
    status: str | None = None,
    tipo: str | None = None,
    setor: str | None = None,
    q: str | None = Query(default=None),
    ativo: bool | None = None,
    _: dict = Depends(get_current_user),
):
    filtros = {"data": data, "de": de, "ate": ate, "funcionario_id": funcionario_id,
               "responsavel_id": responsavel_id, "status": status, "tipo": tipo,
               "setor": setor, "q": q, "ativo": ativo}
    filtros = {k: v for k, v in filtros.items() if v is not None}
    try:
        data_bytes, mime, nome = service.gerar(recurso, formato, filtros)
    except KeyError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(exc))
    return Response(content=data_bytes, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{nome}"'})
