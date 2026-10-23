"""Diagnóstico 3: dias da semana, status das presencas recentes, jornadas."""

import sys
from collections import Counter
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.supabase_client import get_supabase  # noqa: E402

NOMES = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]

print("== A) calendario out/2026 (dia da semana) ==")
for d in range(10, 22):
    dt = date(2026, 10, d)
    print(f"  2026-10-{d:02d} -> {NOMES[dt.weekday()]}")

sb = get_supabase()

print("\n== B) status das presencas por dia (10 a 21) ==")
pres = (sb.table("presencas").select("data,status_codigo")
        .gte("data", "2026-10-10").lte("data", "2026-10-21").execute().data) or []
by = {}
for p in pres:
    by.setdefault(p["data"], Counter())[p["status_codigo"]] += 1
for d in sorted(by):
    print(f"  {d}: {dict(by[d])}")

print("\n== C) jornadas e seus horarios ==")
jor = (sb.table("jornadas").select("id,codigo,nome,ativo").execute().data) or []
hor = (sb.table("jornada_horarios").select("jornada_id,dia_semana,carga_horas,inicio,fim").execute().data) or []
for j in jor:
    hs = sorted([h for h in hor if h["jornada_id"] == j["id"]], key=lambda x: x["dia_semana"])
    print(f"  {j['codigo']} ({j.get('nome')}) ativo={j.get('ativo')}")
    for h in hs:
        print(f"      dow={NOMES[h['dia_semana']]} carga={h['carga_horas']} {h.get('inicio')}-{h.get('fim')}")

print("\n== D) funcionarios SEM jornada (ativo) ==")
funcs = (sb.table("funcionarios")
         .select("id,nome,ativo,em_treinamento,jornada_id,desligamento,admissao")
         .execute().data) or []
sem = [f for f in funcs if f.get("ativo", True) and not f.get("jornada_id")]
print(f"  ativos sem jornada: {len(sem)} de {len(funcs)}")
for f in sem:
    print(f"    {f['nome']} treino={f.get('em_treinamento')} desl={f.get('desligamento')} adm={f.get('admissao')}")

print("\n== E) quantos ativos COM jornada nos dias 17/18 (sab/dom) ==")
com = [f for f in funcs if f.get("jornada_id")]
print(f"  com jornada: {len(com)}")

print("\n== F) carga_prevista global: sab 17 / dom 18 vs dias uteis ==")
if com:
    for d in ("2026-10-16", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21"):
        vals = [sb.rpc("carga_prevista", {"p_funcionario": f["id"], "p_data": d}).execute().data for f in com]
        nz = sum(1 for v in vals if v and float(v) > 0)
        print(f"  {d} ({NOMES[date.fromisoformat(d).weekday()]}): {nz}/{len(com)} com carga>0")
