-- ETAPA 3 — Seed: parâmetros do negócio (jornadas, status, ausências, perfis, feriados 2026)
-- dia_semana: 0=dom .. 6=sáb

insert into public.perfis_usuario (nome) values ('ADMIN'), ('GESTOR'), ('OPERADOR')
on conflict (nome) do nothing;

insert into public.status_presenca (codigo, descricao, exige_apropriacao, conta_absenteismo) values
  ('PRESENTE', 'Presente', true, false),
  ('DESLOCADO', 'Deslocado', true, false),
  ('FOLGA', 'Folga', false, false),
  ('FALTA', 'Falta', false, true),
  ('FERIAS', 'Férias', false, false),
  ('AFASTADO', 'Afastado', false, false),
  ('TREINAMENTO', 'Treinamento', false, false)
on conflict (codigo) do update set
  descricao = excluded.descricao,
  exige_apropriacao = excluded.exige_apropriacao,
  conta_absenteismo = excluded.conta_absenteismo;

insert into public.tipos_ausencia (codigo, descricao) values
  ('FALTA', 'Falta'),
  ('ATESTADO', 'Atestado médico'),
  ('LICENCA', 'Licença'),
  ('FOLGA', 'Folga'),
  ('FERIAS', 'Férias'),
  ('OUTROS', 'Outros')
on conflict (codigo) do nothing;

-- Jornadas
insert into public.jornadas (codigo, nome, descricao) values
  ('ADM', 'ADM', 'Administrativo seg-sex'),
  ('DESLOC_TARDE', 'Deslocado tarde', 'Deslocado 15:00-23:20'),
  ('DESLOC_NOTURNO', 'Deslocado noturno', 'Deslocado 23:00-07:20, atravessa meia-noite')
on conflict (codigo) do update set nome = excluded.nome, descricao = excluded.descricao;

-- Horários ADM: seg(1)-qui(4) 07:00-17:00 9h / sex(5) 07:00-16:00 8h / sab-dom sem carga
insert into public.jornada_horarios (jornada_id, dia_semana, inicio, fim, carga_horas, intervalo_min, atravessa_meia_noite, exige_apropriacao)
select id, d.dia, d.ini, d.fim, d.carga, 60, false, true
from public.jornadas j cross join (values
  (1, '07:00'::time, '17:00'::time, 9.00),
  (2, '07:00'::time, '17:00'::time, 9.00),
  (3, '07:00'::time, '17:00'::time, 9.00),
  (4, '07:00'::time, '17:00'::time, 9.00),
  (5, '07:00'::time, '16:00'::time, 8.00)
) as d(dia, ini, fim, carga)
where j.codigo = 'ADM'
on conflict (jornada_id, dia_semana) do update set
  inicio = excluded.inicio, fim = excluded.fim, carga_horas = excluded.carga_horas;

-- Deslocado tarde: seg-sex 15:00-23:20 7.33h
insert into public.jornada_horarios (jornada_id, dia_semana, inicio, fim, carga_horas, intervalo_min, atravessa_meia_noite, exige_apropriacao)
select id, d.dia, '15:00'::time, '23:20'::time, 7.33, 0, false, true
from public.jornadas j cross join (values (1),(2),(3),(4),(5)) as d(dia)
where j.codigo = 'DESLOC_TARDE'
on conflict (jornada_id, dia_semana) do update set
  inicio = excluded.inicio, fim = excluded.fim, carga_horas = excluded.carga_horas,
  atravessa_meia_noite = false;

-- Deslocado noturno: seg-sex 23:00-07:20 7.33h (atravessa meia-noite)
insert into public.jornada_horarios (jornada_id, dia_semana, inicio, fim, carga_horas, intervalo_min, atravessa_meia_noite, exige_apropriacao)
select id, d.dia, '23:00'::time, '07:20'::time, 7.33, 0, true, true
from public.jornadas j cross join (values (1),(2),(3),(4),(5)) as d(dia)
where j.codigo = 'DESLOC_NOTURNO'
on conflict (jornada_id, dia_semana) do update set
  inicio = excluded.inicio, fim = excluded.fim, carga_horas = excluded.carga_horas,
  atravessa_meia_noite = true;

-- Feriados nacionais 2026 (exemplo; ajustar conforme calendário oficial)
insert into public.feriados (data, descricao, tipo) values
  ('2026-01-01', 'Confraternização Universal', 'NACIONAL'),
  ('2026-04-03', 'Sexta-feira Santa', 'NACIONAL'),
  ('2026-04-21', 'Tiradentes', 'NACIONAL'),
  ('2026-05-01', 'Dia do Trabalho', 'NACIONAL'),
  ('2026-09-07', 'Independência', 'NACIONAL'),
  ('2026-10-12', 'N. Sra. Aparecida', 'NACIONAL'),
  ('2026-11-02', 'Finados', 'NACIONAL'),
  ('2026-11-15', 'Proclamação da República', 'NACIONAL'),
  ('2026-12-25', 'Natal', 'NACIONAL')
on conflict (data) do nothing;
