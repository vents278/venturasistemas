"""Importa funcionários da planilha Lista_consolidada (uso único, idempotente por nome).

Uso: python scripts/import_funcionarios.py <caminho.xlsx>
Mapeamento: nome, cargo, area, setor(=Equipe), obs(responsável+situacao).
Presença 09/10 só p/ casos claros (PRESENTE/FALTA/FÉRIAS); resto fica na obs p/ ajuste na grade.
"""

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import openpyxl  # noqa: E402

from app.core.supabase_client import get_supabase  # noqa: E402
from app.modules.funcionarios.service import _gerar_matricula  # noqa: E402

STATUS_OK = {"PRESENTE": "PRESENTE", "FALTA": "FALTA", "FÉRIAS": "FERIAS", "FERIAS": "FERIAS"}
DATA_REF = "2026-10-09"


def main(path: str) -> None:
    sb = get_supabase()
    wb = openpyxl.load_workbook(path, data_only=True)
    sh = wb["Lista consolidada"]
    adm = sb.table("jornadas").select("id").eq("codigo", "ADM").limit(1).execute()
    adm_id = adm.data[0]["id"] if adm.data else None
    existentes = {r["nome"].strip().upper(): r for r in
                  sb.table("funcionarios").select("id,nome").execute().data or []}
    criados, pulados, pres = 0, 0, 0
    for row in sh.iter_rows(min_row=2, values_only=True):
        nome = (row[0] or "").strip()
        if not nome or nome.upper() in existentes:
            pulados += 1
            continue
        equipe = (row[5] or "").strip() or None
        payload = {
            "matricula": _gerar_matricula(),
            "admissao": DATA_REF,
            "nome": nome,
            "cargo": (row[1] or "").strip() or None,
            "area": (row[3] or "").strip() or None,
            "setor": equipe,
            "observacoes": f"Responsável: {(row[2] or '').strip()} | Situação 09/10: {(row[6] or '').strip()}",
            "jornada_id": adm_id if (equipe or "").upper() == "ADM" else None,
        }
        f = sb.table("funcionarios").insert(payload).execute().data[0]
        existentes[nome.upper()] = f
        criados += 1
        st = STATUS_OK.get((row[6] or "").strip().upper())
        if st:
            sb.table("presencas").upsert(
                {"funcionario_id": f["id"], "data": DATA_REF, "status_codigo": st,
                 "jornada_id": payload["jornada_id"], "obs": "importado da planilha"},
                on_conflict="funcionario_id,data").execute()
            pres += 1
    print(f"criados={criados} ja_existiam={pulados} presencas_09_10={pres}")


if __name__ == "__main__":
    main(sys.argv[1])
