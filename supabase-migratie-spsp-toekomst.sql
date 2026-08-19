-- ============================================================
--  DE COMMERCIËLE DUGOUT · migratie 2 voor SportsSpeakers / SportSpreker
--
--  Nodig omdat óók het tabblad "Toekomst" nu per pipeline werkt.
--  Draai dit in: Supabase → SQL Editor → New query → Run
--  Veilig om meerdere keren te draaien.
--
--  (Migratie 1 = supabase-migratie-spsp-sportspreker.sql, die ging over deals.)
-- ============================================================

alter table public.toekomst
  add column if not exists pipeline text not null default 'commercie';

update public.toekomst set pipeline = 'commercie' where pipeline is null;

create index if not exists toekomst_pipeline_idx on public.toekomst (pipeline);

-- Controle:
-- select pipeline, count(*) from public.toekomst group by pipeline order by 1;
