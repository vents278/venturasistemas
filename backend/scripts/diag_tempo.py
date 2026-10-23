"""Diagnóstico 4: quando presencas/apropriacoes foram criadas; janela 17-21."""

import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.supabase_client import get_supabase  # noqa: E402

sb = get_supabase()

print("== A) presencas de 17/10 a 21/10: created_at (quando foram gravadas) ==")
pres = (sb.table("presencas").select("data,created_at,status_codigo")
        .gte("data", "2026-10-17").lte("data", "2026-10-21")
        .order("created_at").execute().data) or []
for p in pres[:40]:
    print(f"  data={p['data']} criada={p.get('created_at')} {p['status_codigo']}")
print(f"  total: {len(pres)}")

print("\n== B) apropriacoes 17/10+: created_at ==")
apr = (sb.table("apropriacoes").select("data,created_at,horas")
       .gte("data", "2026-10-17").order("created_at").execute().data) or []
for a in apr:
    print(f"  data={a['data']} criada={a.get('created_at')} h={a['horas']}")
print(f"  total: {len(apr)}")

print("\n== C) total de horas por funcionario/data (checar teto 24h) nos ultimos dias ==")
apr2 = (sb.table("apropriacoes").select("funcionario_id,data,horas")
        .gte("data", "2026-10-13").execute().data) or []
tot = {}
for a in apr2:
    tot.setdefault((a["funcionario_id"], a["data"]), 0.0)
    tot[(a["funcionario_id"], a["data"])] += float(a["horas"])
over = {k: v for k, v in tot.items() if v >= 24.0}
print(f"  combinacoes com total >= 24h (bloqueiam novo lancamento): {len(over)}")
for k, v in list(over.items())[:20]:
    nome = sb.table("funcionarios").select("nome").eq("id", k[0]).limit(1).execute().data
    nome = nome[0]["nome"] if nome else k[0]
    print(f"    {nome} {k[1]}: {v}h")

print("\n== D) funcionarios ja com 9h em 20/10 e 21/10 (lancamento round 1 ja fechou?) ==")
for d in ("2026-10-20", "2026-10-21"):
    rows = [a for a in (sb.table("apropriacoes").select("funcionario_id,horas,data").eq("data", d).execute().data or [])]
    print(f"  {d}: {len(rows)} apropriacoes")

print("\n== E) presencas hoje 21/10 x quantos ativos ==")
funcs = sb.table("funcionarios").select("id,ativo,em_treinamento").execute().data or []
ativos = [f for f in funcs if f.get("ativo", True)]
p21 = sb.table("presencas").select("id").eq("data", "2026-10-21").execute().data or []
print(f"  ativos={len(ativos)} presencas hoje={len(p21)}")

print("\n== F) distribuicao criacao das presencas por dia (created_at date) ==")
pres2 = (sb.table("presencas").select("data,created_at")
         .gte("data", "2026-10-13").execute().data) or []
cri = Counter((p.get("created_at") or "")[:10] for p in pres2)
for k in sorted(cri):
    print(f"  criadas em {k}: {cri[k]}")
