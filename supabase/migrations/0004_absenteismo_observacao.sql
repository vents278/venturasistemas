-- ETAPA 14 — campo observacao em absenteismo (seção 15 do spec).
alter table public.absenteismo add column if not exists observacao text;
