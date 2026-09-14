# Troubleshooting · wenn etwas hängt

Erst hier nachsehen, dann `README.md`. Bleibt es hängen: Mail an den Lektor mit Betriebssystem, dem Befehl und der vollständigen Fehlermeldung.

## Pipeline

**`ModuleNotFoundError: No module named 'pandas'`** · Das venv ist nicht aktiv. `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`), dann `pip install -r requirements.txt`. Auf Windows heißt Python manchmal `py` statt `python`.

**Die Pipeline bricht ohne Fehlermeldung ab (`Segmentation fault`, Exit-Code 139)** · Eine pandas-Version, die nicht zur Python-Version passt (pandas 2.2 läuft nicht auf Python 3.14). `pip install -U "pandas>=3.0"` oder Python 3.12 verwenden. `requirements.txt` gibt deshalb einen Bereich an, keine feste Version.

**`ACHTUNG: keine Rohdaten in data/raw/ ...`** · Die Pipeline läuft auf den Testdaten. Eure Rohdaten gehören nach `data/raw/<datum>/` (etwa `data/raw/2026-09-20/`). Liegen mehrere Ordner dort, nimmt die Pipeline den mit dem neuesten Datum im Namen. Welche Dateien sie dort erwartet, steht in `QUELLEN` in `src/config.py`; das sind zunächst die vier Testquellen. Eintragen, was ihr habt, und je Quelle eine Funktion in `clean.py`.

**`Quelle 'stammdaten' fehlt: data/raw/.../flotte_stammdaten.csv`** · `QUELLEN` in `src/config.py` nennt noch die Testdateien. Die Einträge durch eure Dateien ersetzen oder löschen, und die zugehörigen Funktionen in `clean.py` und Tabellen in `integrate.py` anpassen.

**`ModuleNotFoundError: No module named 'pdfplumber'`** · Die Testdaten enthalten zwei PDFs; `pip install -r requirements.txt` installiert pdfplumber. Wer keine PDFs hat, entfernt die beiden PDF-Quellen aus `QUELLEN`.

**`UnicodeDecodeError` beim Lesen** · Die Quelle ist nicht UTF-8, meist Latin-1 oder cp1252 aus Excel. `ENCODING` in `src/config.py` anpassen und im Entscheidungslog notieren.

**Zahlen sind hundertfach zu groß, Daten im falschen Monat** · `to_number` in `clean.py` erwartet deutsches Format (`1 234,56` oder `1.234,56`); bei Punkt als Dezimaltrenner wird `123.02` zu 12302. `to_date` liest `04.06.2025` als 4. Juni und `2025-06-04` als ISO; andere Formate (`06/04/2025`) werden NaT. Beides ist eine Entscheidung je Quelle; die Stichprobe (Prüfschritt 2) findet es.

**`sqlite3.OperationalError: no such table: rechnung` in pytest** · Die Pipeline ist vorher gescheitert. `python src/run.py` allein laufen lassen und den ersten Fehler lesen.

**pytest meldet den zweiten Lauf als verschieden** · Etwas in der Pipeline ist nicht deterministisch: heutiges Datum in den Daten, unsortierte Dateilisten, Zufall ohne Seed, ein Modellaufruf in der Pipeline. Den Modellaufruf aus der Pipeline nehmen oder seine Ausgabe cachen.

## promptfoo

**`No configuration file found at promptfooconfig.yaml`** · promptfoo sucht die Konfiguration im aktuellen Ordner. Aus dem Repo-Root mit `-c evals/promptfooconfig.yaml` aufrufen.

**`No files found for variable tabelle at path ../data/processed/...`** · Die Pipeline ist noch nicht gelaufen; die Suite liest ihre Eingabe aus `data/processed/`. Erst `python src/run.py`.

**`pdfplumber` liefert leeren Text** · Das PDF ist ein Scan ohne Textebene (so wie `data/sample/belege/reparaturen/`). Dann OCR (`pytesseract` mit Tesseract) oder ein Vision-Modell; das ist der Prompt-Anteil, Schritt 5.

**`--providers echo`: alle Tests rot** · Erwartet. Echo antwortet mit dem Prompt, nicht mit einer Zahl. Rot ist richtig, `errors` wären falsch.

**`Transform failed ... is not valid JSON` (Suite 2)** · Das Modell hat kein JSON geliefert; seit der aktuellen Vorlage fängt die Transformation das ab und die Assertions scheitern sauber. Bleibt der Fehler, ist die YAML verändert worden.

**Python-Grader: `python: command not found` oder `spawn python ENOENT`** · promptfoo ruft `python` auf. Das venv aktivieren oder `PROMPTFOO_PYTHON=python3` in `.env` eintragen.

**`429 Too Many Requests` oder `Rate limit exceeded` bei OpenRouter** · Free-Tier: 20 Anfragen pro Minute, 50 pro Tag. Ein Judge-Test braucht zwei Anfragen. Läufe auf zwei Tage verteilen oder das zweite Modell lokal (LM Studio, Beispiel in `evals/promptfooconfig.yaml`).

**`No endpoints found` oder `model not found` bei OpenRouter** · Die `:free`-Modelle rotieren. Unter https://openrouter.ai/models nach `:free` filtern, den Namen in der YAML ersetzen, Datum ins Entscheidungslog. Fallback: `openrouter/free`.

**Antwort leer, Judge sagt „Der Text ist leer", oder `[]` als Ausgabe** · Ein Reasoning-Modell (Qwen 3, Gemma 4, gpt-oss) hat das Token-Budget im Denken verbraucht. `OPENAI_MAX_TOKENS=4096` setzen (oder `max_tokens` in der Provider-Config).

**Grader findet eine falsche Zahl, etwa `123` aus `G123AB`** · Die Ausgabe beginnt mit `Thinking: …`; der Grader hat den Denktext gelesen. Die Grader im Template nehmen den letzten Absatz. Eigene Grader: dasselbe tun, oder das Modell ohne Reasoning betreiben.

**`Model loading was stopped` / HTTP 500 von LM Studio** · promptfoo hat ein Modell angefragt, das LM Studio erst laden müsste, und das Laden ist gescheitert (RAM). Das bereits geladene Modell verwenden (`curl localhost:1234/api/v0/models` zeigt `loaded`).

**LM Studio antwortet nicht** · In LM Studio den lokalen Server starten (Developer → Start Server) und ein Modell laden. Der Name in der YAML muss dem in LM Studio angezeigten entsprechen. Standardadresse `http://localhost:1234/v1`.

## Git

**`git push` abgelehnt: Datei über 100 MB, oder tausende Dateien unter `.venv/`** · `.venv/` ist in `.gitignore`; wurde es trotzdem committet: `git rm -r --cached .venv`, committen, pushen. Bei Rohdaten mit Personenbezug: dasselbe und den Lektor informieren; die Datei bleibt in der Historie, bis das Repo bereinigt ist.

**`.env` ist auf GitHub** · `git rm --cached .env`, committen, pushen, und den Schlüssel beim Anbieter sofort erneuern. Ein einmal gepushter Schlüssel gilt als verbrannt.

**Tag existiert lokal, nicht auf GitHub** · `git push --tags`. Prüfen unter *Tags* im Repo.

## Windows

`source .venv/bin/activate` heißt `.venv\Scripts\activate`; `cp` heißt `copy`; `python` heißt manchmal `py`. Pfade mit Umlauten im Benutzernamen: die Pipeline schreibt mit `encoding="utf-8"`, eigene Skripte sollten das auch tun. Bei „Ausführung von Skripts ist deaktiviert" in PowerShell: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
