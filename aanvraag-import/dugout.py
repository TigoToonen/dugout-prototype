"""
Schrijft ingelezen aanvragen weg als kaart in de Commerciële Dugout.

Praat rechtstreeks met Supabase over HTTP, met alleen wat er standaard in
Python zit — zodat dit op vijf laptops draait zonder dat er iets
geïnstalleerd hoeft te worden.

INLOGGEGEVENS staan in een bestand BUITEN OneDrive:

    C:\\Users\\<jij>\\.dugout-import.json

    {
      "email": "jouw@houseofsports.nl",
      "wachtwoord": "..."
    }

Buiten OneDrive, zodat het wachtwoord niet meesynchroniseert naar de cloud
en naar andere apparaten. Maak dat bestand zelf aan; het staat nergens in
een repository en wordt nooit gekopieerd.
"""

import json
import urllib.error
import urllib.request
from pathlib import Path

# Zelfde project als de app. De publishable key mag openbaar zijn — hij geeft
# op zichzelf geen toegang; de beveiliging zit op de login.
SUPABASE_URL = "https://qjiyznttmxlmctaqleay.supabase.co"
SUPABASE_ANON = "sb_publishable_a7RD4-HRWQiMoYF_pAPisg_caxVvSKz"

INSTELLINGEN = Path.home() / ".dugout-import.json"

# Deze velden gaan mee naar de database. Alles wat het script verder heeft
# uitgerekend (waarschuwingen, hulpvelden) blijft er bewust buiten.
KAART_VELDEN = [
    "klant", "contact", "functie", "email", "tel", "owner", "unit", "merk",
    "waarde", "fase", "type", "actie", "laatste", "bijgewerkt", "opm", "status",
    "volgende_actie", "pipeline", "label", "spreker", "ev_datum", "ev_tijd",
    "locatie", "aantal", "thema",
    "bron", "bron_msgid", "bron_bestand", "bron_door", "bron_op",
    "bron_vingerafdruk",
]


class DugoutFout(Exception):
    pass


def lees_instellingen(pad=INSTELLINGEN):
    if not Path(pad).exists():
        raise DugoutFout(
            "Geen inloggegevens gevonden.\n"
            "Maak %s aan met daarin:\n"
            '  {"email": "jouw@houseofsports.nl", "wachtwoord": "..."}' % pad)
    gegevens = json.loads(Path(pad).read_text(encoding="utf-8"))
    for sleutel in ("email", "wachtwoord"):
        if not gegevens.get(sleutel):
            raise DugoutFout("'%s' ontbreekt in %s" % (sleutel, pad))
    return gegevens


def _verstuur(pad, gegevens=None, token=None, methode="POST", extra_kop=None):
    koppen = {
        "apikey": SUPABASE_ANON,
        "Content-Type": "application/json",
    }
    if token:
        koppen["Authorization"] = "Bearer " + token
    if extra_kop:
        koppen.update(extra_kop)

    lichaam = json.dumps(gegevens).encode("utf-8") if gegevens is not None else None
    verzoek = urllib.request.Request(SUPABASE_URL + pad, data=lichaam,
                                     headers=koppen, method=methode)
    try:
        with urllib.request.urlopen(verzoek, timeout=30) as antwoord:
            tekst = antwoord.read().decode("utf-8")
            return json.loads(tekst) if tekst.strip() else None
    except urllib.error.HTTPError as fout:
        tekst = fout.read().decode("utf-8", "replace")
        try:
            details = json.loads(tekst)
        except ValueError:
            details = {"message": tekst}
        details["_status"] = fout.code
        raise DugoutFout(details)
    except urllib.error.URLError as fout:
        raise DugoutFout({"message": "Geen verbinding: %s" % fout.reason})


def inloggen(gegevens=None):
    """Levert een token waarmee we mogen schrijven, plus wie er is ingelogd."""
    gegevens = gegevens or lees_instellingen()
    try:
        antwoord = _verstuur("/auth/v1/token?grant_type=password", {
            "email": gegevens["email"],
            "password": gegevens["wachtwoord"],
        })
    except DugoutFout as fout:
        details = fout.args[0] if fout.args else {}
        if isinstance(details, dict) and details.get("_status") == 400:
            raise DugoutFout(
                "Inloggen mislukt — controleer e-mailadres en wachtwoord in %s"
                % INSTELLINGEN)
        raise
    if not antwoord or not antwoord.get("access_token"):
        raise DugoutFout("Inloggen gaf geen token terug")
    return antwoord["access_token"], gegevens["email"]


def is_dubbel(fout):
    """
    Herkent de weigering van de database bij een aanvraag die er al staat.
    23505 is de foutcode voor 'deze waarde bestaat al' — hier dus de
    vingerafdruk, geblokkeerd door deals_bron_vingerafdruk_key.
    """
    details = fout.args[0] if fout.args else {}
    if not isinstance(details, dict):
        return False
    return (str(details.get("code")) == "23505"
            or "vingerafdruk" in str(details.get("message", "")).lower())


def test_verbinding():
    """
    Controleert of inloggen en lezen werken, zonder iets te wijzigen.
    Bedoeld voor het instellen: dan weet je meteen of het klopt, in plaats
    van dat je er bij de eerste echte aanvraag achter komt.
    """
    token, wie = inloggen()
    rijen = _verstuur("/rest/v1/deals?select=id&limit=1", token=token, methode="GET")

    # Staan de kolommen van de import erin? Zo niet, dan wijst de installatie
    # naar een database waar de migraties nog niet gedraaid zijn.
    _verstuur("/rest/v1/deals?select=bron,bron_vingerafdruk,goedgekeurd_op&limit=1",
              token=token, methode="GET")

    return wie, len(rijen or [])


def maak_kaart(kaart, token):
    """
    Zet één aanvraag als kaart in de Dugout.
    Geeft terug: ("nieuw", id) · ("dubbel", None) bij een al bestaande aanvraag.
    """
    rij = {k: kaart[k] for k in KAART_VELDEN if kaart.get(k) is not None}
    try:
        antwoord = _verstuur("/rest/v1/deals", rij, token=token,
                             extra_kop={"Prefer": "return=representation"})
    except DugoutFout as fout:
        if is_dubbel(fout):
            return "dubbel", None
        raise
    rijen = antwoord or []
    return "nieuw", (rijen[0].get("id") if rijen else None)


if __name__ == "__main__":
    # python dugout.py --test  -> controleert de verbinding en de inlog
    import sys
    if "--test" in sys.argv:
        try:
            wie, aantal = test_verbinding()
        except DugoutFout as fout:
            print("MISLUKT:", fout.args[0] if fout.args else fout)
            sys.exit(1)
        print("OK — ingelogd als %s, de Dugout antwoordt." % wie)
    else:
        print(__doc__)
