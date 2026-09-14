# ADDM Starter · Advanced Data Management, WS 2026

Vorlage für euer Projekt-Repo. Ein Datenprojekt von der Pipeline bis zur Entscheidungsvorlage, mit so viel LLM, wie ihr wollt. Bewertet wird euer Urteil, nicht der LLM-Output.

## Was hier liegt

| Ordner | Inhalt |
|---|---|
| `data/raw/` | eure Rohdaten, lokal, nie im Repo |
| `data/sample/` | erfundene Testdaten, damit die Pipeline beim Setup durchläuft: `beispiel.csv` (22 Werkstattrechnungen, sauber), `flotte_stammdaten.csv` (253 Fahrzeuge, 43 Spalten, synthetisch aus einem echten Export, absichtlich unordentlich) und `belege/` (Tankkarten- und Ladekarten-PDF, zwölf Reparaturrechnungen als Scans). Was absichtlich falsch ist: `src/synth/fehlerkatalog*.md`. Keine Projektdaten |
| `data/processed/` | die SQLite-Datenbank und die Kennzahlen-CSVs, die die Pipeline erzeugt; wird committet und ist Teil von Deliverable 2. Deshalb: PII ist vorher in `clean.py` entfernt (`PII_COLUMNS`), nicht erst im Prompt |
| `src/` | die Pipeline: `extract` → `clean` → `integrate` → `derive`, dazu `sql/` mit Datenmodell und Kennzahlen; `synth/` erzeugt die synthetischen Stammdaten (regelbasiert, Handout 12) |
| `evals/` | promptfoo-Suiten (vier Beispiele, darunter die Scans an ein Vision-Modell), Referenzantworten (auch die Wahrheit hinter den Belegen in `data/sample/belege/`), Grader; Anleitung in `evals/README.md` |
| `prompts/` | versionierte Prompts, je Analyse eine Datei, Änderungen im `CHANGELOG.md` |
| `docs/` | `anleitung.md` (das Projekt in fünf Schritten, hier anfangen), `projektdokumentation.md` (Abgabeliste: welche Datei, welcher Inhalt, wann), `projektdokumentation/` (die acht Dateien als Gerüst, zu füllen), `projektdokumentation_beispiel/` (dieselben acht Dateien, für die Testdaten ausgefüllt), Entscheidungsvorlage, Betriebshandbuch, Beispielposter (`pitch/Poster.html`), Vortragsfolie, Interview-Prompt, Troubleshooting |
| `tests/` | der Nachweis, dass die Pipeline zweimal dasselbe liefert, und die Prüfung des Zahl-Graders |
| `CLAUDE.md` | Anweisung für Agenten, die in diesem Repo arbeiten |

## Setup (einmalig, etwa zwanzig Minuten)

Voraussetzungen: Python 3.11 oder neuer (getestet mit 3.12 und 3.14, python.org), Node.js 20 oder neuer (für promptfoo, nodejs.org), Git. Für die Evals ein OpenRouter-Schlüssel (openrouter.ai, Konto ohne Kreditkarte, Keys unter „API Keys") oder LM Studio lokal (lmstudio.ai).

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # Windows: copy .env.example .env  · Schlüssel eintragen, Datei bleibt lokal
python src/run.py                                     # Pipeline auf data/sample/ → data/processed/beispiel.sqlite
pytest                                                # läuft die Pipeline zweimal, vergleicht; prüft den Zahl-Grader
npx promptfoo@latest eval -c evals/promptfooconfig.yaml --providers echo   # Konfiguration testen, ohne Modell
```

Der letzte Befehl lädt promptfoo beim ersten Mal herunter (eine Minute) und antwortet mit dem Prompt statt mit einem Modell: alle Tests sind rot, aber es gibt keine Fehler (`errors`). Das ist das erwartete Ergebnis. Mit Schlüssel in `.env` derselbe Befehl ohne `--providers echo`. Alle promptfoo-Befehle laufen aus dem Repo-Root mit `-c evals/<suite>.yaml`.

Läuft alles, ist das Setup fertig. Ab jetzt ersetzt ihr die Inhalte: eure Daten nach `data/raw/<datum>/`, eure Stufen in `src/`, eure Referenzen in `evals/references/`, eure Prompts in `prompts/`. Die Struktur bleibt. Wenn etwas hängt: `docs/troubleshooting.md`.

## Die Pipeline

`python src/run.py` führt vier Stufen aus, je mit einer Prüfung:

1. `extract.py` liest den neuesten Ordner `data/raw/<datum>/` (oder `data/raw/` selbst; ohne Rohdaten die Testdaten in `data/sample/`, mit Warnung), kopiert die Dateien nach `data/interim/` und schreibt `provenienz.json` (Quelle, Dateien, Laufdatum).
2. `clean.py` bereinigt je Quelle, eine Funktion je Quelle (`rechnungen`, `stammdaten`, `tankkarten`, `ladekarten`): Typen, Formate, IDs auf eine Schreibweise, Einheiten, Duplikate, fehlende Werte; entfernt die Spalten aus `PII_COLUMNS`. Zählt, was sie ändert.
3. `integrate.py` baut die SQLite neu aus `src/sql/schema.sql` (fünf Tabellen: fahrzeug, kilometerstand, tankung, ladung, rechnung), lädt die bereinigten Tabellen und verknüpft die Belege über Objektnummer, Ladekartennummer und Kennzeichen mit dem Fahrzeug. Was keinen Partner findet, wird gezählt.
4. `derive.py` führt alle `src/sql/kennzahl_*.sql` aus (Mehrkilometer-Prognose, Tankkosten, Ladekosten, Beispielkennzahl) und legt die Ergebnisse als CSV in `data/processed/` ab.

Die Pipeline ist idempotent: Jeder Lauf baut die Datenbank neu. `pytest` prüft das.

## Warum diese Werkzeuge

Jedes Werkzeug in diesem Repo hält eine Art von Wahrheit, die das davor nicht halten kann. Ihr müsst keines davon beherrschen; das LLM schreibt den Code. Ihr müsst wissen, was jedes tut und welche Entscheidung dort fällt, sonst trifft sie der Agent.

**Python** ist da, weil die Pipeline beliebig oft mit gleichem Ergebnis laufen muss. Excel ist eine Folge von Klicks, die niemand wiederholen kann; Power Query wiederholt sie, aber die Schritte liegen in einer Binärdatei, die Git nicht vergleichen kann, und sie kann weder ein Modell aufrufen noch in SQLite schreiben. Ein Skript ist eine aufgeschriebene Folge von Entscheidungen. Verstehen: Code lesen, bis ihr die Entscheidungen darin seht.

**pandas** hält eine Tabelle im Speicher und bringt die Operationen für schmutzige Daten mit. Eine CSV ist Text. Bevor sie eine Tabelle ist, entscheidet jemand, dass `1.234,56` eine Zahl ist, dass `G 123AB` und `G-123AB` derselbe Schlüssel sind, dass `04.06.2025` der Juni ist und nicht der April. Diese Entscheidungen fallen, bevor die Daten in einer Datenbank liegen; SQL kann sie nicht treffen, und SQLite kann weder Excel noch PDF öffnen. Verstehen: alles zuerst als Text lesen (`dtype=str`), jede Spalte ausdrücklich umwandeln, jede Änderung zählen. Jede Umwandlung ist eine Stelle, an der Daten unbemerkt falsch werden.

**openpyxl** und **pdfplumber** sind nur Leser: pandas öffnet ohne openpyxl kein `.xlsx`, und ein PDF ist keine Tabelle, sondern ein Textextraktionsproblem. pdfplumber liest die beiden Beleg-PDFs der Testdaten Zeile für Zeile; für Scans ohne Textebene reicht es nicht, dann braucht es OCR oder ein Vision-Modell. Wer nur CSVs hat, streicht beide Zeilen aus `requirements.txt` und die PDF-Quellen aus `src/config.py`.

**SQLite** ist das Ergebnis von Deliverable 2, und es ist eine Datenbank statt einer CSV, weil eine CSV keine Schlüssel, keine Typen und kein NOT NULL kennt. `rechnungsnr TEXT PRIMARY KEY` lehnt ein Duplikat ab, statt es zu verstecken; `kennzeichen NOT NULL` lehnt eine Zeile ohne Fahrzeug ab. Das Datenmodell ist damit eine durchgesetzte Behauptung, nicht eine Zeichnung. Eine Datei, kein Server, in Python enthalten, und mit dem DB Browser kann jede Person die Tabelle öffnen und Zeilen zählen. Verstehen: Die SQLite ist das, was der Lektor öffnet.

**SQL für Kennzahlen**, nicht pandas und nicht der Prompt: Berechenbares wird berechnet. Und in SQL statt in pandas, weil eine `.sql`-Datei eine Behauptung ist, die jede Person gegen die Datenbank laufen lassen kann, ohne Python zu lesen; dieselbe Abfrage ist die Referenz für den Eval. Rechnet ihr in pandas, liegt die Referenz in Code, den außer euch niemand ausführt.

**pytest** ist der Beweis für „zweiter Lauf identisch". Ein Test ist eine Behauptung, die fehlschlägt, wenn sie falsch ist; dieser lässt die Pipeline zweimal laufen und vergleicht die Datenbank. Verstehen: Wer die Tabelle umbenennt, zieht die Behauptung mit, statt den Test zu löschen.

**promptfoo** läuft auf Node und ist damit das einzige Werkzeug außerhalb von Python. Evals ließen sich auch in pytest schreiben; promptfoo ist im Template, weil ein Modellwechsel eine Zeile ist, weil ein Judge-Eval eingebaut ist und weil die Ergebnistabelle Trefferquote, Kosten und Zeit je Modell zeigt, genau das, was die Projektdoku in Schritt 5 verlangt. Der Preis ist eine zweite Laufzeitumgebung, und das ist die Abhängigkeit, die beim Setup am häufigsten scheitert. Verstehen: Eine Eingabe, eine Referenz, eine Prüfregel; alles andere ist Verpackung.

**Git** ist der Zeitstempel: Der Tag ist die Abgabe, die Commit-Message das Workflow-Log, die Historie das, womit sich das Entscheidungslog prüfen lässt. **`.env`** ist die eine Datei mit einem Geheimnis und deshalb die eine Datei, die nie ins Repo darf.

Was ihr verstehen müsst, in sechs Begriffen: Eine Tabelle hat typisierte Spalten und einen Schlüssel. Umwandlungen sind Entscheidungen. Deterministisch gegen stochastisch. Die Referenz existiert, bevor das Modell läuft. Idempotent heißt zweimal dasselbe. Ein Geheimnis liegt außerhalb des Repos. Wer das hat, kann einen Agenten durch pandas steuern, das er nicht schreiben könnte, und sieht, wenn der Agent eine Entscheidung getroffen hat, die eure war.

| Verbindlich | Standard, ersetzbar |
|---|---|
| Git, die Ordnerstruktur (Kursleitfaden) · SQLite als Ergebnis von Deliverable 2 · promptfoo für die Suite in Deliverable 3 (Rubric 2a, 2b) | pandas, openpyxl, pdfplumber, pytest. Ersatz ist erlaubt (Polars, csv, unittest), wenn er im Entscheidungslog steht und dieselbe Prüfung liefert |

## Git in sechs Momenten

1. **Repo anlegen:** oben rechts „Use this template" → „Create a new repository", Name vergeben, **Private**. Unter *Settings → Collaborators* den Lektor einladen. Dann `git clone <eure-URL>`.
2. **Was nie ins Repo darf:** `data/raw/`, `data/interim/`, `.env`, `.venv/` sind in `.gitignore`. Rohdaten und Schlüssel bleiben lokal. GitHub lehnt Dateien über 100 MB ab.
3. **Jede Arbeitssitzung sichern:** `git add . && git commit -m "was und warum" && git push`. Die Commit-Message ist Teil der Dokumentation; wenn das LLM beteiligt war, steht das drin.
4. **Abgabe ist ein Tag:** `git tag termin3 && git push --tags`. Ohne `--tags` existiert der Tag nur bei euch. Prüfen unter *Tags* auf GitHub. Für Deliverable 3: `termin4`.
5. **Wenn etwas schiefgeht:** falsche Datei committet → `git rm --cached <datei>`, `.gitignore` prüfen, neu committen (bei Personendaten den Lektor informieren). Tag falsch → `git tag -d termin3`, `git push origin :refs/tags/termin3`, neu setzen. Push abgelehnt → `git pull`, dann `git push`.
6. **Was der Lektor sieht:** den Stand beim Tag. Was danach kommt, zählt nicht für diese Abgabe.

Nur `main`, keine Branches. GitHub Desktop geht genauso: Clone, Commit to main, Push origin, Create Tag.

## Deliverables

| # | Deliverable | Was im Repo liegt | Abgabe |
|---|---|---|---|
| 1 | Pitch | `docs/projektdokumentation/00_auftrag.md`, Poster in `docs/pitch/` (Beispiel: `Poster.html`) | Gallery Walk |
| 2 | Datenpipeline | `src/`, `data/processed/<projekt>.sqlite`, `evals/references/`, Projektdoku: Auftrag, Log, Schritt 1 bis 4, `docs/betrieb.md` Entwurf | Tag `termin3` |
| 3 | Evaluierung und Entscheidungsvorlage | `docs/vorlage.md`, `evals/`, `prompts/`, Projektdoku komplett (Schritt 5, Lessons), `docs/betrieb.md` final, `CLAUDE.md`, `requirements.txt` und `.env.example` gepflegt | Tag `termin4` |
| 4 | Endpräsentation | optional eine Folie in `docs/vortrag/` | live |

Schritt für Schritt: `docs/anleitung.md`. Datei für Datei: `docs/projektdokumentation.md`. Regeln, Rubrics und Termine: Kursleitfaden in der Lernplattform.
