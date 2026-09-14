# Schritt 4 · Abfragen und Referenzantworten

| Analyse | Werkzeug | Referenzantwort | Herkunft der Referenz | Prüfregel | Toleranz |
|---|---|---|---|---|---|
| 1 Mehrkilometer-Prognose je Vertrag | SQL, `kennzahl_mehrkilometer.sql` | Prognose für drei Fahrzeuge | von Hand aus Stichtagen und Vertrag gerechnet (Excel, 14.9.) | numerisch | ± 2 % |
| 2 Tank- und Ladekosten je Fahrzeug | SQL, `kennzahl_tankkosten.sql`, `kennzahl_ladekosten.sql` | Summe je Fahrzeug 5.850,33 EUR gesamt; Netto 1.816,44 EUR | die Summenseiten der Belege selbst | numerisch | auf den Cent |
| 3 Felder aus Reparaturrechnungen | Prompt, `prompts/extraktion_v1.md` | 12 Belege: Rechnungsnr, Datum, Kennzeichen, Netto, Brutto | `evals/references/reparaturrechnungen.json`, beim Erzeugen mitgeschrieben | exakt, Feldvergleich (`graders/feldvergleich.py`) | Beträge ± 0,005 |

Unsicher: RR_03 hat einen Endbetrag, der um 0,10 EUR von Netto + MwSt abweicht; die Referenz führt den Belegwert, die Plausibilitätsprüfung muss es finden. RR_12 ist ein Duplikat von RR_05 und zählt einmal.

*Bis hier: Deliverable 2, Tag `termin3`.*
