-- ============================================================
--  DE COMMERCIËLE DUGOUT · Migratie "Merk bovenaan"
--  Draai in: Supabase → SQL Editor → New query → Run
--
--  Wat dit doet (feedback commercieel overleg 11-8-2026):
--  · klant  = voortaan het MERK (staat bovenaan de kaart)
--  · merk   = voortaan het PARTNERSHIP (bijv. Feyenoord bij Univé; leeg mag)
--  · atleet = de atleet/influencer (alleen bij units Atleten/Influencers)
--
--  Concreet:
--  1. Bij atleet-deals stond de atleet in 'klant' en het merk in 'merk'
--     -> atleet wordt overgezet naar de atleet-kolom, het merk komt in 'klant'.
--  2. Bij o.a. Samsung/TCL/Gamma stond het merk dubbel (klant én merk)
--     -> de dubbeling in 'merk' wordt leeggemaakt.
--
--  Veilig om 2x te draaien (idempotent) · begint met een backup-tabel.
-- ============================================================
begin;

-- 0) Backup van de huidige stand (blijft staan; later op te ruimen met
--    "drop table public.deals_backup_20260811;")
create table if not exists public.deals_backup_20260811 as
  select * from public.deals;

-- 1) Atleet invullen vanuit de oude klant-kolom (alleen waar die nog leeg is)
update public.deals
   set atleet = klant
 where unit in ('Atleten','Influencers')
   and (atleet is null or btrim(atleet) = '')
   and merk is not null and btrim(merk) <> ''
   and klant <> merk;

-- 2) Merk bovenaan: bij atleet-deals verhuist het merk naar 'klant'
update public.deals
   set klant = merk
 where unit in ('Atleten','Influencers')
   and merk is not null and btrim(merk) <> ''
   and klant <> merk;

-- 3) Dubbelingen weg: waar 'merk' hetzelfde is als 'klant' is er geen apart
--    partnership -> leegmaken (fixt "twee keer Samsung" op de kaart)
update public.deals
   set merk = ''
 where merk = klant;

commit;

-- ============================================================
--  CONTROLE (optioneel, na het draaien):
--  Verwacht: bij atleet-deals staat het merk in klant en de atleet in atleet;
--  nergens meer merk = klant.
-- ============================================================
-- select id, unit, klant as merk_bovenaan, atleet, merk as partnership, status
--   from public.deals order by unit, klant;
-- select count(*) as dubbel from public.deals where merk = klant and btrim(merk) <> '';
