"""Regras de e-mail de HE — ETAPA 13.

Toda HE gera e-mail PENDENTE + pendência EMAIL_HE_PENDENTE (idempotente).
Envio real via SMTP; sem SMTP configurado, registra ERRO e retorna 400.
"""

import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from app.core.config import settings
from app.modules.emails import repository as repo
from app.shared.auditoria import audit

logger = logging.getLogger(__name__)


def listar(status=None, de=None, ate=None):
    return repo.list_repo(status, de, ate)


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _funcionario(fid: str) -> dict:
    from app.core.supabase_client import get_supabase

    sb = get_supabase()
    r = sb.table("funcionarios").select("nome,matricula").eq("id", fid).limit(1).execute()
    return r.data[0] if r.data else {"nome": fid, "matricula": "-"}


def _texto(he: dict, func: dict) -> tuple[str, str]:
    assunto = f"HE {he['qtd_horas']}h {he['percentual']}% — {func.get('nome')} ({he['data']})"
    corpo = (
        f"Funcionário: {func.get('nome')} (matrícula {func.get('matricula')})\n"
        f"Data: {he['data']}\nHoras extras: {he['qtd_horas']}h\nAdicional: {he['percentual']}%\n"
        f"Status: E-MAIL PENDENTE"
    )
    return assunto, corpo


def garantir_para_he(he: dict) -> dict:
    """Idempotente: ENVIADO não recria; PENDENTE/ERRO atualiza texto; inexistente cria + pendência."""
    from app.modules.pendencias import repository as pd_repo

    existente = repo.find_por_he(he["id"])
    func = _funcionario(he["funcionario_id"])
    assunto, corpo = _texto(he, func)
    if existente and existente["status"] == "ENVIADO":
        return existente
    if existente:
        email = repo.update_repo(existente["id"], {"assunto": assunto, "corpo": corpo})
    else:
        email = repo.create_repo({
            "hora_extra_id": he["id"],
            "destinatario": settings.HE_EMAIL_DESTINO or "",
            "assunto": assunto,
            "corpo": corpo,
            "status": "PENDENTE",
        })
        if not pd_repo.find_aberta("EMAIL_HE_PENDENTE", he["funcionario_id"], he["data"]):
            pd_repo.create_repo({
                "tipo": "EMAIL_HE_PENDENTE",
                "funcionario_id": he["funcionario_id"],
                "data_ref": he["data"],
                "descricao": f"E-mail pendente: HE {he['qtd_horas']}h {he['percentual']}% de {func.get('nome')}",
                "prioridade": "MEDIA",
                "status": "ABERTA",
                "origem_regra": "motor_regras.hora_extra",
                "registro_tipo": "emails",
                "registro_id": email["id"],
            })
    return email


def limpar_he_removida(funcionario_id: str, data_str: str, he_ids: list) -> None:
    """HE normalizada: remove e-mails PENDENTE órfãos e cancela pendências de e-mail abertas."""
    from app.modules.pendencias import repository as pd_repo

    for hid in he_ids:
        em = repo.find_por_he(hid)
        if em and em["status"] == "PENDENTE":
            repo.delete_repo(em["id"])
    for p in pd_repo.list_abertas_por_data(data_str, ["EMAIL_HE_PENDENTE"]):
        if p.get("funcionario_id") == funcionario_id:
            pd_repo.update_repo(p["id"], {"status": "CANCELADA", "resolved_at": _agora()})


def garantir_dia(data_str: str) -> dict:
    from app.modules.horas_extras import repository as he_repo

    feitas = []
    for he in he_repo.list_repo(data_str, None, None, None, None):
        try:
            feitas.append(garantir_para_he(he))
        except RuntimeError:
            raise
        except Exception as exc:
            logger.warning("garantir email HE %s falhou: %s", he.get("id"), exc)
    return {"data": data_str, "emails": len(feitas)}


def _smtp_send(destinatario: str, assunto: str, corpo: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.set_content(corpo)
    if settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASS)
            s.send_message(msg)
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
            s.starttls()
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASS)
            s.send_message(msg)


def enviar(eid: str, destinatario: str | None = None, usuario_id: str | None = None) -> dict:
    from app.modules.pendencias import repository as pd_repo

    email = repo.get_repo(eid)
    if not email:
        raise KeyError("E-mail não encontrado")
    dest = (destinatario or email.get("destinatario") or "").strip()
    if not dest:
        raise ValueError("Destinatário vazio — informe ou configure HE_EMAIL_DESTINO")
    if not settings.SMTP_HOST:
        repo.update_repo(eid, {"erro": "SMTP não configurado (.env)", "status": "ERRO"})
        raise ValueError("SMTP não configurado (.env)")
    try:
        _smtp_send(dest, email["assunto"], email["corpo"])
    except Exception as exc:
        repo.update_repo(eid, {"erro": str(exc)[:500], "status": "ERRO"})
        raise ValueError(f"Falha no envio: {exc}")
    email = repo.update_repo(eid, {
        "destinatario": dest, "status": "ENVIADO", "erro": None, "enviado_em": _agora(),
    })
    _resolver_pendencias_do_email(email)
    audit(usuario_id, "emails", eid, "enviar", {"status": "PENDENTE"}, email)
    return email


def _resolver_pendencias_do_email(email: dict) -> None:
    from app.modules.pendencias import repository as pd_repo

    sb_list = pd_repo.list_repo("ABERTA", "EMAIL_HE_PENDENTE", None, None, None)
    for p in sb_list:
        if p.get("registro_id") == email["id"]:
            pd_repo.update_repo(p["id"], {"status": "RESOLVIDA", "resolved_at": _agora()})
