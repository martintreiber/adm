# Synthetische Flottendaten · der regelbasierte Weg

Vier Quellen, alle synthetisch aus echten Vorlagen aus dem Flottenmanagement (Handout 12, Weg „regelbasiert, an echte Daten kalibriert"). Die Struktur ist echt, jede Zeile ist erfunden. Zusammen ergeben sie den Walkthrough aus Einheit 1: Stammdaten als CSV, Tank- und Ladekosten als PDF des Leasinggebers und des Ladenetzbetreibers, Reparaturen als PDF-Scans in drei Layouts.

| Quelle | Datei | Form | Referenz |
|---|---|---|---|
| Stammdaten | `data/sample/flotte_stammdaten.csv` | CSV, 253 Fahrzeuge, 43 Spalten | `fehlerkatalog.md` |
| Tankkarten | `data/sample/belege/tankkarten_2025-03.pdf` | Text-PDF, 27 Seiten, ein Fahrzeug je Seite | `evals/references/tankungen_2025-03.csv` |
| Ladekarten | `data/sample/belege/ladekarten_2025-01.pdf` | Text-PDF, 6 Seiten, Positionen je Karte und Ladenetz, Übertrag über Seiten | `evals/references/ladungen_2025-01.csv` |
| Reparaturen | `data/sample/belege/reparaturen/RR_01.pdf` bis `RR_12.pdf` | Karosserie digital + gescannte Zession; Markenwerkstatt als Scan (Nadeldruck); ein Duplikat | `evals/references/reparaturrechnungen.json` |

Die Referenzen sind beim Erzeugen entstanden: Wer die Rechnung schreibt, kennt den Betrag. Sie sind die Wahrheit für Extraktions-Evals. Was absichtlich falsch ist, steht in `fehlerkatalog.md` (Stammdaten) und `fehlerkatalog_belege.md` (Belege).

## Dateien

| Datei | Was | Im Repo |
|---|---|---|
| `fit.py` | liest die echte Stammdatei lokal und schreibt Aggregate nach `params.json`: Häufigkeiten je Kategorie, Quantile je Zahlenspalte, Fehlquoten, Datumsbereiche, Kilometer je Monat. Keine Einzelzeile, keine Namen, keine Kennzeichen, keine Nummern | ja; die echte Datei nie |
| `params.json` | die Kalibrierung, aus 691 Zeilen und 91 Spalten eines echten Exports | ja |
| `generate.py` | erzeugt aus `params.json` mit festem Seed die Stammdatei, reduziert auf 43 Spalten, die jede Flotte führt, und baut Fehler ein | ja |
| `fehlerkatalog.md` | was in den Stammdaten absichtlich falsch ist, mit Objektnummern. Die Referenz für den Qualitätsbericht | ja |
| `fit_belege.py` | dasselbe für die Tank- und Ladekarten-PDFs; schreibt `params_belege.json` | ja; die echten PDFs nie |
| `generate_belege.py` | erzeugt die drei Belegtypen aus `params_belege.json` und den synthetischen Stammdaten; die Reparaturrechnungen sind aus drei echten Layouts nachgebaut, nicht statistisch kalibriert | ja |
| `pdfmini.py` | PDF-Writer ohne Abhängigkeiten (Text, Linien, Kästen) und `scan()`, das aus einem Text-PDF einen Scan ohne Textebene macht | ja |
| `fehlerkatalog_belege.md` | was in den Belegen absichtlich falsch ist, und welche Summen sich gegenseitig prüfen | ja |

```bash
python src/synth/generate.py                 # Stammdaten, 253 Zeilen, deterministisch (Seed 42)
python src/synth/generate_belege.py          # Belege und Referenzen; braucht pdfplumber (für die Scans)
python src/synth/fit.py "/lokal/echte_datei.csv"                    # nur mit der echten Datei; schreibt params.json neu
python src/synth/fit_belege.py "/lokal/tank.pdf" "/lokal/lade.pdf"  # nur mit den echten PDFs
```

## Stammdaten

Spalten: Fahrzeug (Objektnr., Kennzeichen, Fahrgestell-Nr., Marke, Modell, Antrieb, Typ, kW, CO2, Erstzulassung, Status), Vertrag (Leasinggeber, Beginn, Ende, Laufzeit, Laufleistung, Freikilometer, Mehr-/Minderkilometer, Raten, Anschaffungswert), Nutzung (Fahrer, Fahrerkategorie, Kostenstelle, Standort, Ladekarte, Ladung@home, Überprüfung), zehn Kilometerstände je Stichtag, Bemerkung.

Was erfunden ist: Fahrernamen (aus zwei Namenslisten), Kennzeichen, Fahrgestell-, Objekt- und Ladekartennummern, Kostenstellen, Standorte, Bemerkungen. Was kalibriert ist: die Verteilung von Marke, Modell, Antrieb, Status, Leasinggeber, Laufzeit, Freikilometer, die Geldspalten, die Fehlquoten, die Kilometerleistung je Monat. Was nicht abgebildet ist: Zusammenhänge zwischen Spalten außer Marke→Modell→Antrieb und Erstzulassung→Kilometerstände→Vertragsende. Ein teures Fahrzeug ist deshalb nicht öfter ein BMW.

So lest ihr die Datei ein (Schritt 2):

```python
import pandas as pd
df = pd.read_csv("data/sample/flotte_stammdaten.csv", sep=";", encoding="latin-1", skiprows=2, dtype=str)
```

## Belege

Tankkarten und Ladekarten sind Text-PDFs, wie sie der Leasinggeber und der Ladenetzbetreiber schicken: `pdfplumber` liest sie, die Zeilen sind regelmäßig genug für reguläre Ausdrücke, ein Modell braucht es dafür nicht unbedingt. Die Reparaturrechnungen sind Scans ohne Textebene (bis auf die erste Seite der Karosserie-Rechnungen); hier braucht es OCR (`pytesseract`) oder ein Vision-Modell, und hier steht auf mehreren Belegen der Fahrername mit Privatadresse. Vor einem Cloud-Modell maskieren oder lokal verarbeiten.

```python
import pdfplumber
with pdfplumber.open("data/sample/belege/tankkarten_2025-03.pdf") as pdf:
    seiten = [p.extract_text() for p in pdf.pages]   # Seite 1 Summen, dann ein Fahrzeug je Seite, letzte Seite Abgleich
```

Schlüssel zwischen den Quellen: das Kennzeichen (in drei Schreibweisen), die Ladekartennummer (Stammdaten ↔ Ladekarten-PDF), die Objektnummer (Stammdaten ↔ Tankkarten-PDF). Prüfbare Zusammenhänge: Kilometerstände in Tankungen gegen die Stichtage der Stammdaten, Summe je Fahrzeug gegen die Gesamtsumme des Belegs, Übertrag am Seitenende gegen den Seitenanfang, Netto + MwSt gegen den Endbetrag. Die drei Kennzeichen aus `beispiel.csv` kommen in den Stammdaten vor.
