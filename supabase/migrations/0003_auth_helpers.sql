-- ETAPA 4 — helpers de autorização para endurecer RLS por perfil.
-- Uso futuro: policies com public.meu_perfil() = 'ADMIN', etc.

create or replace function public.meu_perfil()
returns text language sql stable security definer set search_path = public as $$
  select p.nome
  from public.usuarios u
  join public.perfis_usuario p on p.id = u.perfil_id
  where u.id = auth.uid()
$$;

create or replace function public.sou_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select coalesce(public.meu_perfil() = 'ADMIN', false)
$$;

-- Exemplo de endurecimento (auditoria só ADMIN lê; demais módulos mantêm baseline da 0002):
-- Descomente quando houver usuários reais, para não se travar fora do sistema.
-- drop policy if exists p_read on public.historico_alteracoes;
-- create policy p_read_admin on public.historico_alteracoes
--   for select to authenticated using (public.sou_admin());
