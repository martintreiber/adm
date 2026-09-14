# Anleitung · das Projekt in fünf Schritten

Vom Pitch bis zur Entscheidungsvorlage in fünf Schritten. Jeder Schritt sagt, was ihr tut, was danach im Repo liegt, was ihr in die Projektdokumentation schreibt und woran ihr merkt, dass er fertig ist. Deliverable 2 (Tag `termin3`, 9.10.) ist Schritt 1 bis 4. Deliverable 3 (Tag `termin4`, 23.10.) ist Schritt 5.

Das LLM darf jeden Schritt für euch bauen. Die Entscheidungen in jedem Schritt sind eure, und sie stehen im Entscheidungslog: Datum, Entscheidung, Alternative, Grund. Wo es keine Alternative gab, war es keine Entscheidung.

**Das Beispiel im Repo.** Jeder Schritt ist für die Testdaten in `data/sample/` schon einmal gebaut; der Code liegt in `src/`, die Ausschnitte unten stammen daraus. Vier Quellen einer Fahrzeugflotte, wie im Walkthrough aus Einheit 1:

| Quelle | Datei | Form | Was daran schwierig ist |
|---|---|---|---|
| Werkstattrechnungen | `data/sample/beispiel.csv` | CSV, 22 Zeilen, sauber | ein Duplikat, eine Zeile ohne Betrag, Kennzeichen in zwei Schreibweisen |
| Stammdaten der Flotte | `data/sample/flotte_stammdaten.csv` | CSV-Export aus Excel, 253 Zeilen, 43 Spalten | zwei Kommentarzeilen, Latin-1, deutsche Zahlen, zehn Kilometerstände als Spalten, Fahrernamen, 22 eingebaute Fehler (`src/synth/fehlerkatalog.md`) |
| Tankkartenabrechnung | `data/sample/belege/tankkarten_2025-03.pdf` | Text-PDF, 27 Seiten, ein Fahrzeug je Seite | Zeilen mit regulären Ausdrücken lesen, Rabatte als `0,76-`, Summe je Seite gegen Seite 1 |
| Ladekartenrechnung | `data/sample/belege/ladekarten_2025-01.pdf` | Text-PDF, 6 Seiten | fünf Positionszeilen je Ladenetz, Übertrag über Seiten, eine Karte ohne Kennzeichen |
| Reparaturrechnungen | `data/sample/belege/reparaturen/RR_01.pdf` bis `RR_12.pdf` | Scans ohne Textebene | OCR oder Vision-Modell, drei Layouts, ein Duplikat, Privatadressen (Schritt 5, Prompt-Anteil) |

Die Frage des Adressaten dazu (Flottenverantwortliche): Welche Leasingverträge laufen auf Mehrkilometer zu, und was kosten Tanken, Laden und Reparaturen je Fahrzeug? Wie das als Pitch aussieht: `docs/pitch/Poster.html`.


---

## Schritt 1 · Datenzugriff sicherstellen

**Ziel:** Die Rohdaten liegen lokal vor, unverändert, mit Datum.

1. Quellen beschaffen: CSV-Export, Excel, PDF-Ordner, API-Abruf, Download eines offenen Datensatzes. Zwei Quellen sind besser als eine, weil erst dann etwas zusammenzuführen ist.
2. Ablegen unter `data/raw/<datum>/`, etwa `data/raw/2026-09-20/`. Der Ordnername ist das Abrufdatum. Die Dateien werden nie verändert.
3. Zählen: wie viele Dateien, wie viele Zeilen, welcher Zeitraum. Diese Zahlen sind der erste Eintrag im Qualitätsbericht.
4. Prüfen, ob Personenbezug drin ist (Handout 05). Wenn ja: entweder die Spalten in Schritt 2 entfernen, oder die Daten vorher synthetisieren (Handout 12; ein fertiges Beispiel liegt in `src/synth/`). Echte Daten mit Personenbezug kommen nie ins Repo und nie in ein Cloud-Modell.

**Im Repo danach:** nichts. `data/raw/` ist gitignored. Im Repo steht nur, was dort liegt (Projektdoku, Schritt 1).

**In der Doku** (`docs/projektdokumentation/02_schritt1_datenzugriff.md`)**:** je Quelle: Herkunft (System, Export, Download), Format, Abrufdatum, Freigabe oder Lizenz, Anzahl Zeilen, was fehlt (Zeiträume, Entitäten).

**Fertig wenn:** `ls data/raw/<datum>/` zeigt die Dateien, und ihr könnt zu jeder sagen, woher sie kommt und was drin ist.

**Im Beispiel:** Die Quellen stehen in `src/config.py`, je Quelle Datei und Leseeinstellungen. `src/extract.py` kopiert sie nach `data/interim/` und schreibt `provenienz.json` mit Dateinamen und Größe.

```python
# src/config.py
QUELLEN = {
    "rechnungen":  {"datei": "beispiel.csv",            "sep": ";", "encoding": "utf-8",   "skiprows": 0},
    "stammdaten":  {"datei": "flotte_stammdaten.csv",   "sep": ";", "encoding": "latin-1", "skiprows": 2},
    "tankkarten":  {"datei": "belege/tankkarten_2025-03.pdf"},
    "ladekarten":  {"datei": "belege/ladekarten_2025-01.pdf"},
}
PII_COLUMNS = ["Fahrer (Nach- und Vorname)", "Bemerkung"]   # das Modell sieht diese Spalten nie
```

Eure Daten: `data/raw/<datum>/` anlegen, die Dateien hineinlegen, `QUELLEN` anpassen. Die Pipeline nimmt den neuesten Datumsordner.


---

## Schritt 2 · Daten auslesen und normalisieren

**Ziel:** Je Quelle eine saubere Tabelle. Gleiche Typen, gleiche Schreibweisen, keine Duplikate, keine Personenspalten.

1. Einlesen, alles als Text (`dtype=str`). Trennzeichen, Encoding, Kopfzeile je Quelle in `src/config.py` festhalten. Excel braucht `openpyxl`, PDF braucht `pdfplumber` oder OCR; das LLM schreibt den Leser.
2. Umwandeln, Spalte für Spalte: Zahlen (`1.234,56` oder `1234.56`?), Daten (`04.06.2025` ist der Juni), Einheiten (Cent oder Euro, Meilen oder Kilometer). Jede Umwandlung ist eine Entscheidung; falsch entschieden sieht sie unauffällig aus.
3. Schlüssel vereinheitlichen: `G 123AB`, `G-123AB` und `g123ab` sind ein Fahrzeug. Ohne das zählt eine Entität doppelt.
4. Duplikate innerhalb der Quelle entfernen, fehlende Werte kennzeichnen statt löschen, Ausreißer markieren statt löschen.
5. Personenspalten entfernen oder ersetzen, hier im Code (`PII_COLUMNS` in `src/config.py`, Entfernung in `src/clean.py`), nicht später im Prompt.
6. Zählen, was passiert ist: gelesene Zeilen, geänderte Werte, entfernte Duplikate, fehlende Werte, entfernte Spalten. Die Pipeline gibt die Zahlen aus.

**Im Repo danach:** `src/clean.py` (je Quelle eine Funktion), `src/config.py` mit den Einstellungen. Die Zwischenstände in `data/interim/` sind gitignored.

**In der Doku** (`docs/projektdokumentation/03_schritt2_normalisieren.md`)**:** der Qualitätsbericht je Quelle (vollständig, korrekt, konsistent, aktuell, wem gehört sie, woher kommt sie), jeweils mit Befund und Konsequenz. Die PII-Entscheidung: welche Spalten weg, wo im Code, warum. Die Zahlen aus Punkt 6.

**Fertig wenn:** `python src/run.py` läuft zweimal durch und meldet beide Male dieselben Zahlen.

**Im Beispiel:** `src/clean.py`, eine Funktion je Quelle. Die drei Hilfsfunktionen oben in der Datei sind die Stellen, an denen die Entscheidungen fallen:

```python
def normalize_id(value):
    """'G 123AB', 'G-123AB', 'g123ab' werden zu 'G123AB'. Mehrere Kennzeichen in einer Zelle: das erste."""
    first = str(value).split("/")[0]
    return re.sub(r"[\s\-]", "", first).upper()

def to_number(value):
    """'1 234,56' und '1.234,56' -> 1234.56; '0,76-' -> -0.76; leer, '-' und '#BEZUG!' -> NaN.
    Ein Punkt gilt als Tausenderpunkt. Liefert eure Quelle '123.02', braucht sie eine eigene Funktion."""

def to_date(value):
    """'04.06.2025' -> 2025-06-04 (Tag zuerst!), Excel-Seriennummer '43360' -> 2018-09-17."""
```

So liest die Funktion `stammdaten()` den Excel-Export, wandelt um, zählt und dreht die Kilometerstände von Spalten in Zeilen:

```python
df = pd.read_csv(INTERIM / "flotte_stammdaten.csv", sep=";", encoding="latin-1", skiprows=2, dtype=str)
df.columns = [" ".join(c.split()) for c in df.columns]           # Zeilenumbrüche in Überschriften
df["kennzeichen"] = df["Kennzeichen"].map(normalize_id)
for col in ["kW", "Laufleistung gesamt (km)", "Leasingrate exkl. MwSt", ...]:
    df[col] = df[col].map(to_number)
for col in ["Erstzulassung", "Vertragsbeginn", "Vertragsende", ...]:
    df[col] = df[col].map(to_date).dt.date
cent = df["Mehrkilometer (EUR/km)"] > 1                            # Einheitenwechsel: Cent statt Euro in einer Teilmenge
df.loc[cent, "Mehrkilometer (EUR/km)"] /= 100
df["Antrieb"] = df["Antrieb"].map({"D": "Diesel", "B": "Benzin", "E": "Elektro", "H/B": "Hybrid", "H/D": "Hybrid"})
dups = df.duplicated(subset=["Objektnr."]).sum()                   # dieselbe Objektnummer mit anderer Kennzeichen-Schreibweise
df = df.drop_duplicates(subset=["Objektnr."])
km_cols = [c for c in df.columns if c.startswith("km-Stand per")]  # zehn Spalten -> eine Zeile je Fahrzeug und Stichtag
km = df.melt(id_vars=["Objektnr."], value_vars=km_cols, var_name="stichtag", value_name="km")
df = drop_pii(df, "stammdaten")                                    # Fahrername und Bemerkung: weg, hier
```

Ein Text-PDF liest `tankkarten()` mit `pdfplumber` Zeile für Zeile und erkennt die Positionen mit einem regulären Ausdruck:

```python
with pdfplumber.open(INTERIM / "belege/tankkarten_2025-03.pdf") as pdf:
    seiten = [p.extract_text() or "" for p in pdf.pages]
kopf = re.compile(r"^([A-Z]{1,2}[\s\-]?\d{2,5}[A-Z]{1,2}) Obj: (\d+)")                       # "K 406JI Obj: 970676"
tank = re.compile(r"^(DKV EUROSERVICE|SHELL|OMV DOWN)\s?(\d{8}) (\d+) (?:(\d+)km )?([\d.,]+) Lit ([\d,]+) (\w+) ([\d.,]+)$")
for nr, text in enumerate(seiten, 1):
    for line in text.splitlines():
        if m := kopf.match(line): kz, obj = m[1], m[2]
        elif m := tank.match(line): zeilen.append(dict(seite=nr, kennzeichen=kz, objektnr=obj, datum=m[2], km_stand=m[4], liter=m[5], ...))
```

Was die Pipeline ausgibt, ist der Qualitätsbericht in Zahlen:

```
clean stammdaten: 253 Zeilen gelesen, 3 Duplikat(e) entfernt, 1 Zelle(n) mit mehreren Kennzeichen, 2 Mehrkilometer-Wert(e) von Cent auf Euro,
                  1 Fehlerwert(e) in Leasingrate, 1035 Kilometerstände, davon 5 rückläufig
clean tankkarten: 27 Seiten, 245 Positionen für 25 Fahrzeuge, Summe 5850.33 gegen Gesamtbetrag Seite 1 5.850,33, 1 Betrag/Liter-Widerspruch
```


---

## Schritt 3 · Zusammenführen und in SQLite ablegen

**Ziel:** Eine Datenbank, eine Tabelle je Entität, ein Schlüssel je Tabelle, Quellen über Schlüssel verknüpft.

1. Datenmodell festlegen: welche Tabellen, welche Primärschlüssel, welche Fremdschlüssel. In `src/sql/schema.sql` als `CREATE TABLE` mit `PRIMARY KEY` und `NOT NULL`. Die Datenbank lehnt dann ab, was nicht passt, statt es zu verstecken.
2. Die bereinigten Tabellen laden (`src/integrate.py`). Jeder Lauf löscht die Datenbank und baut sie neu.
3. Verknüpfen: Zeilen aus Quelle B, die keinen Partner in Quelle A finden, werden gezählt und benannt, nicht stillschweigend verworfen. Widersprüche zwischen Quellen (zwei Beträge für eine Rechnung) werden entschieden und die Entscheidung notiert.
4. Mit DB Browser for SQLite öffnen und nachsehen: Zeilen je Tabelle, ein paar Stichproben gegen die Rohdatei.

**Im Repo danach:** `src/sql/schema.sql`, `src/integrate.py`, `data/processed/<projekt>.sqlite` (wird committet; deshalb enthält sie keine Personenspalten).

**In der Doku** (`docs/projektdokumentation/04_schritt3_datenmodell.md`)**:** die Tabellen mit Schlüsseln und Zeilenzahl, die Beziehungen, die Zuordnungslücken mit Zahl, die Modellierungsentscheidungen (etwa: Kennzeichen als Schlüssel, weil die Objektnummer in Quelle B fehlt).

**Fertig wenn:** `pytest` ist grün (zweiter Lauf identisch, keine doppelten Schlüssel) und keine Zeile ist unerklärt ohne Zuordnung.

**Im Beispiel:** Fünf Tabellen in `src/sql/schema.sql`. Das Fahrzeug hat die Objektnummer als Schlüssel, nicht das Kennzeichen: Kennzeichen wechseln, und die Belege schreiben sie anders.

```sql
CREATE TABLE fahrzeug (
  objektnr        TEXT PRIMARY KEY,
  kennzeichen     TEXT NOT NULL,      -- normalisiert (G123AB), Index, aber kein Schlüssel
  marke           TEXT NOT NULL,
  status          TEXT NOT NULL,      -- aktiv, inaktiv, in Bestellung
  vertragsbeginn  TEXT, vertragsende TEXT, laufleistung_km REAL, freikilometer REAL,
  fahrerkategorie TEXT,               -- die Person selbst ist entfernt (PII)
  ladekarte_nr    TEXT                -- Schlüssel zur Ladekartenrechnung
);
CREATE TABLE kilometerstand (objektnr TEXT REFERENCES fahrzeug, stichtag TEXT, km REAL, PRIMARY KEY (objektnr, stichtag));
CREATE TABLE tankung (tankung_id INTEGER PRIMARY KEY, objektnr TEXT REFERENCES fahrzeug, kennzeichen TEXT NOT NULL, datum TEXT, position TEXT, liter REAL, betrag_eur REAL NOT NULL, ...);
CREATE TABLE ladung  (ladung_id INTEGER PRIMARY KEY, kartennr TEXT NOT NULL, objektnr TEXT REFERENCES fahrzeug, netz TEXT, energie_kwh REAL, betrag_eur REAL NOT NULL, ...);
```

`src/integrate.py` löscht die Datenbank, legt das Schema an, lädt die bereinigten Tabellen und verknüpft: Tankungen über die Objektnummer auf dem Beleg (zweiter Weg: Kennzeichen), Ladungen über die Ladekartennummer in den Stammdaten (zweiter Weg: Kennzeichen). Was keinen Partner findet, bleibt mit `objektnr NULL` drin und wird gezählt:

```python
bekannt = set(fahrzeug["objektnr"]); kz_map = dict(zip(fahrzeug["kennzeichen"], fahrzeug["objektnr"]))
tk["objektnr"] = [o if o in bekannt else kz_map.get(k) for o, k in zip(tk["objektnr"], tk["kennzeichen"])]
karte_map = dict(zip(fahrzeug["ladekarte_nr"].dropna(), fahrzeug.loc[fahrzeug["ladekarte_nr"].notna(), "objektnr"]))
ld["objektnr"] = [karte_map.get(k) or kz_map.get(z) for k, z in zip(ld["kartennr"], ld["kennzeichen"])]
```

```
integrate: beispiel.sqlite: fahrzeug 250, kilometerstand 1035, rechnung 21, tankung 245, ladung 41; ohne Fahrzeug: 0 Tankpositionen, 0 Ladezeilen, 0 Rechnungen
```

Mit DB Browser for SQLite öffnen: `data/processed/beispiel.sqlite`.


---

## Schritt 4 · Abfragen und Referenzantworten erstellen

**Ziel:** Die Kennzahlen als SQL, und für jede Analyse eine Referenzantwort, die vor dem Modell existiert.

1. Je numerische Analyse eine Abfrage `src/sql/kennzahl_<name>.sql`. Die Pipeline führt sie aus und legt das Ergebnis als CSV in `data/processed/` ab. Das Modell rechnet nie.
2. Drei Werte je Abfrage von Hand nachrechnen, mit Taschenrechner oder Excel aus der Rohdatei. Stimmen sie nicht, ist meist die Abfrage falsch, manchmal die Bereinigung.
3. Für Extraktion oder Klassifikation: mindestens acht Fälle, besser zwölf, händisch erfassen. Je Fall Eingabe, erwartete Antwort, wer sie erfasst hat, wo „richtig" unsicher ist. Als JSON in `evals/references/`. Das dauert eine Stunde; nicht auf den letzten Abend legen.
4. Je Analyse festlegen, wie verglichen wird: exakt, numerisch mit welcher Toleranz, oder gegen welche Kriterienliste.

**Im Repo danach:** `src/sql/kennzahl_*.sql`, `data/processed/kennzahl_*.csv`, `evals/references/*.json`.

**In der Doku** (`docs/projektdokumentation/05_schritt4_abfragen_referenzen.md`)**:** je Analyse eine Zeile: Frage, Referenz, Herkunft der Referenz, Prüfregel, Toleranz. Wo die Referenz selbst unsicher ist.

**Fertig wenn:** Für jede Analyse steht, woran ihr erkennen werdet, ob das Modell recht hat, und noch kein Modell ist gelaufen. Das ist Deliverable 2. Tag setzen: `git tag termin3 && git push --tags`.

**Im Beispiel:** Drei Abfragen in `src/sql/`, `derive.py` führt alles aus, was `kennzahl_*.sql` heißt, und legt je eine CSV in `data/processed/` ab. Die Mehrkilometer-Prognose:

```sql
-- src/sql/kennzahl_mehrkilometer.sql: letzten Kilometerstand je Fahrzeug holen, auf das Vertragsende hochrechnen,
-- mit Laufleistung plus Freikilometer vergleichen. Fahrzeuge ohne Kilometerstand bleiben in der Liste, mit Hinweis.
WITH letzter AS (
  SELECT k.objektnr, k.stichtag, k.km FROM kilometerstand k
  JOIN (SELECT objektnr, MAX(stichtag) AS stichtag FROM kilometerstand GROUP BY objektnr) m USING (objektnr, stichtag)
)
SELECT f.objektnr, f.kennzeichen, f.vertragsende, f.laufleistung_km, f.freikilometer, l.km AS letzter_km,
       ROUND(l.km / (julianday(l.stichtag) - julianday(f.vertragsbeginn))
             * (julianday(f.vertragsende) - julianday(f.vertragsbeginn)))            AS prognose_km_vertragsende,
       ROUND(... - f.laufleistung_km - COALESCE(f.freikilometer, 0))                 AS mehrkilometer_prognose,
       CASE WHEN l.km IS NULL THEN 'kein Kilometerstand' ELSE 'ok' END               AS hinweis
FROM fahrzeug f LEFT JOIN letzter l USING (objektnr)
WHERE f.status = 'aktiv' AND f.laufleistung_km IS NOT NULL
ORDER BY mehrkilometer_prognose DESC;
```

Die Spalte `hinweis` zuerst lesen: Zeilen mit „zu kurze Laufzeit" oder „kein Kilometerstand" stehen am Ende der CSV und liefern Prognosen, die nichts taugen; wer die Tabelle blind in die Vorlage zitiert, zitiert Unsinn. Dazu `kennzahl_tankkosten.sql` (Liter, Euro, Rabatt, Kilometer je Fahrzeug) und `kennzahl_ladekosten.sql` (kWh, Euro, Euro je kWh, Anteil Schnellladen je Karte). Die Referenzen dazu: drei Fahrzeuge von Hand aus den Stichtagen und dem Vertrag rechnen; für die Rechnungs-PDFs liegen die Referenzen in `evals/references/`, weil sie beim Erzeugen der Testdaten mitgeschrieben wurden. Bei euren Daten erfasst ihr sie händisch.


---

## Schritt 5 · Analyse durchführen und Entscheidungsvorlage schreiben

**Ziel:** Die Antworten auf die Analysen, geprüft, und die Vorlage für den Adressaten.

Zwei Hälften, getrennt:

**5a · Zahlen.** Kommen aus Schritt 4. Die Kennzahl-CSVs sind die Antwort; sie werden zitiert, nicht neu berechnet.

**5b · Modell.** Alles, was sich nicht berechnen lässt: Felder aus Dokumenten, Kategorien, Text.

1. Prompt schreiben, in `prompts/<name>_v1.md`. Jede Änderung ist eine neue Version, mit Zeile im `CHANGELOG.md`.
2. Eval-Suite bauen: die Referenzen aus Schritt 4 werden Tests in `evals/<suite>.yaml`. Drei Beispiele liegen dort. Laufen lassen: `npx promptfoo@latest eval -c evals/<suite>.yaml`.
3. Modell wählen: mindestens eines, kostenlos erreichbar (OpenRouter `:free` oder LM Studio). Modellname, Datum, Trefferquote, Kosten, Zeit ins Log. Ein zweites Modell ist optional und zählt für „überzeugend".
4. Ergebnisse lesen, nicht nur zählen: Welche Fälle scheitern, warum, und was würde die Suite nie bemerken?
5. Vorlage schreiben, `docs/vorlage.md`, Gliederung in Handout 09. Das LLM darf den Text schreiben. Jede Zahl darin kommt aus einer Kennzahl-CSV oder einem bestandenen Eval und nennt ihre Herkunft. Der Abschnitt „Was wir nicht wissen" ist konkret.
6. Übergabe: `docs/betrieb.md` fertig, `CLAUDE.md` ausgefüllt, `requirements.txt` und `.env.example` aktuell. Dann das Repo in ein neues Verzeichnis klonen und nur der README folgen. Was dabei hakt, kommt in README oder Betriebshandbuch.

**Im Repo danach:** `prompts/`, `evals/`, `docs/vorlage.md`, `docs/betrieb.md`, `CLAUDE.md`.

**In der Doku** (`docs/projektdokumentation/06_schritt5_analyse_vorlage.md`)**:** die Suite (Modell, Trefferquote je Task, Kosten, Zeit), die Modellwahl mit Begründung, die Blindstellen der Suite, der Selbsttest (Datum, was gehakt hat), und die Lessons.

**Fertig wenn:** Ihr könnt jede Zahl in der Vorlage in zwei Minuten am Beamer bis zur Rohdatei zurückverfolgen. Das ist Deliverable 3. Tag setzen: `git tag termin4 && git push --tags`.

**Im Beispiel:** Die Reparaturrechnungen sind der Prompt-Anteil: Scans, drei Layouts, kein Text. `python src/scans_rendern.py` macht aus jedem Beleg ein PNG der ersten Seite. Der Prompt `prompts/extraktion_scan_v1.json` ist eine Chat-Nachricht mit Text und Bild und verlangt JSON mit Rechnungsnummer, Datum, Kennzeichen, Netto, Brutto. Die Suite `evals/extraktion_scans.yaml` schickt die zwölf PNGs an ein Vision-Modell und prüft jedes Feld mit `evals/graders/feldvergleich_scan.py` gegen `evals/references/reparaturrechnungen.json`, mit Teilpunkten je Feld. Wie man sie startet, steht in `evals/README.md`. Das Beispiel zeigt auch die Schleife: Prompt v1 traf 6 von 12, weil er nicht sagte, welches Datum gemeint ist; v2 traf 10 von 12, die Zeile dazu steht in `prompts/CHANGELOG.md`. Zum Vergleich der Form: `evals/extraktion.yaml` macht dasselbe mit zwei getippten Rechnungstexten aus `beispiel.csv`. Was vorher zu klären ist: Auf den Rechnungen stehen Fahrernamen und Privatadressen. Entweder lokal (LM Studio, Vision-Modell) oder vorher maskieren. Die Zahlen für die Vorlage kommen aus den drei Kennzahl-CSVs, nicht aus dem Modell; `prompts/empfehlung_v1.md` bekommt die Tabelle und schreibt den Text, `evals/judge.yaml` prüft, dass keine Zahl darin steht, die nicht in der Tabelle steht.


---

## Immer

- Jede Arbeitssitzung: `git add . && git commit -m "was und warum" && git push`. Wenn das LLM beteiligt war, steht das drin.
- Jede Entscheidung mit Alternative sofort ins Entscheidungslog (`docs/projektdokumentation/01_entscheidungslog.md`), nicht am Ende rekonstruieren.
- Was wann abgegeben wird, Datei für Datei: `docs/projektdokumentation.md`.
- Wenn etwas hängt: `docs/troubleshooting.md`.
