-- ============================================================
--  DE COMMERCIËLE DUGOUT · Migratie "Units naar Athletes"
--  Draai in: Supabase → SQL Editor → New query → Run
--  Veilig om meerdere keren te draaien (idempotent).
--
--  Nieuwe unit-indeling (actiepunten 11-8-2026):
--  Athletes · BAT · HoS Algemeen · HYROX · JODP · Schaatsen · SPEX · TEN · ZAR
--  · "Atleten" en "Influencers"          -> Athletes
--  · "SportsSpeakers" en "SportSpreker"  -> Athletes (keuze Tigo)
--  · "TEN" is toegevoegd als keuze in de app (geen datamigratie nodig)
-- ============================================================

update public.deals
   set unit = 'Athletes'
 where unit in ('Atleten','Influencers','SportsSpeakers','SportSpreker');

-- ook eventuele Toekomst-items mee
update public.toekomst
   set unit = 'Athletes'
 where unit in ('Atleten','Influencers','SportsSpeakers','SportSpreker');

-- Controle (optioneel): welke units komen nu voor?
-- select unit, count(*) from public.deals group by unit order by unit;

-- ============================================================
--  Personen (volgt zodra de namen bekend zijn):
--  · hernoeming Sam ("Samuel Aldries" -> juiste naam) gaat straks zo:
--    update public.deals set owner = 'NIEUWE NAAM' where owner = 'Samuel Aldries';
-- ============================================================
