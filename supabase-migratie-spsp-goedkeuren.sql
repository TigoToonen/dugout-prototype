-- ============================================================
--  DE COMMERCIËLE DUGOUT · migratie 5 voor SportsSpeakers / SportSpreker
--
--  De goedkeuring van een automatisch ingeladen aanvraag.
--
--  Plak dit volledig in: Supabase → SQL Editor → New query → Run
--  Veilig om meerdere keren te draaien.
--
--  VOLGORDE: draai dit ná migratie 4 (supabase-migratie-spsp-import-2.sql).
-- ============================================================

-- Een kaart die uit een aanvraagmail komt, moet eerst door een mens worden
-- nagekeken. Zolang deze kolommen leeg zijn draagt de kaart in de app een
-- rode badge "Nog goed te keuren"; zodra ze gevuld zijn wordt die groen.
--
-- Geen aparte statuskolom: leeg of gevuld is de status. Zo kan er niets uit
-- de pas gaan lopen. Handmatig aangemaakte kaarten hebben geen goedkeuring
-- nodig en blijven allebei de kolommen gewoon leeg — die herken je aan
-- bron = '' (zie migratie 3).

alter table public.deals add column if not exists goedgekeurd_op   timestamptz;
alter table public.deals add column if not exists goedgekeurd_door text;

-- ============================================================
--  Controle achteraf
-- ============================================================
-- Hoort 2 regels te geven:
-- select column_name from information_schema.columns
--  where table_schema='public' and table_name='deals'
--    and column_name in ('goedgekeurd_op','goedgekeurd_door')
--  order by column_name;

-- Hoeveel ingeladen aanvragen wachten nog op goedkeuring?
-- (vlak na deze migratie: 0 regels, er is nog niets ingeladen)
-- select case when goedgekeurd_op is null then 'nog goed te keuren'
--             else 'goedgekeurd' end as status, count(*)
--   from public.deals where bron = 'mail-import' group by 1 order by 1;
