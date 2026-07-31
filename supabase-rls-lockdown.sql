-- ============================================================
--  DE COMMERCIËLE DUGOUT · RLS lockdown
--  Draai dit NADAT de login werkt (Supabase → SQL Editor → Run).
--  Hierna kan ALLEEN een ingelogde gebruiker bij de data;
--  zonder login (anon) is er geen toegang meer.
-- ============================================================

-- 1) Verwijder de tijdelijke open (anon) policy
drop policy if exists "dugout_anon_full_access" on public.deals;

-- 2) Alleen ingelogde (authenticated) gebruikers mogen lezen/schrijven
drop policy if exists "dugout_authenticated_access" on public.deals;
create policy "dugout_authenticated_access"
  on public.deals
  for all
  to authenticated
  using (true)
  with check (true);

-- RLS staat al aan op public.deals (uit het hoofdschema). Voor de zekerheid:
alter table public.deals enable row level security;

-- ============================================================
--  NA het runnen, nog TWEE dingen in het dashboard:
--
--  A) Zelf-registratie uitzetten (belangrijk!)
--     Authentication -> Sign In / Providers -> Email
--     -> "Allow new users to sign up" UIT.
--     Anders kan iemand met de publishable key zelf een account
--     aanmaken en zo bij de data komen. Jij maakt voortaan zelf
--     de accounts aan via Authentication -> Users -> Add user.
--
--  B) (Aanbevolen) Authentication -> URL Configuration:
--     zet de Site URL op het straks gedeployde adres van de app.
-- ============================================================
