-- ============================================================
--  DE COMMERCIËLE DUGOUT · migratie 3 voor SportsSpeakers / SportSpreker
--
--  Maakt het mogelijk om aanvraagmails automatisch als kaart in te laden,
--  en zorgt dat dezelfde aanvraag nooit twee keer op het bord komt.
--
--  Plak dit volledig in: Supabase → SQL Editor → New query → Run
--  Veilig om meerdere keren te draaien (alles is "if not exists").
--
--  VOLGORDE: draai eerst migratie 2 (supabase-migratie-spsp-toekomst.sql).
--
--  Deze migratie is los te draaien: de app werkt daarna precies zoals nu.
--  Bestaande kaarten blijven ongemoeid en gelden als handmatig aangemaakt.
-- ============================================================

-- 1) Waar komt deze kaart vandaan?
--    ''            = handmatig aangemaakt in de app (alles wat er nu staat)
--    'mail-import' = automatisch ingeladen uit een opgeslagen aanvraagmail
alter table public.deals
  add column if not exists bron text not null default '';

-- 2) Herkomst van een automatisch ingeladen kaart
alter table public.deals add column if not exists bron_msgid   text;         -- Message-ID uit de EML = de vingerafdruk
alter table public.deals add column if not exists bron_bestand text;         -- bestandsnaam zoals hij in de map stond
alter table public.deals add column if not exists bron_door    text;         -- wie de import draaide
alter table public.deals add column if not exists bron_op      timestamptz;  -- wanneer

-- 3) De dubbelbeveiliging.
--    Elke aanvraagmail heeft een Message-ID die de mailserver zelf heeft
--    toegekend en die in het EML-bestand meekomt. Door die uniek te maken,
--    weigert de database een tweede kaart voor dezelfde aanvraag — ongeacht
--    wie scant, wanneer, vanaf welke laptop of onder welke bestandsnaam.
--
--    Het is een PARTIËLE index: alleen rijen mét een Message-ID doen mee.
--    Handmatig aangemaakte kaarten hebben er geen en blijven dus buiten schot.
--
--    Let op: dit legt vast dat één aanvraagmail één kaart oplevert. Dat is de
--    afspraak (twee gevraagde sprekers komen samen op één kaart). Wil je daar
--    ooit van af, dan moet deze index mee veranderen.
create unique index if not exists deals_bron_msgid_key
  on public.deals (bron_msgid)
  where bron_msgid is not null;

-- ============================================================
--  Controle achteraf
-- ============================================================
-- Staan de kolommen erin? (hoort 5 regels te geven)
-- select column_name from information_schema.columns
--  where table_schema='public' and table_name='deals'
--    and column_name in ('bron','bron_msgid','bron_bestand','bron_door','bron_op')
--  order by column_name;

-- Verdeling handmatig vs. automatisch.
-- Vlak na deze migratie hoort dit één regel te geven: '' met alle bestaande kaarten.
-- select coalesce(nullif(bron,''),'(handmatig)') as bron, count(*)
--   from public.deals group by 1 order by 1;

-- Staat de dubbelbeveiliging er?
-- select indexname from pg_indexes
--  where schemaname='public' and tablename='deals' and indexname='deals_bron_msgid_key';
