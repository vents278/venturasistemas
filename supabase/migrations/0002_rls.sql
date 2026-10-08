-- ETAPA 3 — RLS baseline
-- service_role bypassa RLS; políticas abaixo valem para authenticated.
-- Na ETAPA 4 (auth) vamos restringir por perfil (ADMIN/GESTOR/OPERADOR).

alter table public.perfis_usuario enable row level security;
alter table public.usuarios enable row level security;
alter table public.jornadas enable row level security;
alter table public.jornada_horarios enable row level security;
alter table public.feriados enable row level security;
alter table public.status_presenca enable row level security;
alter table public.funcionarios enable row level security;
alter table public.ordens_servico enable row level security;
alter table public.presencas enable row level security;
alter table public.apropriacoes enable row level security;
alter table public.horas_extras enable row level security;
alter table public.tipos_ausencia enable row level security;
alter table public.absenteismo enable row level security;
alter table public.pendencias enable row level security;
alter table public.tarefas enable row level security;
alter table public.tarefa_checklists enable row level security;
alter table public.tarefa_comentarios enable row level security;
alter table public.tarefa_anexos enable row level security;
alter table public.emails enable row level security;
alter table public.notificacoes enable row level security;
alter table public.historico_alteracoes enable row level security;

-- Baseline permissivo para authenticated (leitura ampla + escrita).
-- Endurecer na ETAPA 4. Tabelas de parâmetro: leitura pública autenticada.
do $$
declare t text;
begin
  foreach t in array array[
    'perfis_usuario','usuarios','jornadas','jornada_horarios','feriados',
    'status_presenca','funcionarios','ordens_servico','presencas','apropriacoes',
    'horas_extras','tipos_ausencia','absenteismo','pendencias','tarefas',
    'tarefa_checklists','tarefa_comentarios','tarefa_anexos','emails',
    'notificacoes','historico_alteracoes']
  loop
    execute format('drop policy if exists p_read on public.%I', t);
    execute format('create policy p_read on public.%I for select to authenticated using (true)', t);
    execute format('drop policy if exists p_write on public.%I', t);
    execute format('create policy p_write on public.%I for insert to authenticated with check (true)', t);
    execute format('drop policy if exists p_upd on public.%I', t);
    execute format('create policy p_upd on public.%I for update to authenticated using (true) with check (true)', t);
    execute format('drop policy if exists p_del on public.%I', t);
    execute format('create policy p_del on public.%I for delete to authenticated using (true)', t);
  end loop;
end $$;
