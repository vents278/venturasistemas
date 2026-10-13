-- Paridade com sistema antigo: tipo DESLOCADO_SEM_OS nas pendências.
alter table public.pendencias drop constraint if exists pendencias_tipo_check;
alter table public.pendencias add constraint pendencias_tipo_check check
  (tipo in ('APROPRIACAO_INCOMPLETA','SEM_APROPRIACAO','DESLOCADO_SEM_OS','EMAIL_HE_PENDENTE','FALTA_INFO'));
