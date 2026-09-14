# Entscheidungslog

| Datum | Entscheidung | Alternative | Warum | Folge |
|---|---|---|---|---|
| 14.9. | Objektnummer ist der Schlüssel, nicht das Kennzeichen | Kennzeichen als Schlüssel | Kennzeichen wechseln und stehen in drei Schreibweisen | `schema.sql`: `fahrzeug.objektnr PRIMARY KEY`, Kennzeichen nur Index |
| 14.9. | Kilometerstände von zehn Spalten in eine Tabelle mit einer Zeile je Stichtag | Spalten behalten | ein neuer Stichtag wäre eine neue Spalte, also eine Schemaänderung | `clean.py` `melt`, Tabelle `kilometerstand` |
| 14.9. | Mehrkilometer-Werte über 1 durch 100 teilen | Zeilen ausschließen | drei Zeilen führen Cent statt Euro, Rest ist plausibel | `clean.py`, gezählt im Bericht |
| 14.9. | Rückläufige Kilometerstände bleiben drin | löschen | sie sind ein Befund, kein Fehler der Pipeline; die Prognose nimmt den letzten Stand | `kennzahl_mehrkilometer.sql`, Hinweis in „Was wir nicht wissen" |
| 14.9. | Fahrername und Bemerkung werden in `clean.py` entfernt | im Prompt ausschließen | Bemerkung enthält Namen im Freitext; das Modell sieht `data/processed/` | `PII_COLUMNS` in `config.py` |
