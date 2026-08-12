-- ============================================================
--  DE COMMERCIËLE DUGOUT · Testdata opschonen (v2 — VEILIGE selectie)
--  Draai in: Supabase → SQL Editor → New query
--
--  ⚠ LET OP: de oude versie van dit script selecteerde testdata op
--  contactpersoon-VOORnamen (Geoffrey, Dille, Bart, …). Sinds de
--  migratie "namen-kort" (supabase-migratie-namen-kort.sql) gebruiken
--  ECHTE rijen óók voornamen (Bart, Dille, Michelle, …). Op owner
--  selecteren zou nu dus ECHTE data wissen.
--
--  Deze v2 herkent de oude demo-rijen aan hun FICTIEVE contact-
--  e-mailadressen uit de demo-dataset — die komen in echte data niet voor.
--
--  STAP 1 — draai eerst ALLEEN deze select en controleer dat dit
--  inderdaad allemaal fictieve testkaarten zijn:
-- ============================================================

select id, klant, merk, atleet, contact, email, owner, unit, status, waarde, laatste
  from public.deals
 where email in (
   's.bosch@unive.nl','mark.visser@unive.nl','s.degroot@arag.nl','r.smit@arag.nl',
   'm.dewit@unive.nl','noor@upfront.nl','d.bakker@eurojackpot.eu','m.devries@rexona.com',
   'partnerships@defensie.nl','w.jansen@houseofathletes.nl','p.hendriks@unive.nl'
 )
 order by klant, merk;

-- ============================================================
--  STAP 2 — klopt het overzicht hierboven? Draai dan dit blok:
--  (maakt eerst een backup-tabel, verwijdert daarna de testrijen)
-- ============================================================

-- begin;
--
-- create table if not exists public.deals_backup_testdata_20260812 as
--   select * from public.deals
--    where email in (
--      's.bosch@unive.nl','mark.visser@unive.nl','s.degroot@arag.nl','r.smit@arag.nl',
--      'm.dewit@unive.nl','noor@upfront.nl','d.bakker@eurojackpot.eu','m.devries@rexona.com',
--      'partnerships@defensie.nl','w.jansen@houseofathletes.nl','p.hendriks@unive.nl'
--    );
--
-- delete from public.deals
--  where email in (
--    's.bosch@unive.nl','mark.visser@unive.nl','s.degroot@arag.nl','r.smit@arag.nl',
--    'm.dewit@unive.nl','noor@upfront.nl','d.bakker@eurojackpot.eu','m.devries@rexona.com',
--    'partnerships@defensie.nl','w.jansen@houseofathletes.nl','p.hendriks@unive.nl'
--  );
--
-- commit;

-- ============================================================
--  CONTROLE na afloop: dit hoort alleen nog echte namen te tonen
-- ============================================================
-- select distinct owner from public.deals order by owner;
