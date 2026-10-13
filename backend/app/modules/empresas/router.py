"""Empresas: ADMIN gerencia; demais veem só as suas."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.supabase_client import get_supabase
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.empresas.schemas import EmpresaIn, EmpresaUpdate

router = APIRouter(prefix="/empresas", tags=["empresas"])


def _visiveis(user: dict) -> list:
    sb = get_supabase()
    if user.get("perfil") == "ADMIN":
        return (sb.table("empresas").select("*").order("nome").execute().data) or []
    ids = user.get("empresas") or []
    if not ids:
        return (sb.table("empresas").select("*").order("nome").execute().data) or []
    return (sb.table("empresas").select("*").in_("id", ids).order("nome").execute().data) or []


@router.get("")
def listar(user: dict = Depends(get_current_user)):
    try:
        return _visiveis(user)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", status_code=201)
def criar(body: EmpresaIn, _: dict = Depends(require_admin)):
    sb = get_supabase()
    return sb.table("empresas").insert({"nome": body.nome.strip(), "cnpj": body.cnpj}).execute().data[0]


@router.patch("/{eid}")
def atualizar(eid: str, body: EmpresaUpdate, _: dict = Depends(require_admin)):
    sb = get_supabase()
    r = sb.table("empresas").update(body.model_dump(exclude_unset=True)).eq("id", eid).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return r.data[0]


@router.delete("/{eid}", status_code=204)
def excluir(eid: str, _: dict = Depends(require_admin)):
    sb = get_supabase()
    uso = sb.table("funcionarios").select("id", count="exact").eq("empresa_id", eid).limit(1).execute()
    if (uso.count or 0) > 0:
        raise HTTPException(status_code=400, detail="Empresa possui funcionários")
    sb.table("empresas").delete().eq("id", eid).execute()
