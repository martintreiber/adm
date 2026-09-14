"""Pfade und Einstellungen der Pipeline. Nur hier ändern."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SAMPLE = ROOT / "data" / "sample"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
SQL = ROOT / "src" / "sql"
PROJEKT = "beispiel"                      # Name eures Projekts: ergibt data/processed/<projekt>.sqlite; Tests lesen ihn von hier
DB = PROCESSED / f"{PROJEKT}.sqlite"


def _snapshot(raw: Path):
    """Rohdaten liegen in data/raw/<datum>/ (ein Ordner je Abruf) oder direkt in data/raw/.
    Gibt den neuesten Ordner mit Dateien zurück, sonst data/raw/ selbst, sonst None."""
    if not raw.exists():
        return None
    has_files = lambda d: any(p.suffix.lower() in (".csv", ".pdf", ".xlsx") for p in d.rglob("*"))
    dated = sorted(d for d in raw.iterdir() if d.is_dir() and has_files(d))
    if dated:
        return dated[-1]  # ISO-Datum im Namen: der letzte ist der neueste
    return raw if any(p.suffix.lower() in (".csv", ".pdf", ".xlsx") for p in raw.glob("*")) else None


SNAPSHOT = _snapshot(RAW)
# Solange keine eigenen Rohdaten vorliegen, läuft die Pipeline auf data/sample/ (Testdaten). extract.py warnt dann.
SOURCE = SNAPSHOT or SAMPLE

# Je Quelle: Datei (relativ zum Snapshot-Ordner) und Leseeinstellungen. Eure Quellen: hier eintragen, die Funktionen in clean.py anpassen.
QUELLEN = {
    "rechnungen":  {"datei": "beispiel.csv",                    "sep": ";", "encoding": "utf-8",   "skiprows": 0},
    "stammdaten":  {"datei": "flotte_stammdaten.csv",           "sep": ";", "encoding": "latin-1", "skiprows": 2},
    "tankkarten":  {"datei": "belege/tankkarten_2025-03.pdf"},
    "ladekarten":  {"datei": "belege/ladekarten_2025-01.pdf"},
    # "reparaturen": Scans in belege/reparaturen/; Extraktion per OCR oder Modell ist der Prompt-Anteil (Schritt 5), Referenz in evals/references/
}

# Spalten mit Personenbezug, die das Modell nie sieht. Werden in clean.py entfernt, bevor etwas in data/processed/ landet.
PII_COLUMNS: list[str] = ["Fahrer (Nach- und Vorname)", "Bemerkung"]
