-- ============================================================
--  Commerciële Dugout — Realtime live sync aanzetten
--  Draai dit ÉÉN keer in Supabase → SQL Editor.
--  Zonder dit komt er geen enkele live-wijziging binnen.
--  Bevat GEEN persoonsgegevens; veilig om te bewaren.
-- ============================================================

-- 1) Zet de deals-tabel in de realtime-publicatie (idempotent: 2x draaien mag).
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename  = 'deals'
  ) then
    alter publication supabase_realtime add table public.deals;
  end if;
end $$;

-- 2) Volledige oude rij meesturen bij UPDATE/DELETE.
--    Nodig zodat RLS én de "welke rij is verwijderd"-info correct doorkomen.
alter table public.deals replica identity full;

-- Controle (optioneel): moet 1 regel 'deals' teruggeven.
-- select schemaname, tablename from pg_publication_tables
-- where pubname = 'supabase_realtime' and tablename = 'deals';
