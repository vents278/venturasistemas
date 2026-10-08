# Supabase — ETAPA 3

## Aplicar (ordens)

1. Crie o projeto em https://supabase.com → copie URL + anon/service keys para `.env` (ver `.env.example`).
2. No Dashboard → SQL Editor, rode nesta ordem:
   - `supabase/migrations/0001_schema.sql`
   - `supabase/migrations/0002_rls.sql`
   - `supabase/seed.sql`
3. Confira: Table Editor deve mostrar `jornadas` com 3 linhas, `jornada_horarios` com 15 linhas (5 ADM + 5 tarde + 5 noturno), `status_presenca` com 7 linhas.

## Verificação local

```powershell
cd backend
python scripts\check_supabase.py
```

Sem `.env` configurado: valida só os arquivos SQL (esperado na primeira vez).
Com `.env`: testa `select` em `status_presenca` via service key.

## Notas

- RLS habilitado em todas as tabelas; políticas da `0002` são baseline permissivo para `authenticated`. Endurecer por perfil na ETAPA 4.
- `carga_prevista(funcionario, data)` retorna 0 em feriado/desligado/sem jornada — usada pelo motor de regras (ETAPA 9).
- Storage (anexos) entra nas etapas de tarefas/absenteísmo.
