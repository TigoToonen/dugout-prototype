-- ============================================================
--  DE COMMERCIËLE DUGOUT · Migratie "Reminderdatum contract"
--  Draai in: Supabase → SQL Editor → New query → Run
--  Veilig om meerdere keren te draaien.
--
--  De reminder vóór de contract-einddatum is voortaan een ECHTE datum
--  (datumkiezer in de app) i.p.v. "X maanden vooraf". Zodra die datum
--  is bereikt verschijnt de kaart bij "Aandacht nodig".
--  Bestaande maand-reminders worden automatisch omgerekend.
-- ============================================================

alter table public.deals add column if not exists reminder_datum date;

-- Bestaande "X maanden vooraf"-reminders omrekenen naar een concrete datum
update public.deals
   set reminder_datum = (einddatum - (reminder_maanden || ' months')::interval)::date
 where reminder_datum is null
   and einddatum is not null
   and reminder_maanden is not null;

create index if not exists deals_reminder_datum_idx on public.deals (reminder_datum);

-- (De oude kolom reminder_maanden blijft staan maar wordt door de app
--  niet meer gebruikt; opruimen kan later desgewenst met:
--  alter table public.deals drop column reminder_maanden;)
