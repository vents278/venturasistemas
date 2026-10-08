-- ETAPA 3 (fix) — privilégios para as roles do Supabase.
-- Tabelas criadas pelo SQL Editor pertencem ao postgres; sem GRANT, service_role/authenticated recebem 42501.
grant all on all tables in schema public to service_role;
grant all on all sequences in schema public to service_role;
grant execute on all functions in schema public to service_role, authenticated;

grant select, insert, update, delete on all tables in schema public to authenticated;
grant usage, select on all sequences in schema public to authenticated;

-- Garante o mesmo para tabelas futuras criadas via SQL Editor (rodar de novo se criar tabela nova).
alter default privileges in schema public grant all on tables to service_role;
alter default privileges in schema public grant select, insert, update, delete on tables to authenticated;
