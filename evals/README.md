# Evals · Ground Truth bauen und Suiten laufen lassen

Vier Beispiel-Suiten. Die ersten drei laufen auf `data/sample/beispiel.csv` und zeigen je eine Prüfregel; die vierte ist der Prompt-Anteil des Beispielprojekts (Schritt 5b): Scans ohne Textebene an ein Vision-Modell. Eure eigenen Suiten ersetzen Eingaben, Referenzen und Prompts.

| Suite | Prüfregel | Datei |
|---|---|---|
| Kennzahl | numerisch mit Toleranz, Grader in `graders/zahl.js`, geprüft durch `tests/test_grader.py` | `promptfooconfig.yaml` |
| Extraktion | exakt, Feldvergleich (Tier 1 in YAML, Tier 2 in `graders/feldvergleich.py`) | `extraktion.yaml` |
| Judge | Kriterienliste, zweites Modell prüft | `judge.yaml` |
| Extraktion aus Scans | zwölf Reparaturrechnungen als Bild an ein Vision-Modell, Grader `graders/feldvergleich_scan.py` gegen `references/reparaturrechnungen.json` | `extraktion_scans.yaml` |

## Laufen lassen

Aus dem Repo-Root, nach `python src/run.py` (die Suiten lesen `data/processed/kennzahl_beispiel.csv`):

```bash
cp .env.example .env                                              # Schlüssel eintragen (Windows: copy)
npx promptfoo@latest eval -c evals/promptfooconfig.yaml           # Suite 1; Suite 2 und 3: extraktion.yaml, judge.yaml
npx promptfoo@latest view                                         # Ergebnisse im Browser
npx promptfoo@latest eval -c evals/promptfooconfig.yaml --output evals/results/2026-10-20_kennzahl.json   # Lauf protokollieren
```

Ohne Schlüssel läuft jede Suite mit `--providers echo`; das Modell antwortet dann mit dem Prompt selbst. Für Suite 3 zusätzlich `--grader echo`, sonst ruft der Judge das Modell aus der YAML. Alle Tests sind rot, aber ohne `errors`: Das testet die Konfiguration, nicht das Modell. Für den Python-Grader (Suite 2) braucht promptfoo den Befehl `python`; auf macOS/Linux das venv aktivieren oder `PROMPTFOO_PYTHON=python3` in `.env` setzen.

**Lokal mit LM Studio**, ohne die YAML zu ändern (Server gestartet, Modell geladen, Name wie in LM Studio angezeigt):

```bash
OPENAI_BASE_URL=http://localhost:1234/v1 OPENAI_API_KEY=lm-studio OPENAI_MAX_TOKENS=4096 \
  npx promptfoo@latest eval -c evals/promptfooconfig.yaml --providers openai:chat:qwen/qwen3-8b --grader openai:chat:qwen/qwen3-8b
```

**Scans an ein Vision-Modell (Suite 4).** Erst die PNGs erzeugen, dann die Suite mit einem Modell, das Bilder versteht (in LM Studio als „vlm" gekennzeichnet, etwa Qwen3-VL oder Gemma 4):

```bash
python src/scans_rendern.py                                   # data/interim/scans/RR_01.png … RR_12.png, erste Seite je Beleg
OPENAI_BASE_URL=http://localhost:1234/v1 OPENAI_API_KEY=lm-studio OPENAI_MAX_TOKENS=4096 \
  npx promptfoo@latest eval -c evals/extraktion_scans.yaml --providers openai:chat:<vision-modell>
```

Der Prompt ist keine Textdatei, sondern eine JSON-Chat-Nachricht mit Text und Bild (`prompts/extraktion_scan_v1.json`); promptfoo liest die PNG aus der Variable `bild` und setzt sie als Data-URL ein, im Prompt steht nur `{{bild}}`; wer `data:image/png;base64,` selbst davorschreibt, bekommt „Invalid image". Die Scans enthalten Fahrernamen und Privatadressen, deshalb lokal. Ein Lauf sind zwölf Anfragen. Stand 14.9.2026 mit `qwen/qwen3.8-27b` lokal: Prompt v1 6/12, Prompt v2 10/12 in 3 min 34 s; die zwei Reste sind eine falsch gelesene Ziffer im Nadeldruck-Scan und ein Kennzeichen. Was sich zwischen v1 und v2 geändert hat, steht in `prompts/CHANGELOG.md`.

`--grader` setzt das Modell für den Judge (Suite 3). `OPENAI_MAX_TOKENS` braucht ein Reasoning-Modell: Es denkt zuerst, und wenn das Budget (Standard 1024) im Denken aufgeht, ist die Antwort leer. promptfoo stellt den Denktext als `Thinking: …` vor die Antwort; die Grader im Template werten deshalb nur den letzten Absatz aus (`graders/zahl.js`) beziehungsweise das letzte JSON-Objekt (`extraktion.yaml`). Stand 14.9.2026 laufen alle drei Suiten mit `qwen/qwen3.8-27b` lokal durch: Suite 1 2/2, Suite 2 2/2, Suite 3 1/1.

Das Modell steht oben in jeder YAML unter `providers`. Version pinnen (kein `:latest`, kein `:free` ohne Datum im Log) und im Entscheidungslog festhalten, welches Modell warum. Ein zweites Modell ist eine zweite Zeile unter `providers`.

## Referenzen zu den Beispielbelegen

`references/tankungen_2025-03.csv`, `references/ladungen_2025-01.csv` und `references/reparaturrechnungen.json` sind beim Erzeugen der PDFs in `data/sample/belege/` mitgeschrieben worden (Handout 12, LLM-Weg: wer die Rechnung erzeugt, kennt den Betrag). Sie zeigen die Form einer Referenzdatei mit Herkunft und Unsicherheit und taugen als Testfälle für eine eigene Extraktions-Suite; die absichtlichen Widersprüche stehen in `src/synth/fehlerkatalog_belege.md`.

## Referenzantworten bauen (Deliverable 2)

Die Referenz ist die Antwort, die ihr für richtig haltet, bevor das Modell antwortet. Sie entsteht unabhängig vom Modell: händisch erfasst, aus SQL berechnet oder von einer Person beurteilt.

1. **Wie viele Fälle:** Extraktion und Klassifikation mindestens acht, zwölf sind besser. Numerische Kennzahlen: jede Kennzahl eine Referenz, aus SQL oder von Hand nachgerechnet. Judge: drei bis fünf Kriterien je Text.
2. **Wie erfassen:** eine JSON-Datei je Suite in `references/`, je Fall Eingabe, erwartete Antwort und Herkunft (`"quelle": "händisch, Rechnung 7, 14.9."`). Wer die Referenz erfasst hat, steht dabei; bei Zweifeln zwei Personen.
3. **Wie verglichen wird:** je Analyse in der Projektdokumentation, Schritt 4: exakt, numerisch mit welcher Toleranz, oder gegen welche Kriterien.
4. **Unsicherheit dokumentieren:** Wo „richtig" selbst strittig ist (eine unleserliche Rechnung, ein Grenzfall bei der Klassifikation), steht das in der Referenzdatei und in der Projektdokumentation, Schritt 4. Eine unsichere Referenz ist erlaubt, eine verschwiegene nicht.
5. **Referenzen altern:** Datum und Datenstand in die Datei. Ändert sich die Quelle, wird die Referenz geprüft, nicht das Ergebnis angepasst.

## Was ihr protokolliert (Projektdoku, Schritt 5)

Je Lauf: Modell und Version, Trefferquote je Suite, Kosten, Laufzeit, Anzahl Anfragen. Mit `--output evals/results/<datum>_<suite>.json` liegt der Lauf als Datei vor; `results/` ist gitignored, die Zahlen kommen in die Projektdokumentation, Schritt 5.
