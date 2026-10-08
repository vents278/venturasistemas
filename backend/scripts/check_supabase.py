"""Verificação da ETAPA 3: valida SQL local + conexão Supabase (se .env configurado)."""

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

SQL_FILES = [
    Path(__file__).resolve().parents[2] / "supabase" / "migrations" / "0001_schema.sql",
    Path(__file__).resolve().parents[2] / "supabase" / "migrations" / "0002_rls.sql",
    Path(__file__).resolve().parents[2] / "supabase" / "seed.sql",
]

REQUIRED_TOKENS = [
    "funcionarios", "jornada_horarios", "carga_prevista",
    "apropriacoes", "horas_extras", "pendencias", "tarefas",
]


def check_sql() -> None:
    missing = [p for p in SQL_FILES if not p.exists()]
    if missing:
        raise SystemExit(f"SQL ausente: {missing}")
    for p in SQL_FILES:
        text = p.read_text(encoding="utf-8").lower()
        for tok in REQUIRED_TOKENS if p.name == "0001_schema.sql" else []:
            if tok not in text:
                raise SystemExit(f"{p.name} sem token obrigatório: {tok}")
    print("SQL OK: 0001_schema, 0002_rls, seed presentes")


def check_connection() -> None:
    from app.core.config import settings

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        print("SKIP conexao: .env sem SUPABASE_URL/SERVICE_KEY — aplique o SQL no dashboard primeiro")
        return
    from app.core.supabase_client import get_supabase

    sb = get_supabase()
    r = sb.table("status_presenca").select("codigo").limit(1).execute()
    print(f"Supabase OK: status_presenca respondeu ({len(r.data)} linha(s) amostra)")


if __name__ == "__main__":
    check_sql()
    check_connection()
