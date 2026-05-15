# Lernkarten-Trainer

Ein Lernkarten-Trainer fürs Terminal — mit ASCII-Design, sechs Farb-Themes,
gewichteter Wiederholungslogik und interaktiver Pfeil-/Vim-Navigation.

## Installation

Python 3.10+ wird vorausgesetzt. Externe Abhängigkeiten gibt es keine
(`requirements.txt` ist leer).

```bash
git clone <repo-url>
cd lernkarten-trainer
```

## Ausführen

Programm starten mit dem mitgelieferten Beispiel-Deck (12 Karten zu OS, SE und Netzwerken):

```bash
python lernkarten.py --file data/example_deck.json
```

Eigene Datei (wird automatisch angelegt):

```bash
python lernkarten.py --file data/eigenes_deck.json
```

Mit anderem Theme:

```bash
python lernkarten.py --theme matrix   # matrix | amber | ice (Default) | paper | synth | classic
```

## Bedienung

Im Menü:
- **↑ / ↓** oder **j / k** zum Navigieren
- **Enter** zum Auswählen
- **1–6** zur Direktwahl
- **t** öffnet die Theme-Auswahl
- **q** oder **Esc** beendet (Stand wird automatisch gespeichert)

In der Lernsession:
- **Enter** zeigt die Antwort
- **j / n** = richtig / falsch
- **x** bricht die Session vorzeitig ab (Fortschritt bleibt gespeichert)

## Tests

Alle Tests mit einem Befehl:

```bash
python -m unittest discover -s tests -v
```

56 Unit- und Integrationstests, abgedeckt sind u. a. leere Decks, fehlende
oder kaputte JSON-Dateien, Division durch null bei Erfolgsquoten und Abbruch
der Lernsession.

## Projektstruktur

```
lernkarten.py            # Start-Skript (Einstiegspunkt)
src/lernkarten/
    card.py              # Datenklasse für eine Lernkarte
    deck.py              # Verwaltung einer Kartensammlung
    storage.py           # Laden/Speichern als JSON
    session.py           # Lernsession + Wiederholungslogik
    statistics.py        # Auswertungen
    theme.py             # 6 Farb-Themes (24-Bit-ANSI)
    keyboard.py          # Einzeltasten-Eingabe (termios / msvcrt)
    cli.py               # Interaktives Menü mit ASCII-Design
tests/                   # Unit-Tests (unittest)
data/
    example_deck.json    # Beispiel-Deck zum Ausprobieren
```

## Speicherformat

JSON-Array. Jede Karte hat die Felder `question`, `answer`, `category`,
`correct_count`, `wrong_count`:

```json
[
  {
    "question": "Was ist ein Deadlock?",
    "answer": "Ein Zustand, in dem zwei oder mehr Prozesse blockieren …",
    "category": "Betriebssysteme",
    "correct_count": 5,
    "wrong_count": 0
  }
]
```

Fehlende `correct_count` / `wrong_count` werden als `0` interpretiert.
Fehlt eines der Pflichtfelder, lehnt der Loader die Datei ab.

## Wiederholungslogik

Die nächste Karte wird gewichtet zufällig gezogen:

```
gewicht(karte) = 1 + 3 * falsch_anteil + bonus_neu

  falsch_anteil = wrong_count / (correct_count + wrong_count)
  bonus_neu     = 2.0, falls die Karte noch nie beantwortet wurde
```

Damit werden falsch beantwortete und neue Karten bevorzugt, ohne dass
„leichte" Karten ganz aus der Rotation fallen.

## Lizenz

[MIT](LICENSE) — frei nutzbar, modifizierbar und weiterverbreitbar.
