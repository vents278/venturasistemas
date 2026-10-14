-- Status manual da preventiva.
-- Quando true, o status informado pelo gestor tem precedência sobre o cálculo
-- automático (programação × presença × OS). O status CANCELADA continua terminal.
-- Rows existentes permanecem automáticas (default false).

alter table public.preventivas
  add column if not exists status_manual boolean not null default false;
