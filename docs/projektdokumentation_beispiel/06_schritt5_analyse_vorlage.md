# Schritt 5 · Analyse und Entscheidungsvorlage

Suite `evals/extraktion_scans.yaml` gegen die zwölf Scans (PNG aus `src/scans_rendern.py`), Modell `qwen/qwen3.8-27b` lokal in LM Studio, 14.9.2026, 0 EUR, zwölf Anfragen, 3 min 34 s:

| Task | Modell | Trefferquote | Kosten | Zeit |
|---|---|---|---|---|
| Felder aus Scans, Prompt v1 | qwen/qwen3.8-27b, lokal | 6 / 12 | 0 EUR | 6 min 3 s |
| Felder aus Scans, Prompt v2 | qwen/qwen3.8-27b, lokal | 10 / 12 | 0 EUR | 3 min 34 s |
| Kennzahl, Extraktion aus Text, Judge (Template-Suiten) | qwen/qwen3.8-27b, lokal | 2/2, 2/2, 1/1 | 0 EUR | 23 s, 31 s, 3 min 43 s |

Modellwahl: lokal, weil Fahrernamen und Privatadressen auf den Belegen stehen; Fallback: maskierte Belege an ein Cloud-Modell. Was in v1 scheiterte: viermal das Annahmedatum statt des Liefer-/Leistungsdatums (Prompt sagte nicht, welches Datum), einmal das Datum an die Rechnungsnummer gehängt (so steht es auf dem Beleg), einmal eine Ziffer im Nadeldruck falsch gelesen. Vier der sechs waren Prompt-Fehler; v2 benennt das Datum und die Nummer, siehe `prompts/CHANGELOG.md`. Was in v2 bleibt: RR_11 Brutto 1850,10 statt 1858,10, eine Ziffer im Scan; Netto + MwSt gegen den Endbetrag hätte es entlarvt. RR_07 Kennzeichen als `null` zurückgegeben, obwohl es auf dem Beleg steht (S 41937C); ein zweiter Lauf oder ein zweites Modell würde zeigen, ob das reproduzierbar ist. Was die Suite nie sieht: ob das extrahierte Kennzeichen zu einem Fahrzeug in den Stammdaten gehört (RR_09 besteht), und ob eine Rechnung doppelt ist (RR_12 besteht). Zahlen in der Vorlage:

| Zahl in der Vorlage | Abfrage oder Eval | Tabelle / Datei |
|---|---|---|
| 23 von 64 Verträgen laufen auf mehr als 10 % Mehrkilometer zu | `kennzahl_mehrkilometer.sql`, Filter `mehrkilometer_prognose > 0.1 * laufleistung_km` | `data/processed/kennzahl_mehrkilometer.csv` |
| 7 Verträge zu jung für eine Prognose | dieselbe Abfrage, Spalte `hinweis` | dieselbe Datei |
| Tankkosten März 2025: 5.850,33 EUR für 25 Fahrzeuge | `kennzahl_tankkosten.sql`, Summe | `data/processed/kennzahl_tankkosten.csv`, Seite 1 des Belegs |
| Ladekosten Jänner 2025: 1.816,43 EUR, 0,61 EUR je kWh im Median | `kennzahl_ladekosten.sql` | `data/processed/kennzahl_ladekosten.csv` |
