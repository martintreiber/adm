# Schritt 2 · Auslesen und normalisieren

**Was die Pipeline je Quelle tut** (`src/clean.py`): Einstellungen (Trennzeichen, Encoding), Umwandlungen (Zahlen, Daten, Einheiten), Schlüsselnormalisierung, Duplikate, fehlende Werte. Die Zahlen aus dem Pipeline-Lauf:

| Quelle | Zeilen gelesen | Werte geändert | Duplikate entfernt | fehlende Werte | Spalten entfernt (PII) |
|---|---|---|---|---|---|
| | | | | | |

**Qualitätsbericht**, je Quelle mit Konsequenz:

| Frage | Befund | Konsequenz („deshalb …") |
|---|---|---|
| Vollständig? | | |
| Korrekt? (Stichprobe gegen Rohdatei) | | |
| Konsistent? (Schlüssel, Schreibweisen, Einheiten) | | |
| Aktuell? | | |
| Wem gehört sie? | | |
| Woher kommt sie, lückenlos? | | |

**PII-Entscheidung:** Spalten, die das Modell nie sieht; Stelle im Code (Datei, Funktion); was deshalb nur lokal oder gar nicht mit LLMs verarbeitet wird.
