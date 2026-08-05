-- ============================================================
--  DE COMMERCIËLE DUGOUT · Migratie "Athletes / Dug Out"
--  Voegt de extra velden toe voor atleet- en influencerdeals.
--  Draai dit ná het hoofdschema in: Supabase → SQL Editor → Run.
--  Veilig om meerdere keren te draaien (IF NOT EXISTS).
-- ============================================================

alter table public.deals add column if not exists atleet           text;
alter table public.deals add column if not exists sport            text;
alter table public.deals add column if not exists soort_deal       text;   -- Arbeidsovereenkomst / Sponsorovereenkomst / Influencers / Commissiedeal
alter table public.deals add column if not exists hoa_type         text;   -- Atletenmanagement / Influencers
alter table public.deals add column if not exists startdatum       date;
alter table public.deals add column if not exists einddatum        date;
alter table public.deals add column if not exists reminder_maanden integer; -- 12 / 6 / 3 maanden vóór einddatum

-- Handige index om aflopende contracten snel te vinden
create index if not exists deals_einddatum_idx on public.deals (einddatum);
