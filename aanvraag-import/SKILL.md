---
name: aanvragen-inladen
description: Laadt opgeslagen sprekersaanvragen (.eml) in als kaart in de Commerciële Dugout, en regelt bij het eerste gebruik zelf de installatie. Gebruik deze skill wanneer iemand zegt "/aanvragen-inladen", "laad de nieuwe aanvragen in", "verwerk de aanvragen", "zet de aanvragen in de dugout", of vraagt of er nog aanvragen klaarstaan. Gebruik hem NIET voor het schrijven van sprekersvoorstellen — dat is de skill sportspreker-voorstel.
---

# Aanvragen inladen in de Commerciële Dugout

Leest opgeslagen aanvraagmails uit een map en maakt er kaarten van in de
sprekerspipeline van de Dugout.

Praat Nederlands en houd het kort. De gebruiker is verkoper, geen techneut:
vertel wat er gebeurt, niet hoe het werkt.

---

## Eerst: is dit al ingesteld?

Kijk of `~/.aanvragen-inladen.json` bestaat.

- **Bestaat het** → lees de paden eruit en ga verder bij **Aanvragen inladen**.
- **Bestaat het niet** → dit is de eerste keer. Doe eerst **De eerste keer**.

```json
{ "programma": "...", "aanvragen": "..." }
```

`programma` is de map met `lees_aanvragen.py`.
`aanvragen` is de map met de submappen `SportsSpeakers` en `SportSpreker`.

---

# De eerste keer — installeren

Zeg dat je het even klaarzet, dat het ongeveer vijf minuten duurt en dat je een
paar dingen gaat vragen. Werk de stappen op volgorde af en wacht op antwoord;
verzin niets zelf.

## 1. Staat Python erop?

```
python --version
```

Versienummer 3.9 of hoger → doorgaan.

Foutmelding → **stop** en zeg:

> Op deze laptop staat Python nog niet, en dat heeft het programma nodig.
> Vraag even aan Tigo hoe je dat installeert — dan pikken we het hier weer op.

Installeer Python niet zelf.

## 2. Heeft deze persoon al toegang tot de Dugout?

Vraag: **kun je zelf inloggen op de Commerciële Dugout in je browser?**

- **Ja** → door naar stap 3.
- **Nee of weet niet** → stop en zeg dat Tigo eerst een account voor ze moet
  aanmaken. Zonder Dugout-account kan het programma niets wegschrijven; er valt
  hier niets te installeren wat dat oplost.

Dit is geen aparte inlog: het programma gebruikt hetzelfde account waarmee ze
de Dugout in hun browser openen.

## 3. Waar komen de aanvragen te staan?

Stel deze twee vragen, één voor één:

**a. In welke map wil je binnengekomen aanvragen opslaan?**
Stel `Documenten\Aanvragen sprekers` voor; neem dat over als ze geen voorkeur
hebben.

**b. Werk je voor SportsSpeakers, SportSpreker, of allebei?**
Bij twijfel maak je beide mappen aan — een lege map schaadt niet.

Maak de map aan met daarin per label een submap. De namen moeten **exact** zo
zijn, want daaruit leest het programma het label:

```
<gekozen map>/
    SportsSpeakers/
    SportSpreker/
```

Bestaat er al iets, laat dat staan en meld het.

## 4. Het programma ophalen

Maak `Documenten\Dugout aanvragen-programma` en haal daar deze vier bestanden
op, elk onder hun eigen naam:

```
https://raw.githubusercontent.com/TigoToonen/dugout-prototype/main/aanvraag-import/lees_aanvragen.py
https://raw.githubusercontent.com/TigoToonen/dugout-prototype/main/aanvraag-import/dugout.py
https://raw.githubusercontent.com/TigoToonen/dugout-prototype/main/aanvraag-import/SKILL.md
https://raw.githubusercontent.com/TigoToonen/dugout-prototype/main/sprekers.js
```

Lukt downloaden niet → **stop** en meld dat. Verzin de code niet zelf en typ
hem niet over.

`sprekers.js` bevat de sprekerslijsten. Zonder dat bestand werkt het programma
wel, maar worden namen niet gecontroleerd.

## 5. Inloggegevens klaarzetten

Vraag naar het **e-mailadres** waarmee ze op de Dugout inloggen. Maak dan
`~/.dugout-import.json`:

```json
{
  "email": "<hun e-mailadres>",
  "wachtwoord": ""
}
```

Zeg daarna:

> Open `C:\Users\<naam>\.dugout-import.json`, zet je Dugout-wachtwoord tussen
> de lege aanhalingstekens en sla op. Zeg het als je klaar bent.

**Vraag nooit naar het wachtwoord, laat het niet in de chat plakken en zet het
nooit zelf in het bestand.** Jij hoeft het niet te weten, en wat in een chat
staat is minder goed beschermd dan een bestand op de eigen schijf.

Bestaat het bestand al met een ingevuld wachtwoord → met rust laten.

Leg kort uit dat het daar staat omdat die map niet meesynchroniseert met
OneDrive, dus het wachtwoord blijft op deze laptop.

## 6. De skill installeren

Zet het opgehaalde `SKILL.md` neer als:

```
~/.claude/skills/aanvragen-inladen/SKILL.md
```

De mapnaam moet exact `aanvragen-inladen` zijn — die bepaalt dat
`/aanvragen-inladen` werkt.

Schrijf daarna `~/.aanvragen-inladen.json`:

```json
{
  "programma": "<map uit stap 4>",
  "aanvragen": "<map uit stap 3a>"
}
```

Let op: in JSON moet elke backslash in een Windows-pad verdubbeld worden.
Controleer na het schrijven of het bestand geldig JSON is.

## 7. Controleren

Twee controles. Doe ze allebei.

**a. Werkt het programma?**

```
python "<programma>/lees_aanvragen.py" "<aanvragen>"
```

Goed is: hij noemt de twee sprekerslijsten (117 en 156 namen) en meldt dat er
geen bestanden staan.

**b. Werkt het inloggen?**

```
python "<programma>/dugout.py" --test
```

Goed is: `OK — ingelogd als …, de Dugout antwoordt.`

Krijg je `MISLUKT`, dan klopt het e-mailadres of het wachtwoord niet. Vraag ze
het bestand na te kijken — vraag **niet** wat erin staat.

Deze controle nu doen is belangrijk: anders komen ze er pas achter bij hun
eerste echte aanvraag, en dan is het vervelend.

## 8. Uitleggen hoe het werkt

Gebruik de tekst onder **Uitleg voor de gebruiker** onderaan dit bestand.
Vraag daarna of er nog iets onduidelijk is.

---

# Aanvragen inladen — elke keer

## 1. Lezen, nooit meteen wegschrijven

```
python "<programma>/lees_aanvragen.py" "<aanvragen>"
```

Zonder `--echt` verandert er niets. Laat per aanvraag zien wat er gevonden is:
klant, contactpersoon, spreker, datum, locatie.

Staan er geen bestanden → meld dat gewoon en stop. Dat is geen fout.

## 2. De vrije tekst uitlezen

Is er `claude-taak.json` weggeschreven, lees die dan. Per aanvraag staat er
welke velden open zijn en de tekst van de klant. Haal daaruit:

- **locatie** — waar het evenement plaatsvindt
- **aantal** — aantal personen, als heel getal
- **ev_datum** — alleen als het formulierveld leeg was én de klant een
  concrete datum noemt

Regels:

- **Gok nooit.** Staat het er niet, laat het veld dan weg. Een leeg veld is
  beter dan een verkeerd veld; de volledige klanttekst staat toch op de kaart.
- Een periode is geen datum. "De week van 26 oktober" vul je niet in.
- Twijfel over het jaartal → laat de datum leeg.

Schrijf naar `aanvullingen.json` in de programmamap:

```json
[
  { "vingerafdruk": "…", "locatie": "WTC Utrecht", "aantal": 100 }
]
```

Draai opnieuw met `--aanvullingen aanvullingen.json` en toon het resultaat.

## 3. Akkoord vragen

Vraag of de gegevens kloppen voordat je iets wegschrijft. Altijd — ook als
alles er goed uitziet.

## 4. Wegschrijven

```
python "<programma>/lees_aanvragen.py" "<aanvragen>" --aanvullingen aanvullingen.json --echt --max <aantal>
```

Zet `--max` op het aantal aanvragen dat je zojuist hebt getoond, nooit hoger.
Dat is de rem: die voorkomt dat een fout in één keer een reeks kaarten oplevert.

Is dit de eerste keer dat deze gebruiker inlaadt, doe dan eerst `--max 1`, laat
die ene kaart controleren, en pas daarna de rest.

## 5. Afronden

Vertel wat er is aangemaakt en wat er nu moet gebeuren:

> De kaarten staan in de Dugout onder **Aanvraag ontvangen**, met de rode
> markering **Nog goed te keuren**. Open ze, vul aan wat ontbreekt, kies jezelf
> als contactpersoon en klik op *Gegevens kloppen — goedkeuren*.

---

# Wat je nooit doet

- **Nooit naar het wachtwoord vragen** en het nooit in de chat laten plakken.
  Het programma leest het zelf uit `~/.dugout-import.json`. Werkt inloggen niet,
  zeg dan dat ze dat bestand moeten nakijken.
- **Nooit bestanden weggooien.** Het programma verplaatst ze zelf naar
  `verwerkt` of `mislukt`.
- **Nooit `--echt` zonder `--max`.**
- **Nooit een veld invullen dat niet in de aanvraag staat.**
- **Nooit Python installeren** of code verzinnen als downloaden mislukt.

# Als er iets misgaat

| Melding | Wat het betekent |
|---|---|
| Geen inloggegevens gevonden | `~/.dugout-import.json` ontbreekt of is leeg |
| Inloggen mislukt | Verkeerd e-mailadres of wachtwoord in dat bestand |
| Geen verbinding | Geen internet, of Supabase is onbereikbaar |
| stond er al, geen tweede kaart | Goed nieuws — deze aanvraag was al ingeladen |
| Formuliervariant niet herkend | Nieuw soort aanvraagmail; stuur het bestand naar Tigo |

Bestanden in `mislukt` zijn niet verwerkt. Meld dat en gooi ze niet weg.

---

# Uitleg voor de gebruiker

> **Klaar.** Zo werkt het vanaf nu:
>
> **1. Aanvraag opslaan.** Komt er een offerteaanvraag binnen, sla de mail dan
> op als EML-bestand in de map van het juiste label. De map bepaalt welk label
> de kaart krijgt, dus let even op dat je in de goede map opslaat. Meerdere
> tegelijk mag.
>
> **2. Typ `/aanvragen-inladen`.** Ik lees ze uit, laat zien wat ik gevonden heb
> en vraag of het klopt voordat er iets in de Dugout komt. Gewoon vragen — "laad
> de nieuwe aanvragen in" — werkt ook.
>
> Er zit geen klok op: het gebeurt alleen als jij het vraagt. Doe het dus meteen
> nadat je een mail hebt opgeslagen, dan raak je het niet kwijt.
>
> **3. Kaart nakijken en goedkeuren.** De nieuwe kaarten staan in de Dugout
> onder *Aanvraag ontvangen*, met een rode markering **Nog goed te keuren**.
> Open zo'n kaart, vul aan wat ontbreekt, kies jezelf als contactpersoon en klik
> op *Gegevens kloppen — goedkeuren*. De markering wordt groen. Zolang hij rood
> is, weet iedereen dat er nog niemand naar gekeken heeft.
>
> **Wat je niet hoeft te doen:** verwerkte mails weggooien. Dat gebeurt vanzelf
> — ze verhuizen naar de submap `verwerkt`. Laat die staan, het zijn je
> originelen.
>
> **Dubbel opslaan kan geen kwaad.** Sla je dezelfde aanvraag twee keer op, of
> doet een collega dat ook, dan komt er geen tweede kaart. Ook niet bij een
> andere bestandsnaam of een doorgestuurde mail.
>
> **Twee dingen blijven soms leeg:** locatie en aantal personen. Die staan
> meestal ergens in de tekst van de klant, maar niet altijd. Er wordt niets
> gegokt; wat ontbreekt staat bovenaan de opmerking op de kaart. De volledige
> tekst van de klant staat er altijd bij.
>
> **Vraagt een klant meerdere sprekers?** De eerste komt in het sprekersveld, de
> rest staat in de opmerking. Eén aanvraag blijft één kaart.
