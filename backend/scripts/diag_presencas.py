"""Diagnóstico: por que lançamentos param a partir de 2026-10-17."""

import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402

if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
    raise SystemExit("Sem SUPABASE_URL/SERVICE_KEY no .env")

from app.core.supabase_client import get_supabase  # noqa: E402

sb = get_supabase()
DE = "2026-10-10"
ATE = "2026-10-21"

print("== 1) presencas por dia ==")
pres = sb.table("presencas").select("data,status_codigo").gte("data", DE).lte("data", ATE).execute().data or []
por_dia = Counter(p["data"] for p in pres)
for d in sorted(por_dia):
    print(f"  {d}: {por_dia[d]}")
faltando = [d for d in [f"2026-10-{x:02d}" for x in range(10, 22)] if d not in por_dia]
print("  dias SEM presencas:", faltando)

print("\n== 2) desligamentos por data ==")
funcs = sb.table("funcionarios").select("id,nome,ativo,em_treinamento,desligamento,admissao").execute().data or []
desl = Counter(str(f.get("desligamento")) for f in funcs)
for k, v in sorted(desl.items()):
    print(f"  desligamento={k}: {v} funcionario(s)")
ativos = [f for f in funcs if f.get("ativo", True)]
inativos = [f for f in funcs if not f.get("ativo", True)]
print(f"  ativos={len(ativos)} inativos={len(inativos)} treinamento={sum(1 for f in funcs if f.get('em_treinamento'))}")

print("\n== 3) ativos com desligamento < 2026-10-17 (bloqueiam lancamento) ==")
bloq = [f for f in ativos if f.get("desligamento") and str(f["desligamento"]) < "2026-10-17"]
print(f"  total: {len(bloq)}")
for f in bloq[:15]:
    print(f"    {f['nome']} desl={f['desligamento']}")

print("\n== 4) feriados ==")
fer = sb.table("feriados").select("data,descricao").gte("data", "2026-10-01").lte("data", "2026-10-31").execute().data or []
for f in fer:
    print(f"  {f['data']} {f.get('descricao')}")

print("\n== 5) jornadas x horarios (dow) ==")
jor = sb.table("jornadas").select("id,codigo,nome,ativo").execute().data or []
hor = sb.table("jornada_horarios").select("jornada_id,dia_semana,carga_horas,inicio,fim").execute().data or []
por_j = {}
for h in hor:
    por_j.setdefault(h["jornada_id"], []).append(h["dia_semana"])
for j in jor:
    print(f"  {j['codigo']} ativo={j.get('ativo')} dow={sorted(por_j.get(j['id'], []))}")

print("\n== 6) funcionarios ativos SEM jornada ==")
sem_j = [f for f in ativos if not f.get("jornada_id")]
print(f"  total: {len(sem_j)}")
for f in sem_j[:15]:
    print(f"    {f['nome']}")

print("\n== 7) apropriacoes por dia ==")
apr = sb.table("apropriacoes").select("data").gte("data", DE).lte("data", ATE).execute().data or []
por_dia_a = Counter(a["data"] for a in apr)
for d in sorted(por_dia_a):
    print(f"  {d}: {por_dia_a[d]}")
