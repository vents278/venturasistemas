-- Programação e controle de manutenções preventivas.
-- Reutiliza funcionarios, ordens_servico, usuarios, empresas e pendencias.
-- Nada existente é alterado além da lista de tipos de pendência (novos códigos).

-- ============ preventivas (cabeçalho da programação) ============
create table if not exists public.preventivas (
  id uuid primary key default gen_random_uuid(),
  data date not null,
  area text not null,
  equipamento text,
  descricao text not null,
  responsavel_id uuid references public.funcionarios(id),
  hora_inicio time,
  hora_fim time,
  observacoes text,
  status text not null default 'PROGRAMADA'
    check (status in ('PROGRAMADA','EM_ANDAMENTO','AGUARDANDO_OS','PARCIALMENTE_CONCLUIDA','CONCLUIDA','CANCELADA')),
  -- confirmação manual de que o lançamento das OS da preventiva está completo
  os_completa boolean not null default false,
  empresa_id uuid references public.empresas(id),
  created_by uuid references public.usuarios(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_preventivas_data on public.preventivas(data);
create index if not exists idx_preventivas_area on public.preventivas(area);
create index if not exists idx_preventivas_status on public.preventivas(status);

-- ============ funcionários escalados na preventiva ============
create table if not exists public.preventiva_funcionarios (
  id uuid primary key default gen_random_uuid(),
  preventiva_id uuid not null references public.preventivas(id) on delete cascade,
  funcionario_id uuid not null references public.funcionarios(id) on delete cascade,
  programado boolean not null default true,
  compareceu boolean not null default false,
  hora_prev_inicio time,
  hora_prev_fim time,
  hora_efet_inicio time,
  hora_efet_fim time,
  -- confirma que todas as OS daquele funcionário foram lançadas (fecha o checklist individual)
  os_completa boolean not null default false,
  observacoes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (preventiva_id, funcionario_id)
);

create index if not exists idx_prev_func_preventiva on public.preventiva_funcionarios(preventiva_id);
create index if not exists idx_prev_func_funcionario on public.preventiva_funcionarios(funcionario_id);

-- ============ OS executadas por funcionário na preventiva ============
-- os_codigo é TEXTO para preservar zeros à esquerda / formatos alfanuméricos.
-- os_id é o vínculo opcional com a OS já cadastrada no ERP.
create table if not exists public.preventiva_os (
  id uuid primary key default gen_random_uuid(),
  preventiva_id uuid not null references public.preventivas(id) on delete cascade,
  preventiva_funcionario_id uuid not null references public.preventiva_funcionarios(id) on delete cascade,
  funcionario_id uuid not null references public.funcionarios(id) on delete cascade,
  os_codigo text not null,
  os_id uuid references public.ordens_servico(id),
  descricao text,
  data_execucao date,
  horas numeric(5,2) not null default 0 check (horas >= 0 and horas <= 24),
  recebida boolean not null default false,
  data_recebimento date,
  recebido_por uuid references public.usuarios(id),
  observacoes text,
  anexo_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- não permite duplicar o mesmo número de OS para o mesmo funcionário na preventiva
  unique (preventiva_funcionario_id, os_codigo)
);

create index if not exists idx_prev_os_preventiva on public.preventiva_os(preventiva_id);
create index if not exists idx_prev_os_func on public.preventiva_os(funcionario_id);
create index if not exists idx_prev_os_codigo on public.preventiva_os(os_codigo);
create index if not exists idx_prev_os_osid on public.preventiva_os(os_id);

-- ============ updated_at automático ============
drop trigger if exists trg_preventivas_updated on public.preventivas;
create trigger trg_preventivas_updated before update on public.preventivas
  for each row execute function public.set_updated_at();

drop trigger if exists trg_prev_func_updated on public.preventiva_funcionarios;
create trigger trg_prev_func_updated before update on public.preventiva_funcionarios
  for each row execute function public.set_updated_at();

drop trigger if exists trg_prev_os_updated on public.preventiva_os;
create trigger trg_prev_os_updated before update on public.preventiva_os
  for each row execute function public.set_updated_at();

-- ============ RLS (mesmo baseline das demais tabelas) ============
alter table public.preventivas enable row level security;
alter table public.preventiva_funcionarios enable row level security;
alter table public.preventiva_os enable row level security;

do $$
declare t text;
begin
  foreach t in array array['preventivas','preventiva_funcionarios','preventiva_os']
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

grant select, insert, update, delete on public.preventivas, public.preventiva_funcionarios, public.preventiva_os
  to authenticated, service_role;

-- ============ novos tipos de pendência do módulo ============
alter table public.pendencias drop constraint if exists pendencias_tipo_check;
alter table public.pendencias add constraint pendencias_tipo_check check (tipo in (
  'APROPRIACAO_INCOMPLETA','SEM_APROPRIACAO','EMAIL_HE_PENDENTE','FALTA_INFO',
  'PREVENTIVA_SEM_OS','PREVENTIVA_OS_PENDENTE','PREVENTIVA_DOC_INCOMPLETA','PREVENTIVA_HORAS_DIVERGENTES'
));
