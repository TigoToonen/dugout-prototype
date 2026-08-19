-- ============================================================
--  DE COMMERCIËLE DUGOUT · migratie voor het tabblad
--  "SportsSpeakers / SportSpreker"
--
--  Plak dit volledig in: Supabase → SQL Editor → New query → Run
--  Draai dit VÓÓR de nieuwe index.html live gaat.
--  Veilig om meerdere keren te draaien (alles is "if not exists").
--
--  Bestaande kaarten blijven ongemoeid: die krijgen automatisch
--  pipeline = 'commercie' en blijven dus in de huidige pipeline staan.
-- ============================================================

-- 1) In welke pipeline hoort deze kaart thuis?
--    'commercie' = de bestaande Commerciële Dugout (standaard)
--    'spsp'      = het nieuwe tabblad SportsSpeakers / SportSpreker
alter table public.deals
  add column if not exists pipeline text not null default 'commercie';

-- 2) Extra velden voor een sprekersaanvraag
alter table public.deals add column if not exists label    text;      -- SportsSpeakers (NL) / SportSpreker (BE)
alter table public.deals add column if not exists spreker  text;      -- gevraagde spreker(s)
alter table public.deals add column if not exists ev_datum date;      -- datum van het evenement
alter table public.deals add column if not exists ev_tijd  text;      -- tijdstip, bijv. "19:00 - 20:00"
alter table public.deals add column if not exists locatie  text;      -- locatie van het evenement
alter table public.deals add column if not exists aantal   integer;   -- aantal personen
alter table public.deals add column if not exists thema    text;      -- thema en doel

-- 3) Vangnet: rijen van vóór deze migratie expliciet op 'commercie'
update public.deals set pipeline = 'commercie' where pipeline is null;

-- 4) Index, zodat het filteren per pipeline snel blijft
create index if not exists deals_pipeline_idx on public.deals (pipeline);

-- ============================================================
--  Controle achteraf — hoort 2 regels te geven zodra er
--  aanvragen in staan, en anders alleen 'commercie'.
-- ============================================================
-- select pipeline, count(*) from public.deals group by pipeline order by 1;
