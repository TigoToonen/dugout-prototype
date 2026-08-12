-- ============================================================
--  DE COMMERCIËLE DUGOUT · Migratie "Korte namen contactpersoon HoS"
--  Draai in: Supabase → SQL Editor → New query → Run
--  Veilig om meerdere keren te draaien (idempotent).
--
--  Voortaan voornamen, behalve waar de achternaam nodig is:
--  Koen Hermens · Ruud Koedijk · Ruud van Doornik · Tom Schouten · Tom Taminiau
--  (en spellingscorrectie: Hermes -> Hermens)
-- ============================================================

update public.deals set owner='Bart'         where owner='Bart Gabriels';
update public.deals set owner='Bjorn'        where owner='Bjorn Bakker';
update public.deals set owner='Dille'        where owner='Dille Rikkert';
update public.deals set owner='Ederik'       where owner='Ederik Tiessen';
update public.deals set owner='Joep'         where owner='Joep Wouters van den Oudenweijer';
update public.deals set owner='Koen Hermens' where owner in ('Koen Hermes','Koen');
update public.deals set owner='Max'          where owner='Max van der Ven';
update public.deals set owner='Michelle'     where owner='Michelle Geldhof';
update public.deals set owner='Samuel'       where owner in ('Samuel Ardies','Samuel Aldries');

-- Controle (optioneel):
-- select distinct owner from public.deals order by owner;
