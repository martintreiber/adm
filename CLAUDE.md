<!-- Anweisung für jedes LLM, das in diesem Repo arbeitet. So sieht sie für das Beispielprojekt aus; mit Deliverable 3 ersetzt ihr sie durch eure. Kurz, im Imperativ, in der Sprache des Projekts. -->

# Projekt Flotte (Beispiel des Starter-Repos)

## Was das ist
Entscheidungsvorlage für Flottenverantwortliche: Welche Leasingverträge laufen auf Mehrkilometer zu, was kosten Tanken, Laden und Reparaturen je Fahrzeug? Drei Analysen: Mehrkilometer-Prognose (SQL), Tank- und Ladekosten je Fahrzeug (SQL), Felder aus Reparaturrechnungen (Prompt gegen Scans). Alle Daten in data/sample/ sind synthetisch.

## Wo was liegt
- data/sample/   Testdaten: flotte_stammdaten.csv, beispiel.csv, belege/ (zwei Text-PDFs, zwölf Scans). Nie ändern; erzeugt von src/synth/
- data/raw/<datum>/   echte Rohdaten (Snapshot), nie ändern, nie lesen; liegen nur lokal
- data/interim/   Zwischenstände, nie lesen; PNGs der Scans in scans/ enthalten Privatadressen
- data/processed/beispiel.sqlite   erzeugt von src/run.py; Kennzahlen als kennzahl_*.csv daneben
- src/   Pipeline: config.py (QUELLEN, PII_COLUMNS), clean.py (eine Funktion je Quelle), integrate.py, derive.py; src/sql/ Schema und Kennzahlen
- evals/   promptfoo-Suiten, references/ die Wahrheit je Beleg, graders/ eigene Grader
- prompts/   versionierte Prompts, je Analyse eine Datei, Änderungen im CHANGELOG.md
- docs/   anleitung.md (fünf Schritte), projektdokumentation.md (Abgabeliste), projektdokumentation/ (Gerüst), projektdokumentation_beispiel/ (ausgefüllt), vorlage.md, betrieb.md, troubleshooting.md

## Datenmodell
- fahrzeug: objektnr ist der Schlüssel, nicht das Kennzeichen (wechselt, drei Schreibweisen). kennzeichen normalisiert: G123AB
- kilometerstand: eine Zeile je Fahrzeug und Stichtag; rückläufige Stände bleiben drin, sie sind ein Befund
- tankung: eine Zeile je Belegposition; betrag_eur negativ bei Rabatten; km_stand laut Zapfsäule, nicht laut Stammdaten
- ladung: eine Zeile je Karte, Netz und Leistungsklasse; Zuordnung über fahrzeug.ladekarte_nr
- Geld in EUR als REAL, Datum als ISO-Text. Mehrkilometer in EUR je km; Werte über 1 waren Cent und sind in clean.py geteilt

## Regeln
- Die Spalten "Fahrer (Nach- und Vorname)" und "Bemerkung" werden in src/clean.py entfernt (config.PII_COLUMNS). Nie auf Fahrerebene auswerten, nie Fahrernamen aus Belegen übernehmen.
- Zahlen in docs/vorlage.md kommen aus src/sql/ und data/processed/kennzahl_*.csv. Nie vom Modell rechnen lassen.
- kennzahl_mehrkilometer.csv: Spalte hinweis lesen; nur Zeilen mit 'ok' zitieren.
- Nach Änderungen an Prompts: npx promptfoo@latest eval -c evals/<suite>.yaml. Das Ergebnis kommt in die Commit-Message.
- Scans (data/sample/belege/reparaturen/, data/interim/scans/) nur an ein lokales Modell schicken.
- Rohdaten und .env nie committen. data/processed/ wird committet und enthält deshalb keine Personenspalten.
- Jede Änderung an clean.py: python src/run.py zweimal, pytest grün, Zahlen im Qualitätsbericht (docs/projektdokumentation_beispiel/03_…) nachziehen.

## Starten
python src/run.py && pytest && npx promptfoo@latest eval -c evals/promptfooconfig.yaml
