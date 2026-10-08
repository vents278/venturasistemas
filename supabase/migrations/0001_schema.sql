-- ETAPA 3 — Schema núcleo do ERP Estação de Trabalho
-- Ordem: extensões → tabelas base → operacionais → engine/pendências → auditoria → indexes → views/functions/triggers

-- ============ extensões ============
create extension if not exists "pgcrypto";

-- ============ perfis / usuários (FK para auth.users do Supabase Auth) ============
create table if not exists public.perfis_usuario (
  id smallserial primary key,
  nome text not null unique
);

create table if not exists public.usuarios (
  id uuid primary key references auth.users(id) on delete cascade,
  perfil_id smallint not null references public.perfis_usuario(id),
  nome text not null,
  email text not null unique,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============ jornadas parametrizáveis (nunca hardcoded) ============
-- dia_semana: 0=domingo .. 6=sábado (compatível com EXTRACT(DOW FROM data))
create table if not exists public.jornadas (
  id uuid primary key default gen_random_uuid(),
  codigo text not null unique, -- ADM, DESLOC_TARDE, DESLOC_NOTURNO
  nome text not null,
  descricao text,
  ativo boolean not null default true
);

create table if not exists public.jornada_horarios (
  id uuid primary key default gen_random_uuid(),
  jornada_id uuid not null references public.jornadas(id) on delete cascade,
  dia_semana smallint not null check (dia_semana between 0 and 6),
  inicio time not null,
  fim time not null,
  carga_horas numeric(5,2) not null check (carga_horas >= 0 and carga_horas <= 24),
  intervalo_min int not null default 60 check (intervalo_min >= 0),
  atravessa_meia_noite boolean not null default false,
  exige_apropriacao boolean not null default true,
  unique (jornada_id, dia_semana)
);

create table if not exists public.feriados (
  data date primary key,
  descricao text not null,
  tipo text not null default 'NACIONAL' -- NACIONAL/ESTADUAL/MUNICIPAL/FACULTATIVO
);

-- ============ presença / funcionários ============
create table if not exists public.status_presenca (
  codigo text primary key, -- PRESENTE, DESLOCADO, FOLGA, FALTA, FERIAS, AFASTADO, TREINAMENTO
  descricao text not null,
  exige_apropriacao boolean not null default false,
  conta_absenteismo boolean not null default false
);

create table if not exists public.funcionarios (
  id uuid primary key default gen_random_uuid(),
  matricula text not null unique,
  nome text not null,
  cpf text unique, -- nullable; unicidade vale só quando preenchido
  cargo text,
  area text,
  setor text,
  empresa text,
  admissao date not null,
  desligamento date check (desligamento is null or desligamento >= admissao),
  ativo boolean not null default true,
  jornada_id uuid references public.jornadas(id),
  supervisor_id uuid references public.funcionarios(id),
  observacoes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ordens_servico (
  id uuid primary key default gen_random_uuid(),
  codigo text not null unique,
  descricao text,
  status text not null default 'ABERTA',
  responsavel_id uuid references public.funcionarios(id),
  created_at timestamptz not null default now()
);

create table if not exists public.presencas (
  id uuid primary key default gen_random_uuid(),
  funcionario_id uuid not null references public.funcionarios(id) on delete cascade,
  data date not null,
  status_codigo text not null references public.status_presenca(codigo),
  jornada_id uuid references public.jornadas(id), -- snapshot da jornada do dia
  obs text,
  created_at timestamptz not null default now(),
  unique (funcionario_id, data)
);

-- ============ apropriação / horas extras ============
create table if not exists public.apropriacoes (
  id uuid primary key default gen_random_uuid(),
  funcionario_id uuid not null references public.funcionarios(id) on delete cascade,
  data date not null,
  os_id uuid not null references public.ordens_servico(id),
  horas numeric(5,2) not null check (horas > 0 and horas <= 24),
  created_at timestamptz not null default now(),
  unique (funcionario_id, data, os_id)
);

create table if not exists public.horas_extras (
  id uuid primary key default gen_random_uuid(),
  funcionario_id uuid not null references public.funcionarios(id) on delete cascade,
  data date not null,
  qtd_horas numeric(5,2) not null check (qtd_horas > 0 and qtd_horas <= 24),
  percentual smallint not null check (percentual in (50, 70, 100)),
  origem text not null default 'MOTOR_REGRAS',
  created_at timestamptz not null default now(),
  unique (funcionario_id, data, percentual)
);

-- ============ absenteísmo ============
create table if not exists public.tipos_ausencia (
  id smallserial primary key,
  codigo text not null unique,
  descricao text not null
);

create table if not exists public.absenteismo (
  id uuid primary key default gen_random_uuid(),
  funcionario_id uuid not null references public.funcionarios(id) on delete cascade,
  data date not null,
  tipo_id smallint not null references public.tipos_ausencia(id),
  motivo text,
  periodo text not null default 'INTEGRAL' check (periodo in ('MANHA','TARDE','INTEGRAL')),
  anexo_url text,
  created_at timestamptz not null default now(),
  unique (funcionario_id, data, tipo_id)
);

-- ============ pendências (automáticas) x tarefas (manuais) ============
create table if not exists public.pendencias (
  id uuid primary key default gen_random_uuid(),
  tipo text not null check (tipo in ('APROPRIACAO_INCOMPLETA','SEM_APROPRIACAO','EMAIL_HE_PENDENTE','FALTA_INFO')),
  funcionario_id uuid references public.funcionarios(id) on delete set null,
  data_ref date,
  descricao text not null,
  prioridade text not null default 'MEDIA' check (prioridade in ('ALTA','MEDIA','BAIXA')),
  status text not null default 'ABERTA' check (status in ('ABERTA','RESOLVIDA','CANCELADA')),
  origem_regra text not null, -- ex: motor_regras.apropriacao
  registro_tipo text,         -- presencas|apropriacoes|horas_extras|emails
  registro_id uuid,
  responsavel_id uuid references public.funcionarios(id),
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

-- Idempotência: UNIQUE com COALESCE para tratar NULLs (UNIQUE simples ignora NULL)
create unique index if not exists uq_pendencias_idempotente on public.pendencias
  (tipo, coalesce(funcionario_id, '00000000-0000-0000-0000-000000000000'::uuid),
   coalesce(data_ref, '1900-01-01'::date), coalesce(registro_id, '00000000-0000-0000-0000-000000000000'::uuid));

create table if not exists public.tarefas (
  id uuid primary key default gen_random_uuid(),
  titulo text not null,
  descricao text,
  status text not null default 'A_FAZER' check (status in ('A_FAZER','EM_ANDAMENTO','AGUARDANDO','CONCLUIDO')),
  prioridade text not null default 'MEDIA' check (prioridade in ('ALTA','MEDIA','BAIXA')),
  responsavel_id uuid references public.funcionarios(id),
  criador_id uuid references public.usuarios(id),
  prazo date,
  categoria text,
  conclusao_em timestamptz,
  pendencia_origem_id uuid unique references public.pendencias(id),
  created_at timestamptz not null default now()
);

create table if not exists public.tarefa_checklists (
  id uuid primary key default gen_random_uuid(),
  tarefa_id uuid not null references public.tarefas(id) on delete cascade,
  titulo text not null,
  feito boolean not null default false
);

create table if not exists public.tarefa_comentarios (
  id uuid primary key default gen_random_uuid(),
  tarefa_id uuid not null references public.tarefas(id) on delete cascade,
  autor_id uuid references public.usuarios(id),
  texto text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.tarefa_anexos (
  id uuid primary key default gen_random_uuid(),
  tarefa_id uuid not null references public.tarefas(id) on delete cascade,
  arquivo_url text not null, -- Supabase Storage
  nome text,
  created_at timestamptz not null default now()
);

-- ============ e-mails / notificações / auditoria ============
create table if not exists public.emails (
  id uuid primary key default gen_random_uuid(),
  hora_extra_id uuid references public.horas_extras(id) on delete set null,
  destinatario text not null,
  assunto text not null,
  corpo text not null,
  status text not null default 'PENDENTE' check (status in ('PENDENTE','ENVIADO','ERRO')),
  erro text,
  enviado_em timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.notificacoes (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references public.usuarios(id) on delete cascade,
  titulo text not null,
  mensagem text,
  lida boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.historico_alteracoes (
  id bigserial primary key,
  usuario_id uuid references public.usuarios(id),
  data_hora timestamptz not null default now(),
  tabela text not null,
  registro_id uuid,
  acao text not null,
  antes jsonb,
  depois jsonb
);

-- ============ indexes operacionais ============
create index if not exists idx_funcionarios_setor on public.funcionarios(setor);
create index if not exists idx_funcionarios_ativo on public.funcionarios(ativo);
create index if not exists idx_presencas_data on public.presencas(data);
create index if not exists idx_apropriacoes_func_data on public.apropriacoes(funcionario_id, data);
create index if not exists idx_he_func_data on public.horas_extras(funcionario_id, data);
create index if not exists idx_pendencias_status on public.pendencias(status);
create index if not exists idx_pendencias_func_data on public.pendencias(funcionario_id, data_ref);
create index if not exists idx_tarefas_status on public.tarefas(status);
create index if not exists idx_emails_status on public.emails(status);
create index if not exists idx_abs_data on public.absenteismo(data);

-- ============ updated_at automático ============
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists trg_usuarios_updated on public.usuarios;
create trigger trg_usuarios_updated before update on public.usuarios
  for each row execute function public.set_updated_at();

drop trigger if exists trg_funcionarios_updated on public.funcionarios;
create trigger trg_funcionarios_updated before update on public.funcionarios
  for each row execute function public.set_updated_at();

-- ============ carga prevista (jornada + feriado + desligamento) ============
-- Usada pelo motor de regras (ETAPA 9) e pela view de saldo.
create or replace function public.carga_prevista(p_funcionario uuid, p_data date)
returns numeric(5,2) language plpgsql stable as $$
declare
  v_jornada uuid;
  v_dow int;
  v_carga numeric(5,2);
  v_deslig date;
begin
  select jornada_id, desligamento into v_jornada, v_deslig
  from public.funcionarios where id = p_funcionario;
  if not found then return 0; end if;
  if v_deslig is not null and p_data > v_deslig then return 0; end if;
  if exists (select 1 from public.feriados where data = p_data) then return 0; end if;
  if v_jornada is null then return 0; end if;
  v_dow := extract(dow from p_data);
  select carga_horas into v_carga from public.jornada_horarios
  where jornada_id = v_jornada and dia_semana = v_dow;
  return coalesce(v_carga, 0);
end $$;

-- ============ views ============
-- Saldo diário: previsto x apropriado (base do dashboard e da ETAPA 9)
create or replace view public.vw_apropriacao_diaria as
select
  f.id as funcionario_id,
  f.matricula,
  f.nome,
  d.data,
  public.carga_prevista(f.id, d.data) as carga_prevista,
  coalesce(sum(a.horas), 0) as total_apropriado,
  coalesce(sum(a.horas), 0) - public.carga_prevista(f.id, d.data) as saldo
from public.funcionarios f
cross join (select distinct data from public.presencas
            union select distinct data from public.apropriacoes) d
left join public.apropriacoes a
  on a.funcionario_id = f.id and a.data = d.data
group by f.id, f.matricula, f.nome, d.data;

create or replace view public.vw_pendencias_abertas as
select * from public.pendencias where status = 'ABERTA';
