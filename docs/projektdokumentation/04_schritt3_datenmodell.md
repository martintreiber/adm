# Schritt 3 · Zusammenführen und ablegen

**Datenmodell** (`src/sql/schema.sql`, `data/processed/<projekt>.sqlite`):

| Tabelle | Primärschlüssel | Fremdschlüssel | aus Quelle | Zeilen |
|---|---|---|---|---|
| | | | | |

Beziehungen: …

Zuordnungslücken (Zeilen ohne Partner, Widersprüche zwischen Quellen) mit Zahl und Entscheidung: …

Modellierungsentscheidungen (etwa: was zum Schlüssel wurde und warum): …

Startbefehl: `python src/run.py` · Prüfung: `pytest` (zweiter Lauf identisch, keine doppelten Schlüssel)
