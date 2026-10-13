-- Multi-empresa + acessos por usuário.
create table if not exists public.empresas (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  cnpj text,
  ativo boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.funcionarios
  add column if not exists empresa_id uuid references public.empresas(id);

create table if not exists public.usuario_empresas (
  usuario_id uuid not null references public.usuarios(id) on delete cascade,
  empresa_id uuid not null references public.empresas(id) on delete cascade,
  primary key (usuario_id, empresa_id)
);

create table if not exists public.usuario_modulos (
  usuario_id uuid not null references public.usuarios(id) on delete cascade,
  modulo text not null,
  primary key (usuario_id, modulo)
);

alter table public.empresas enable row level security;
alter table public.usuario_empresas enable row level security;
alter table public.usuario_modulos enable row level security;

do $$
declare t text;
begin
  foreach t in array array['empresas','usuario_empresas','usuario_modulos']
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

grant select, insert, update, delete on public.empresas, public.usuario_empresas, public.usuario_modulos to authenticated, service_role;
