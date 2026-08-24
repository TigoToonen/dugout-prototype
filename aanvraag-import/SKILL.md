---
name: aanvragen-inladen
description: Laadt opgeslagen sprekersaanvragen (.eml) in als kaart in de Commerciële Dugout. Gebruik deze skill wanneer iemand zegt "/aanvragen-inladen", "laad de nieuwe aanvragen in", "verwerk de aanvragen", "zet de aanvragen in de dugout", of vraagt of er nog aanvragen klaarstaan. Gebruik hem NIET voor het schrijven van sprekersvoorstellen — dat is de skill sportspreker-voorstel.
---

# Aanvragen inladen in de Commerciële Dugout

Leest opgeslagen aanvraagmails uit een map en maakt er kaarten van in de
sprekerspipeline van de Dugout.

## Waar alles staat

De installatie heeft een bestand `~/.aanvragen-inladen.json` achtergelaten met
de paden. Lees dat eerst:

```
{ "programma": "...", "aanvragen": "..." }
```

- `programma` — map met `lees_aanvragen.py`
- `aanvragen` — map met de submappen `SportsSpeakers` en `SportSpreker`

Ontbreekt dat bestand, zeg dan dat de installatie nog niet is uitgevoerd en
vraag om het installatiedocument.

## Werkwijze

### 1. Lezen — nooit meteen wegschrijven

```
python "<programma>/lees_aanvragen.py" "<aanvragen>"
```

Zonder `--echt` verandert er niets. Toon de gebruiker per aanvraag wat er
gevonden is: klant, contactpersoon, spreker, datum, locatie.

Staan er geen bestanden, meld dat dan gewoon en stop. Dat is geen fout.

### 2. De vrije tekst uitlezen

Is er `claude-taak.json` weggeschreven, lees die dan. Per aanvraag staat er
welke velden nog open zijn en de tekst van de klant. Haal daaruit:

- **locatie** — waar het evenement plaatsvindt
- **aantal** — aantal personen, als heel getal
- **ev_datum** — alleen als het formulierveld leeg was én de klant een
  concrete datum noemt

Regels:

- **Gok nooit.** Staat het er niet, laat het veld dan weg. Een leeg veld is
  beter dan een verkeerd veld; de volledige klanttekst staat toch op de kaart.
- Een periode is geen datum. "De week van 26 oktober" vul je niet in.
- Bij twijfel over het jaartal: laat de datum leeg.

Schrijf je bevindingen naar `aanvullingen.json` in de programmamap:

```json
[
  { "vingerafdruk": "…", "locatie": "WTC Utrecht", "aantal": 100 }
]
```

Draai daarna opnieuw met `--aanvullingen aanvullingen.json` en laat het
resultaat zien.

### 3. Akkoord vragen

Vraag de gebruiker of de gegevens kloppen voordat je iets wegschrijft. Doe dit
altijd, ook als alles er goed uitziet.

### 4. Wegschrijven

```
python "<programma>/lees_aanvragen.py" "<aanvragen>" --aanvullingen aanvullingen.json --echt --max <aantal>
```

Zet `--max` op het aantal aanvragen dat je zojuist hebt getoond, nooit hoger.
Dat is de rem: hij voorkomt dat een fout in één keer een reeks kaarten oplevert.

Gaat het om de eerste keer dat deze gebruiker inlaadt, doe dan eerst `--max 1`,
laat die ene kaart controleren, en pas daarna de rest.

### 5. Afronden

Vertel wat er is aangemaakt en wat er nu moet gebeuren:

> De kaarten staan in de Dugout onder **Aanvraag ontvangen**, met de rode
> markering **Nog goed te keuren**. Open ze, vul aan wat ontbreekt, kies jezelf
> als contactpersoon en klik op *Gegevens kloppen — goedkeuren*.

## Wat je nooit doet

- **Nooit naar het wachtwoord vragen** en het nooit in de chat laten plakken.
  Het programma leest het zelf uit `~/.dugout-import.json`. Werkt inloggen niet,
  zeg dan dat ze dat bestand moeten nakijken — vraag niet wat erin staat.
- **Nooit bestanden weggooien.** Het programma verplaatst ze zelf naar
  `verwerkt` of `mislukt`.
- **Nooit `--echt` zonder `--max`.**
- **Nooit een veld invullen dat niet in de aanvraag staat.**

## Als er iets misgaat

| Melding | Wat het betekent |
|---|---|
| Geen inloggegevens gevonden | `~/.dugout-import.json` ontbreekt of is leeg |
| Inloggen mislukt | Verkeerd e-mailadres of wachtwoord in dat bestand |
| stond er al, geen tweede kaart | Goed nieuws — deze aanvraag was al ingeladen |
| Formuliervariant niet herkend | Nieuw soort aanvraagmail; stuur het bestand naar Tigo |

Bestanden in de map `mislukt` zijn niet verwerkt. Meld dat, en gooi ze niet weg.
