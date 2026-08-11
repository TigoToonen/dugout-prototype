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
--  Personen:
--  · Ederik Tiessen en Tom Taminiau zijn toegevoegd aan de keuzelijst (app)
--  · Ivan Spijkerstra, Mark van den Akker en Trisztan Post (SPSP) zijn uit
--    de keuzelijst gehaald; bestaande deals op hun naam blijven leesbaar
--  · Naamscorrectie Sam: "Samuel Aldries" -> "Samuel Ardies", ook in de data:
-- ============================================================
update public.deals set owner = 'Samuel Ardies' where owner = 'Samuel Aldries';
