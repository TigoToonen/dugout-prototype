"""
Leest opgeslagen aanvraagmails (.eml) en haalt er de velden uit voor een
kaart in de sprekerspipeline van de Commerciële Dugout.

DRY RUN: dit script schrijft niets weg. Het leest en toont alleen.

Gebruik:
    python lees_aanvragen.py "<map>"                      lezen en tonen
    python lees_aanvragen.py "<map>" --aanvullingen a.json  met wat Claude vond
    python lees_aanvragen.py "<map>" --echt --max 1         écht wegschrijven

Zonder --echt gebeurt er niets: het script leest en toont alleen. Met --echt
worden er kaarten aangemaakt in de Dugout; --max begrenst hoeveel er in één
keer bij mogen komen, zodat een fout nooit in één klap tien kaarten oplevert.

De map hoort twee submappen te hebben, één per label:
    SportsSpeakers/   -> SportsSpeakers (NL)
    SportSpreker/     -> SportSpreker (BE)

Verwerkte bestanden gaan naar 'verwerkt', mislukte naar 'mislukt', naast de
map waar ze vandaan komen. Er wordt nooit iets weggegooid.

Bewust géén externe pakketten: dit moet op vijf laptops draaien zonder installatie.
"""

import difflib
import email
import email.utils
import hashlib
import html
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone
from email.header import decode_header, make_header
from pathlib import Path

# ------------------------------------------------------------------
#  Vaste gegevens
# ------------------------------------------------------------------

MAP_NAAR_LABEL = {
    "sportsspeakers": "SportsSpeakers (NL)",
    "sportspreker": "SportSpreker (BE)",
}

# Aan welk afzenderadres hoort welk label — puur als controle op de map.
AFZENDER_NAAR_LABEL = {
    "info@sportsspeakers.nl": "SportsSpeakers (NL)",
    "info@sportspreker.be": "SportSpreker (BE)",
}

# De regel waarmee het aanvraagblok begint, in beide formuliervarianten.
ANKER = "Er is een nieuwe offerteaanvraag binnengekomen"

# De twee formuliervarianten. De labels staan in de volgorde waarin ze in de
# mail voorkomen; het script knipt de tekst op die labels in stukken.
VARIANTEN = {
    "offerteaanvraag": [
        "Welke spreker(s)?", "Naam", "Bedrijfsnaam", "E-mailadres",
        "Telefoonnummer", "Datum", "Tijdstip", "Thema en doel",
        "Opmerking", "GCLID",
    ],
    "aanvraag-voor": [
        "Welke spreker(s)?", "Naam", "Bedrijfsnaam", "E-mailadres",
        "Telefoonnummer", "Voorkeursdatum", "Bericht", "GCLID",
    ],
}

# Van formulierlabel naar kolom in de tabel deals.
LABEL_NAAR_VELD = {
    "Welke spreker(s)?": "spreker",
    "Naam": "contact",
    "Bedrijfsnaam": "klant",
    "E-mailadres": "email",
    "Telefoonnummer": "tel",
    "Datum": "ev_datum",
    "Voorkeursdatum": "ev_datum",
    "Tijdstip": "ev_tijd",
    "Thema en doel": "thema",
    "Opmerking": "opm_bron",
    "Bericht": "opm_bron",
}

MAANDEN = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 11,
    "december": 12,
}

OPVOLG_DAGEN = 7          # datum volgende actie = binnenkomst + 7
FASE = "Aanvraag ontvangen"

def _zoek_sprekers_js():
    """
    De sprekerslijsten van de Dugout — hetzelfde bestand als de app gebruikt,
    zodat een naam die hier matcht ook in de app in de keuzelijst staat.

    Waar dat bestand staat verschilt per installatie: naast dit script (zoals
    bij een verse installatie), een map hoger (in de repo), of in de
    projectmap van Tigo. We pakken de eerste die bestaat.
    """
    hier = Path(__file__).resolve()
    kandidaten = [
        hier.parent / "sprekers.js",
        hier.parents[1] / "sprekers.js",
        hier.parents[3] / "Commercie" / "Projecten" / "dugout" / "sprekers.js",
    ]
    for pad in kandidaten:
        try:
            if pad.exists():
                return pad
        except IndexError:
            continue
    return kandidaten[0]


SPREKERS_JS = _zoek_sprekers_js()


# ------------------------------------------------------------------
#  Sprekersnamen matchen op de lijst
#
#  Bewust geen model: dit is vergelijken met een bekende lijst en heeft
#  één goed antwoord. Wel nodig omdat schrijfwijzen verschillen — in de
#  lijst staat zowel "Richard van Hooijdonk" (NL) als "Richard Van
#  Hooijdonk" (BE), met verschillende tarieven.
# ------------------------------------------------------------------

def plat(tekst):
    """Kleine letters, zonder accenten, zonder dubbele spaties."""
    tekst = unicodedata.normalize("NFD", str(tekst or ""))
    tekst = "".join(c for c in tekst if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", tekst).strip().lower()


def laad_sprekers(pad=SPREKERS_JS):
    """
    Leest sprekers.js. Dat is JavaScript, geen JSON — de sleutels staan
    zonder aanhalingstekens — dus we vissen de regels er met een patroon uit.
    """
    lijsten = {}
    if not Path(pad).exists():
        return lijsten
    tekst = Path(pad).read_text(encoding="utf-8")
    huidig = None
    for regel in tekst.splitlines():
        kop = re.match(r'\s*"([^"]+)"\s*:\s*\[', regel)
        if kop:
            huidig = kop.group(1)
            lijsten[huidig] = []
            continue
        if huidig is None:
            continue
        m = re.search(r'\{n:"([^"]+)"(.*)\}', regel)
        if m:
            extra = m.group(2)
            def veld(sleutel):
                v = re.search(sleutel + r':"([^"]*)"', extra)
                return v.group(1) if v else ""
            lijsten[huidig].append({
                "naam": m.group(1), "sport": veld("s"),
                "budget": veld("b"), "soort": veld("c"),
            })
    return lijsten


def match_spreker(naam, label, lijsten):
    """
    Zoekt de naam in de lijst van dit label.
      exact  — zelfde naam, los van hoofdletters en accenten
      bijna  — zeer sterk gelijkend, bijv. een typefout of ontbrekend streepje
      geen   — niet gevonden; we nemen de naam over zoals hij in de mail staat
    """
    lijst = lijsten.get(label) or []
    if not lijst:
        return {"naam": naam, "match": "geen lijst"}

    doel = plat(naam)
    for s in lijst:
        if plat(s["naam"]) == doel:
            return {"naam": s["naam"], "match": "exact",
                    "sport": s["sport"], "budget": s["budget"], "soort": s["soort"]}

    namen = [s["naam"] for s in lijst]
    dichtbij = difflib.get_close_matches(doel, [plat(n) for n in namen], n=1, cutoff=0.90)
    if dichtbij:
        for s in lijst:
            if plat(s["naam"]) == dichtbij[0]:
                return {"naam": s["naam"], "match": "bijna", "gevraagd": naam,
                        "sport": s["sport"], "budget": s["budget"], "soort": s["soort"]}

    return {"naam": naam, "match": "geen"}


# ------------------------------------------------------------------
#  Mail openmaken
# ------------------------------------------------------------------

def kop(msg, naam):
    """Leest een header en maakt er leesbare tekst van."""
    ruw = msg.get(naam)
    if not ruw:
        return ""
    try:
        return " ".join(str(make_header(decode_header(ruw))).split())
    except Exception:
        return " ".join(str(ruw).split())


def html_naar_tekst(rauw):
    rauw = re.sub(r"(?is)<(script|style).*?</\1>", "", rauw)
    rauw = re.sub(r"(?i)<br\s*/?>", "\n", rauw)
    rauw = re.sub(r"(?i)</(td|th|p|div|tr|li|h[1-6])>", "\n", rauw)
    return html.unescape(re.sub(r"(?s)<[^>]+>", "", rauw))


def bodytekst(msg):
    """De tekst van de mail. Platte tekst heeft de voorkeur boven HTML."""
    for zoek_html in (False, True):
        for deel in msg.walk():
            soort = deel.get_content_type()
            if soort == ("text/html" if zoek_html else "text/plain"):
                try:
                    rauw = deel.get_payload(decode=True).decode(
                        deel.get_content_charset() or "utf-8", "replace")
                except Exception:
                    continue
                return html_naar_tekst(rauw) if zoek_html else rauw
    return ""


def schoon(tekst):
    """Haalt de ruis weg die Outlook in de tekst zet."""
    # Eerst de regeleinden gelijktrekken. Mail gebruikt CRLF; zonder dit
    # blijft er een \r aan het eind van elke regel staan en herkent het
    # script de formulierlabels niet als losse regel.
    tekst = tekst.replace("\r\n", "\n").replace("\r", "\n")
    tekst = re.sub(r"<mailto:[^>]*>", "", tekst)
    tekst = re.sub(r"\[cid:[^\]]*\]", "", tekst)
    tekst = re.sub(r"<https?://[^>]*>", "", tekst)
    tekst = re.sub(r"[ \t]+\n", "\n", tekst)
    return re.sub(r"\n{3,}", "\n\n", tekst)


# ------------------------------------------------------------------
#  Doorstuurketen: waar kwam de aanvraag écht vandaan, en wanneer?
# ------------------------------------------------------------------

def nl_datum(tekst):
    """'dinsdag 18 augustus 2026 16:43' -> date(2026, 8, 18)"""
    m = re.search(r"(\d{1,2})\s+([a-zA-Zé]+)\s+(\d{4})", tekst)
    if not m:
        return None
    maand = MAANDEN.get(m.group(2).lower())
    if not maand:
        return None
    try:
        return date(int(m.group(3)), maand, int(m.group(1)))
    except ValueError:
        return None


def herkomst(msg, tekst):
    """
    Afzender en datum van de OORSPRONKELIJKE aanvraag.

    Outlook zet bij doorsturen de originele kop als 'Van:' / 'Verzonden:'
    in de tekst. De laatste die we tegenkomen is de oudste schakel, en dus
    de echte aanvraag. Staat er geen keten in, dan is het bestand het
    origineel en gebruiken we de mailkop.
    """
    afzenders = re.findall(r"(?im)^\s*Van:\s*(.+)$", tekst)
    datums = re.findall(r"(?im)^\s*Verzonden:\s*(.+)$", tekst)

    doorgestuurd = bool(afzenders or datums)

    if afzenders:
        adres = email.utils.parseaddr(afzenders[-1])[1]
    else:
        adres = email.utils.parseaddr(msg.get("From", ""))[1]

    binnen = nl_datum(datums[-1]) if datums else None
    if binnen is None:
        tup = email.utils.parsedate_tz(msg.get("Date", ""))
        binnen = date(*tup[:3]) if tup else None

    return adres.lower(), binnen, doorgestuurd


# ------------------------------------------------------------------
#  Het aanvraagblok uit elkaar halen
# ------------------------------------------------------------------

def kies_variant(tekst, onderwerp):
    """Welke van de twee formulieren is dit? Bepaald op de aanwezige labels."""
    scores = {}
    for naam, labels in VARIANTEN.items():
        aanwezig = sum(1 for lab in labels
                       if re.search(r"(?m)^\s*%s\s*$" % re.escape(lab), tekst))
        scores[naam] = aanwezig
    beste = max(scores, key=scores.get)
    return (beste, scores[beste]) if scores[beste] >= 4 else (None, scores[beste])


def knip_velden(tekst, labels):
    """
    Knipt de tekst op de formulierlabels. Elk label staat op een eigen regel;
    alles tot het volgende label is de waarde. Lege velden blijven leeg.
    """
    posities = []
    for lab in labels:
        m = re.search(r"(?m)^[ \t]*%s[ \t]*$" % re.escape(lab), tekst)
        if m:
            posities.append((m.start(), m.end(), lab))
    posities.sort()

    uit = {}
    for i, (_, eind, lab) in enumerate(posities):
        volgende = posities[i + 1][0] if i + 1 < len(posities) else len(tekst)
        uit[lab] = tekst[eind:volgende].strip()
    return uit


def lees_datum(waarde):
    """
    De formulieren leveren de datum in drie notaties aan. Alle drie komen
    in echte aanvragen voor:
        28/10/2026    dag/maand/jaar
        20-08-2027    dag-maand-jaar
        2026-09-02    jaar-maand-dag
        28 oktober 2026
    Het jaartal verraadt welke van de eerste drie het is: staat het vooraan,
    dan is het de laatste notatie.
    """
    if not waarde:
        return None

    m = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", waarde)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)),
                        int(m.group(3))).isoformat()
        except ValueError:
            return None

    m = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", waarde)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)),
                        int(m.group(1))).isoformat()
        except ValueError:
            return None

    d = nl_datum(waarde)
    return d.isoformat() if d else None


def lees_tijd(waarde):
    """19u00-20u00 -> 19:00 - 20:00 · 15:00 blijft 15:00."""
    if not waarde:
        return ""
    tijden = re.findall(r"\b(\d{1,2})[u:.](\d{2})\b", waarde)
    if not tijden:
        return waarde.strip()
    net = ["%02d:%s" % (int(u), m) for u, m in tijden]
    return " - ".join(net[:2]) if len(net) >= 2 else net[0]


def lees_sprekers(waarde):
    if not waarde:
        return []
    return [n.strip() for n in re.split(r"[,;]|\ben\b", waarde) if n.strip()]


def aanvullen(resultaten, pad):
    """
    Voegt toe wat Claude uit de vrije tekst heeft gehaald.

    Het bestand is een lijst van {vingerafdruk, locatie, aantal, ev_datum}.
    Alleen velden die er echt in staan worden overgenomen; wat Claude niet
    kon vinden blijft leeg, en dat is beter dan een gok.
    """
    if not Path(pad).exists():
        return "bestand niet gevonden: %s" % pad
    lijst = json.loads(Path(pad).read_text(encoding="utf-8"))
    per_afdruk = {a.get("vingerafdruk"): a for a in lijst}

    gevuld = 0
    for r in resultaten:
        k = r.get("kaart")
        if not k:
            continue
        a = per_afdruk.get(k.get("bron_vingerafdruk"))
        if not a:
            continue
        for veld in ("locatie", "ev_datum"):
            if a.get(veld):
                k[veld] = a[veld]
                gevuld += 1
        if a.get("aantal") not in (None, ""):
            try:
                k["aantal"] = int(a["aantal"])
                gevuld += 1
            except (TypeError, ValueError):
                pass

        # de waarschuwingsregel opnieuw opbouwen: wat nu wél gevonden is,
        # hoort er niet meer bij te staan
        open_nu = []
        if not k.get("ev_datum"):
            open_nu.append("datum evenement")
        if not k.get("locatie"):
            open_nu.append("locatie")
        if k.get("aantal") in (None, ""):
            open_nu.append("aantal personen")
        r["handmatig_aanvullen"] = open_nu
        k["opm"] = bouw_opmerking(r.get("vrije_tekst", ""),
                                  r.get("overige_sprekers", []), open_nu)
    return "%d velden aangevuld" % gevuld


def bouw_opmerking(vrije_tekst, overige_sprekers, ontbreekt):
    """
    De opmerking op de kaart. Bovenaan wat iemand moet weten, daaronder de
    tekst van de klant, ongewijzigd — zodat er nooit iets verloren gaat.
    """
    kop_regels = []
    if overige_sprekers:
        kop_regels.append("Ook gevraagd: " + ", ".join(overige_sprekers))
    if ontbreekt:
        kop_regels.append("⚠ Niet automatisch gevonden: " + ", ".join(ontbreekt))

    delen = []
    if kop_regels:
        delen.append("\n".join(kop_regels))
    if vrije_tekst.strip():
        delen.append(vrije_tekst.strip())
    return "\n\n---\n\n".join(delen)


def vingerafdruk(label, mail, sprekers, ev_datum, vrije_tekst):
    """
    Kenmerk van de aanvraag zelf — gelijk voor het origineel en elke
    doorgestuurde kopie. Hierop weigert de database een tweede kaart.
    """
    kern = "|".join([
        label,
        (mail or "").lower().strip(),
        ",".join(sorted(s.lower() for s in sprekers)),
        ev_datum or "",
        re.sub(r"\s+", " ", (vrije_tekst or "")).strip().lower()[:400],
    ])
    return hashlib.sha256(kern.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------
#  Eén bestand verwerken
# ------------------------------------------------------------------

def verwerk(pad: Path, label: str, lijsten=None):
    lijsten = lijsten if lijsten is not None else {}
    with open(pad, "r", encoding="utf-8", errors="replace") as f:
        msg = email.message_from_file(f)

    onderwerp = kop(msg, "Subject")
    tekst = schoon(bodytekst(msg))
    afzender, binnen, doorgestuurd = herkomst(msg, tekst)

    resultaat = {
        "bestand": pad.name,
        "_pad": str(pad),
        "label": label,
        "onderwerp": onderwerp,
        "afzender_origineel": afzender,
        "doorgestuurd": doorgestuurd,
        "binnenkomst": binnen.isoformat() if binnen else None,
        "waarschuwingen": [],
        "handmatig_aanvullen": [],
    }

    if ANKER not in tekst:
        resultaat["fout"] = "Geen aanvraagblok gevonden — is dit wel een aanvraagmail?"
        return resultaat

    variant, score = kies_variant(tekst, onderwerp)
    resultaat["variant"] = variant
    if not variant:
        resultaat["fout"] = "Formuliervariant niet herkend (%d labels gevonden)" % score
        return resultaat

    start = tekst.index(ANKER)
    velden = knip_velden(tekst[start:], VARIANTEN[variant])

    kaart = {
        "pipeline": "spsp",
        "label": label,
        "fase": FASE,
        "owner": "",
        "status": "actief",
        "waarde": 0,
        "bron": "mail-import",
        "bron_bestand": pad.name,
        "bron_msgid": kop(msg, "Message-ID"),
    }

    vrije_tekst = ""
    for lab, waarde in velden.items():
        veld = LABEL_NAAR_VELD.get(lab)
        if not veld:
            continue                      # GCLID slaan we bewust niet op
        if veld == "ev_datum":
            kaart["ev_datum"] = lees_datum(waarde)
            if waarde and not kaart["ev_datum"]:
                resultaat["waarschuwingen"].append(
                    "Datum '%s' niet begrepen" % waarde)
            elif not waarde:
                resultaat["handmatig_aanvullen"].append("datum evenement")
        elif veld == "ev_tijd":
            kaart["ev_tijd"] = lees_tijd(waarde)
        elif veld == "opm_bron":
            vrije_tekst = waarde
        else:
            kaart[veld] = waarde.strip()

    # Op de kaart komt alléén de eerst genoemde spreker. Vraagt de klant er
    # meer, dan gaan de overige namen naar de opmerking — weggooien zou
    # betekenen dat je op de kaart niet meer ziet wat er gevraagd is.
    ruw = lees_sprekers(kaart.get("spreker", ""))
    treffers = [match_spreker(n, label, lijsten) for n in ruw]
    sprekers = [t["naam"] for t in treffers]
    kaart["spreker"] = sprekers[0] if sprekers else ""
    resultaat["sprekers"] = sprekers
    resultaat["overige_sprekers"] = sprekers[1:]
    resultaat["sprekermatch"] = treffers

    for t in treffers:
        if t["match"] == "bijna":
            resultaat["waarschuwingen"].append(
                "Spreker '%s' gelezen als '%s'" % (t.get("gevraagd"), t["naam"]))
        elif t["match"] == "geen":
            resultaat["waarschuwingen"].append(
                "Spreker '%s' staat niet in de lijst van %s" % (t["naam"], label))

    if binnen:
        kaart["laatste"] = binnen.isoformat()
        kaart["bijgewerkt"] = binnen.isoformat()
        kaart["volgende_actie"] = (binnen + timedelta(days=OPVOLG_DAGEN)).isoformat()
    else:
        resultaat["waarschuwingen"].append("Binnenkomstdatum niet gevonden")

    # Locatie en aantal personen staan alleen in de vrije tekst, en soms staat
    # daar ook een datum terwijl het formulierveld leeg bleef. Dat is lezen en
    # interpreteren — dat doet het script niet zelf. Wat hier open blijft, komt
    # in "vraag_claude" te staan; zie aanvullen().
    kaart["locatie"] = None
    kaart["aantal"] = None
    resultaat["handmatig_aanvullen"] += ["locatie", "aantal personen"]

    vraag = ["locatie", "aantal"]
    if not kaart.get("ev_datum"):
        vraag.append("ev_datum")
    resultaat["vraag_claude"] = {
        "vingerafdruk": None,          # wordt hieronder gevuld
        "velden": vraag,
        "tekst": vrije_tekst,
    }

    kaart["opm"] = bouw_opmerking(
        vrije_tekst, resultaat["overige_sprekers"],
        resultaat["handmatig_aanvullen"])

    # De vingerafdruk gebruikt álle gevraagde sprekers, niet alleen de eerste.
    # Hij moet de aanvraag herkennen, niet de kaart.
    kaart["bron_vingerafdruk"] = vingerafdruk(
        label, kaart.get("email"), sprekers, kaart.get("ev_datum"), vrije_tekst)
    resultaat["vraag_claude"]["vingerafdruk"] = kaart["bron_vingerafdruk"]

    verwacht = AFZENDER_NAAR_LABEL.get(afzender)
    if verwacht and verwacht != label:
        resultaat["waarschuwingen"].append(
            "Mail komt van %s (%s) maar ligt in de map voor %s"
            % (afzender, verwacht, label))

    if not kaart.get("email"):
        resultaat["waarschuwingen"].append("Geen e-mailadres gevonden")
    if not sprekers:
        resultaat["waarschuwingen"].append("Geen spreker gevonden")

    resultaat["kaart"] = kaart
    resultaat["vrije_tekst"] = vrije_tekst
    return resultaat


# ------------------------------------------------------------------
#  Tonen
# ------------------------------------------------------------------

def toon(r):
    print("=" * 72)
    print("BESTAND   ", r["bestand"])
    print("LABEL     ", r["label"], "(uit de map)")
    print("HERKOMST  ", r["afzender_origineel"],
          "· doorgestuurd" if r["doorgestuurd"] else "· origineel",
          "· binnengekomen", r["binnenkomst"] or "ONBEKEND")

    if r.get("fout"):
        print("!! ", r["fout"])
        return

    print("VARIANT   ", r["variant"])
    k = r["kaart"]
    print("-" * 72)
    for veld, titel in [
        ("klant", "Klant"), ("contact", "Contactpersoon"), ("email", "E-mail"),
        ("tel", "Telefoon"), ("spreker", "Gevraagde spreker(s)"),
        ("ev_datum", "Datum evenement"), ("ev_tijd", "Tijdstip"),
        ("thema", "Thema / opdracht"), ("locatie", "Locatie"),
        ("aantal", "Aantal personen"), ("volgende_actie", "Volgende actie"),
        ("fase", "Fase"), ("owner", "Eigenaar"),
    ]:
        waarde = k.get(veld)
        print("  %-22s %s" % (titel, "—" if waarde in (None, "") else waarde))

    if r.get("overige_sprekers"):
        print("  %-22s %s" % ("Ook gevraagd",
                              ", ".join(r["overige_sprekers"])))
    print("  %-22s %s…" % ("Vingerafdruk", k["bron_vingerafdruk"][:16]))

    if r["waarschuwingen"]:
        print("-" * 72)
        for w in r["waarschuwingen"]:
            print("  ! ", w)

    opm = (k.get("opm") or "").strip()
    if opm:
        print("-" * 72)
        print("  Opmerking zoals hij op de kaart komt:")
        regels = opm.splitlines()
        for regel in regels[:8]:
            print("    ", regel[:88])
        if len(regels) > 8:
            print("      … (%d regels in totaal)" % len(regels))


def wegschrijven(resultaten, max_aantal):
    """
    Maakt de kaarten echt aan. Per aanvraag: kaart aanmaken, bestand naar
    'verwerkt', regel in het logboek. Gaat er iets mis, dan verhuist het
    bestand naar 'mislukt' en gaan we door met de volgende — één rare
    aanvraag mag de rest niet tegenhouden.
    """
    import dugout

    token, wie = dugout.inloggen()
    print("Ingelogd als", wie)

    nieuw = dubbel = mislukt = 0
    logboek = Path(__file__).with_name("import-log.jsonl")

    for r in resultaten:
        if r.get("fout") or not r.get("kaart"):
            continue
        if nieuw >= max_aantal:
            print("  · rem bereikt (--max %d) — rest blijft staan" % max_aantal)
            break

        kaart = r["kaart"]
        kaart["bron_door"] = wie
        kaart["bron_op"] = datetime.now(timezone.utc).isoformat()
        bestand = Path(r["_pad"])

        try:
            status, kaart_id = dugout.maak_kaart(kaart, token)
        except dugout.DugoutFout as fout:
            mislukt += 1
            print("  ✗ %s — %s" % (bestand.name, fout.args[0]))
            verplaats(bestand, "mislukt")
            noteer(logboek, bestand.name, "mislukt", str(fout.args[0]))
            continue

        if status == "dubbel":
            dubbel += 1
            print("  = %s — stond er al, geen tweede kaart" % bestand.name)
            verplaats(bestand, "verwerkt")
            noteer(logboek, bestand.name, "dubbel", kaart["bron_vingerafdruk"])
        else:
            nieuw += 1
            print("  ✓ %s — kaart %s aangemaakt" % (bestand.name, kaart_id))
            verplaats(bestand, "verwerkt")
            noteer(logboek, bestand.name, "nieuw", kaart_id)

    print("\n%d nieuw · %d al aanwezig · %d mislukt" % (nieuw, dubbel, mislukt))
    if nieuw:
        print("De nieuwe kaarten staan in 'Aanvraag ontvangen' met de markering")
        print("'Nog goed te keuren'. Ze tellen pas mee als iemand ze nakijkt.")


def verplaats(bestand: Path, submap: str):
    doel = bestand.parent / submap
    doel.mkdir(exist_ok=True)
    nieuw = doel / bestand.name
    n = 1
    while nieuw.exists():                      # nooit iets overschrijven
        nieuw = doel / ("%s (%d)%s" % (bestand.stem, n, bestand.suffix))
        n += 1
    bestand.replace(nieuw)


def noteer(logboek: Path, bestand, status, details):
    regel = {"wanneer": datetime.now(timezone.utc).isoformat(),
             "bestand": bestand, "status": status, "details": str(details)}
    with open(logboek, "a", encoding="utf-8") as f:
        f.write(json.dumps(regel, ensure_ascii=False) + "\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    basis = Path(sys.argv[1])
    if not basis.is_dir():
        print("Map niet gevonden:", basis)
        sys.exit(1)

    aanvul_pad = None
    if "--aanvullingen" in sys.argv:
        i = sys.argv.index("--aanvullingen")
        if i + 1 < len(sys.argv):
            aanvul_pad = sys.argv[i + 1]

    echt = "--echt" in sys.argv
    max_aantal = 1                      # zonder --max blijft het bij één kaart
    if "--max" in sys.argv:
        i = sys.argv.index("--max")
        if i + 1 < len(sys.argv):
            try:
                max_aantal = max(0, int(sys.argv[i + 1]))
            except ValueError:
                print("--max verwacht een getal")
                sys.exit(1)

    lijsten = laad_sprekers()
    if lijsten:
        print("Sprekerslijsten: " + " · ".join(
            "%s (%d)" % (k, len(v)) for k, v in lijsten.items()))
    else:
        print("! Sprekerslijst niet gevonden — namen worden niet gecontroleerd.")
        print("  Verwacht op:", SPREKERS_JS)

    resultaten = []
    for submap, label in MAP_NAAR_LABEL.items():
        map_pad = next((p for p in basis.iterdir()
                        if p.is_dir() and p.name.lower() == submap), None)
        if not map_pad:
            continue
        for eml in sorted(map_pad.glob("*.eml")):
            resultaten.append(verwerk(eml, label, lijsten))

    if not resultaten:
        print("Geen .eml-bestanden gevonden in", basis)
        return

    if aanvul_pad:
        print("Aanvullingen:", aanvullen(resultaten, aanvul_pad))

    for r in resultaten:
        toon(r)

    print("=" * 72)
    goed = [r for r in resultaten if not r.get("fout")]
    print("%d bestanden gelezen, %d gelukt, %d mislukt."
          % (len(resultaten), len(goed), len(resultaten) - len(goed)))
    afdrukken = {r["kaart"]["bron_vingerafdruk"] for r in goed}
    print("%d unieke aanvragen (dubbele worden door de database geweigerd)."
          % len(afdrukken))
    hier = Path(__file__).parent
    (hier / "dry-run-resultaat.json").write_text(
        json.dumps(resultaten, indent=2, ensure_ascii=False), encoding="utf-8")

    # Wat Claude nog moet uitlezen. Is alles al ingevuld, dan blijft dit leeg.
    taken = [r["vraag_claude"] for r in goed
             if r.get("vraag_claude") and r.get("handmatig_aanvullen")]
    if taken:
        (hier / "claude-taak.json").write_text(
            json.dumps(taken, indent=2, ensure_ascii=False), encoding="utf-8")

    if not echt:
        print("\nDRY RUN — er is niets weggeschreven.")
        print("Volledige uitkomst: dry-run-resultaat.json")
        if taken:
            print("Nog uit te lezen door Claude: claude-taak.json (%d aanvragen)"
                  % len(taken))
        print("\nEcht wegschrijven? Zet er --echt achter (en eventueel --max N).")
        return

    print("\n" + "=" * 72)
    print("WEGSCHRIJVEN NAAR DE DUGOUT — maximaal %d nieuwe kaart(en)" % max_aantal)
    print("=" * 72)
    try:
        wegschrijven(goed, max_aantal)
    except Exception as fout:                       # inloggen mislukt e.d.
        print("\nGestopt:", fout)
        print("Er is niets weggeschreven.")
        sys.exit(1)


if __name__ == "__main__":
    main()
