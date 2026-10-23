"""Diagnóstico 2: apropriações/OS a partir de 2026-10-17."""

import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.supabase_client import get_supabase  # noqa: E402

sb = get_supabase()

print("== A) apropriacoes por dia (full range) ==")
apr = sb.table("apropriacoes").select("data,created_at").gte("data", "2026-10-01").execute().data or []
print("  por data:", dict(sorted(Counter(a["data"] for a in apr).items())))

print("\n== B) ultimas apropriacoes criadas ==")
ult = sb.table("apropriacoes").select("data,created_at,horas").order("created_at", desc=True).limit(8).execute().data or []
for a in ult:
    print(f"  data={a['data']} criada={a.get('created_at')} h={a['horas']}")

print("\n== C) ordens de servico ==")
os_rows = sb.table("ordens_servico").select("*").execute().data or []
print("  total OS:", len(os_rows))
if os_rows:
    print("  colunas:", list(os_rows[0].keys()))
    for o in os_rows[:12]:
        print(f"    {o.get('codigo')} status={o.get('status')} prazo={o.get('prazo')} {str(o.get('descricao'))[:40]}")

print("\n== D) apropriacoes por OS ==")
por_os = Counter(a.get("os_id") for a in (sb.table("apropriacoes").select("os_id").execute().data or []))
os_by_id = {str(o.get("id")): o.get("codigo") for o in os_rows}
for os_id, n in por_os.most_common():
    print(f"  {os_by_id.get(os_id, os_id)}: {n}")

print("\n== E) carga_prevista amostra em 2026-10-14 vs 2026-10-17 ==")
funcs = sb.table("funcionarios").select("id,nome,jornada_id").limit(5).execute().data or []
for f in funcs:
    for d in ("2026-10-14", "2026-10-17", "2026-10-20"):
        r = sb.rpc("carga_prevista", {"p_funcionario": f["id"], "p_data": d}).execute().data
        print(f"  {f['nome'][:18]} {d}: carga={r}")

print("\n== F) jornada dos funcionarios (qualquer valor) ==")
jf = sb.table("funcionarios").select("id,nome,jornada_id").execute().data or []
com = [f for f in jf if f.get("jornada_id")]
print(f"  com jornada: {len(com)} / {len(jf)}")
for f in com[:10]:
    print(f"    {f['nome']}: {f['jornada_id']}")
