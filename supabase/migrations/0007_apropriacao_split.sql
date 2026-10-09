-- Reformulação apropriações: data de execução e updated_at na OS,
-- split normal/extra auditável por linha, percentuais de HE configuráveis.

alter table public.ordens_servico
  add column if not exists data_execucao date,
  add column if not exists updated_at timestamptz not null default now();

drop trigger if exists trg_os_updated on public.ordens_servico;
create trigger trg_os_updated before update on public.ordens_servico
  for each row execute function public.set_updated_at();

alter table public.apropriacoes
  add column if not exists horas_normais numeric(5,2) not null default 0,
  add column if not exists horas_extras numeric(5,2) not null default 0;

create table if not exists public.parametros_he (
  condicao text primary key, -- SEG_SEX, SABADO, DOMINGO, FERIADO
  percentual smallint not null check (percentual in (50, 70, 100)),
  updated_at timestamptz not null default now()
);

insert into public.parametros_he (condicao, percentual) values
  ('SEG_SEX', 50), ('SABADO', 70), ('DOMINGO', 100), ('FERIADO', 100)
on conflict (condicao) do nothing;

alter table public.parametros_he enable row level security;
drop policy if exists p_read on public.parametros_he;
create policy p_read on public.parametros_he for select to authenticated using (true);
drop policy if exists p_write on public.parametros_he;
create policy p_write on public.parametros_he for insert to authenticated with check (true);
drop policy if exists p_upd on public.parametros_he;
create policy p_upd on public.parametros_he for update to authenticated using (true) with check (true);

grant select, insert, update, delete on public.parametros_he to authenticated, service_role;
