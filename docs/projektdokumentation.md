# Projektdokumentation · Abgabeliste

Die Projektdokumentation ist ein Ordner, `docs/projektdokumentation/`, eine Datei je Abschnitt. Die acht Dateien liegen dort als Gerüst (Überschriften, leere Tabellen, Platzhalter) und werden von euch gefüllt. Wie sie ausgefüllt aussehen, zeigt `docs/projektdokumentation_beispiel/` für die Testdaten im Repo, Datei für Datei mit denselben Namen; dort steht nur Inhalt, keine Anleitung. Diese Seite ist die Anleitung: was in jede Datei gehört, wann sie abgegeben wird, und woran ihr erkennt, dass sie fertig ist. Zusammen vier bis sechs Seiten; was im Repo liegt, wird verlinkt, nicht kopiert.

Grundsatz: Entscheidungen, die ihr nicht getroffen habt, hat der Agent getroffen. Das Entscheidungslog macht sichtbar, welche eure waren.

## Die Dateien der Projektdokumentation

Gerüst: `docs/projektdokumentation/<datei>` · Beispiel: `docs/projektdokumentation_beispiel/<datei>`

| Datei | Inhalt | Abgabe | Fertig wenn |
|---|---|---|---|
| `docs/projektdokumentation/00_auftrag.md` | Adressat (Rolle), Entscheidung, drei Analysen mit Werkzeug (SQL, Prompt, beides), was nicht drin ist, Änderungen seit dem Pitch mit Datum | 26.9. (Pitch), dann laufend | Der Drei-Sätze-Test klappt: Wer entscheidet was, mit welchen Daten, woran erkennen wir, dass das LLM recht hat |
| `docs/projektdokumentation/01_entscheidungslog.md` | Eine Zeile je Entscheidung: Datum, Entscheidung, Alternative, Warum, Folge (Datei, Commit). Pflicht: Programm oder Prompt je Aufgabe, jeder Datenausschluss, PII-Grenze, Modellwahl, Scope-Änderungen | laufend, ab dem ersten Commit | Jede Zeile hat eine Alternative; die Zeilen passen zur Commit-Historie |
| `docs/projektdokumentation/02_schritt1_datenzugriff.md` | Quellentabelle (Herkunft, Format, Abrufdatum, Freigabe, Zeilen, was fehlt), verworfene Kandidaten, Personenbezug, bei synthetischen Daten Weg, Seed, Kalibrierung | `termin3` | Zu jeder Datei in `data/raw/<datum>/` steht, woher sie kommt und was drin ist |
| `docs/projektdokumentation/03_schritt2_normalisieren.md` | Zahlen aus dem Pipeline-Lauf je Quelle (gelesen, geändert, Duplikate, fehlend, PII-Spalten), Qualitätsbericht mit sechs Fragen und Konsequenz, PII-Entscheidung mit Stelle im Code | `termin3` | Jede Zahl stammt aus der Ausgabe von `python src/run.py`; jeder Befund hat eine Konsequenz |
| `docs/projektdokumentation/04_schritt3_datenmodell.md` | Tabellen mit Primär- und Fremdschlüsseln, Herkunft, Zeilenzahl; Beziehungen; Zuordnungslücken mit Zahl; Modellierungsentscheidungen; Startbefehl und Prüfung | `termin3` | Stimmt mit `src/sql/schema.sql` und der SQLite überein; `pytest` grün |
| `docs/projektdokumentation/05_schritt4_abfragen_referenzen.md` | Je Analyse: Werkzeug, Referenzantwort, Herkunft der Referenz (wer, wann, wie), Prüfregel, Toleranz; wo „richtig" unsicher ist | `termin3` | Für jede Analyse steht, woran erkannt wird, ob das Modell recht hat, und kein Modell ist dafür gelaufen; Referenzen in `evals/references/` |
| `docs/projektdokumentation/06_schritt5_analyse_vorlage.md` | Eval-Suite (Modell mit Datum, Trefferquote, Kosten, Zeit, Anfragen), Modellwahl mit Fallback, was scheitert, was die Suite nie sieht, Herkunft jeder Zahl der Vorlage, Übergabe mit Selbsttest, LLM-Workflow mit je zwei Fällen | `termin4` | Jede Zahl in `docs/vorlage.md` steht in der Herkunftstabelle mit Abfrage oder Eval und Datei |
| `docs/projektdokumentation/07_offene_punkte_lessons.md` | Datenlücken und Annahmen, Risiken nach Konsequenz, drei Lessons je ein Satz, was beim nächsten Mal anders wäre | `termin4` | Die Lücken sind konkret (welche Fahrzeuge, welche Monate), nicht allgemein |

## Alles, was abgegeben wird, je Deliverable

Die Abgabe ist der Stand des Repos beim Tag. Was hier nicht steht, wird nicht bewertet.

**Deliverable 1 · Pitch (Gallery Walk Sa 26.9.; alles Folgende bis dahin, früher ablegen geht, muss aber nicht)**

| Was | Wo | Erwarteter Inhalt |
|---|---|---|
| Poster | `docs/pitch/<name>.pdf` | One-Pager A3 oder A2: Datenquelle mit Provenienz, drei Analysen, Zielpublikum und Entscheidung, Zweck, LLM-Arbeit. Beispiel für die Testdaten: `docs/pitch/Poster.html` (A4; im Browser öffnen und als PDF drucken); löschen, wenn euer eigenes da ist |
| Auftrag | `docs/projektdokumentation/00_auftrag.md` | siehe oben |
| Rohdaten | `data/raw/<datum>/` (lokal, nie im Repo) | liegen vor; im Repo steht nur, was dort liegt (`02_schritt1_datenzugriff.md`). Wer bis zum 26.9. keine hat, wechselt die Quelle und sagt es beim Pitch |

**Deliverable 2 · Datenpipeline (Tag `termin3`, Fr 9.10., 23:59)**

| Was | Wo | Erwarteter Inhalt |
|---|---|---|
| Pipeline | `src/run.py`, `src/config.py`, `src/clean.py`, `src/integrate.py`, `src/derive.py` | `QUELLEN` mit euren Dateien; eine Funktion je Quelle in `clean.py`; läuft zweimal mit gleichem Ergebnis |
| Datenmodell | `src/sql/schema.sql` | eine Tabelle je Entität, Primär- und Fremdschlüssel, `NOT NULL` wo es gilt |
| Datenbank | `data/processed/<projekt>.sqlite` | von der Pipeline erzeugt, committet, ohne Personenspalten |
| Abfragen | `src/sql/kennzahl_<analyse>.sql` | eine Abfrage je numerische Analyse; Ergebnis als CSV in `data/processed/` |
| Referenzantworten | `evals/references/<analyse>.json` oder `.csv` | je Fall Eingabe, erwartete Antwort, Herkunft (wer, wann), Unsicherheit; mindestens acht Fälle für Extraktion oder Klassifikation |
| Test | `tests/test_pipeline.py` | grün; der Datenbankname steht in `src/config.py` (`PROJEKT`), der Test prüft alle Tabellen und den zweiten Lauf |
| Projektdokumentation | `00` bis `05` im Ordner oben | wie in der Tabelle |
| Betriebshandbuch, Entwurf | `docs/betrieb.md` | Starten, neue Daten, bekannte Schwächen; halbe Seite |

**Deliverable 3 · Evaluierung und Entscheidungsvorlage (Tag `termin4`, Fr 23.10., 23:59)**

| Was | Wo | Erwarteter Inhalt |
|---|---|---|
| Entscheidungsvorlage | `docs/vorlage.md` | 3 bis 5 Seiten für die benannte Rolle, Gliederung Handout 09; jede Zahl mit Herkunft |
| Prompts | `prompts/<analyse>_v<n>.md`, `prompts/CHANGELOG.md` | versioniert; je Version eine Zeile im Changelog mit Suite vorher → nachher |
| Eval-Suite | `evals/<suite>.yaml`, `evals/graders/` | alle Tasks als Tests gegen die Referenzen; Modell gepinnt mit Datum; Grader selbst geprüft |
| Ergebnisse | in `06_schritt5_analyse_vorlage.md` (die JSON in `evals/results/` bleibt lokal) | Trefferquote je Task, Modell, Kosten, Zeit, Anfragen |
| Projektdokumentation | `06` und `07` im Ordner oben, `00` bis `05` aktuell | wie in der Tabelle |
| Betriebshandbuch, final | `docs/betrieb.md` | alle sieben Abschnitte, eine Seite |
| Agent-Anweisung | `CLAUDE.md` | ausgefüllt: Was das ist, wo was liegt, Datenmodell, Regeln, Starten |
| Abhängigkeiten | `requirements.txt`, `.env.example` | Versionen; jede Umgebungsvariable, die die Pipeline oder die Suite braucht |
| Selbsttest | in `06_schritt5_analyse_vorlage.md` | frischer Clone nach README: Datum, Dauer, was gehakt hat, was ergänzt wurde |

**Deliverable 4 · Endpräsentation (24.10.)**

| Was | Wo | Erwarteter Inhalt |
|---|---|---|
| Folie, optional | `docs/vortrag/<name>.pdf` | eine Folie: die zwei bis drei wichtigsten Lessons |
| Die Frage aus dem Repo | live | eine Zahl bis zur Rohdatei, oder eine Entscheidung mit Alternative; Vorbereitung mit `docs/interview_prompt.md` |
