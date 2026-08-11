-- ============================================================
--  DE COMMERCIËLE DUGOUT · Migratie "Datum volgende actie"
--  Draai in: Supabase → SQL Editor → New query → Run
--  Veilig om meerdere keren te draaien (IF NOT EXISTS).
--
--  Nieuw veld: wanneer moet dit contact weer opgepakt worden?
--  De app gebruikt dit veld voortaan als basis voor "Aandacht nodig"
--  (i.p.v. de vaste 14-dagenregel; die blijft alleen gelden als
--  er géén datum is ingepland).
-- ============================================================

alter table public.deals add column if not exists volgende_actie date;

-- Handige index: het dashboard filtert/sorteert hierop
create index if not exists deals_volgende_actie_idx on public.deals (volgende_actie);
