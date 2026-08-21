-- ============================================================
--  DE COMMERCIËLE DUGOUT · migratie 4 voor SportsSpeakers / SportSpreker
--
--  Verplaatst de dubbelbeveiliging van de Message-ID naar een
--  vingerafdruk die uit de aanvraag zelf wordt berekend.
--
--  Plak dit volledig in: Supabase → SQL Editor → New query → Run
--  Veilig om meerdere keren te draaien.
--
--  VOLGORDE: draai dit ná migratie 3 (supabase-migratie-spsp-import.sql).
--  Er is nog niets ingeladen, dus er gaat geen data verloren.
-- ============================================================

-- WAAROM
-- ------
-- De Message-ID wordt door de mailserver toegekend aan één specifieke mail.
-- Wordt diezelfde aanvraag doorgestuurd — van info@ naar een collega, of
-- tussen collega's onderling — dan krijgt die kopie een NIEUWE Message-ID.
-- Twee mensen die elk hun eigen kopie opslaan, zouden zo twee kaarten voor
-- dezelfde aanvraag krijgen.
--
-- De aanvraag zelf verandert daarbij niet. Daarom rekenen we de vingerafdruk
-- voortaan uit de inhoud: label, e-mailadres, gevraagde spreker(s), datum en
-- de vrije tekst. Die is gelijk voor het origineel én elke doorgestuurde
-- kopie, en blijft werken als de mailroute later verandert.
--
-- De Message-ID blijft gewoon opgeslagen — handig om terug te zoeken —
-- maar is niet langer waar de dubbelbeveiliging op steunt.

-- 1) De nieuwe vingerafdruk
alter table public.deals
  add column if not exists bron_vingerafdruk text;

-- 2) De dubbelbeveiliging verhuist ernaartoe.
--    Partieel: alleen rijen mét een vingerafdruk doen mee, dus handmatig
--    aangemaakte kaarten blijven buiten schot.
drop index if exists public.deals_bron_msgid_key;

create unique index if not exists deals_bron_vingerafdruk_key
  on public.deals (bron_vingerafdruk)
  where bron_vingerafdruk is not null;

-- ============================================================
--  Controle achteraf
-- ============================================================
-- Hoort precies één regel te geven: deals_bron_vingerafdruk_key
-- select indexname from pg_indexes
--  where schemaname='public' and tablename='deals'
--    and indexname in ('deals_bron_msgid_key','deals_bron_vingerafdruk_key');

-- Hoort de kolom te tonen:
-- select column_name from information_schema.columns
--  where table_schema='public' and table_name='deals'
--    and column_name='bron_vingerafdruk';
