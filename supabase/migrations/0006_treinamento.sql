-- Treinamento: funcionário ainda não ativo entra sozinho na grade como TREINAMENTO.
alter table public.funcionarios add column if not exists em_treinamento boolean not null default false;
