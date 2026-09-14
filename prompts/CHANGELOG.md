# Prompt-Änderungen

Je Prompt eine Zeile pro Version: was geändert wurde, warum, und was die Suite davor und danach gemessen hat.

| Prompt | Version | Änderung | Grund | Suite vorher → nachher |
|---|---|---|---|---|
| extraktion | v1 | Erstfassung | | |
| extraktion_scan | v1 | Erstfassung als Chat-Nachricht mit Bild (JSON), fünf Felder | Scans haben keine Textebene | 6/12 (qwen/qwen3.8-27b lokal, 14.9.2026) |
| extraktion_scan | v2 | datum = Liefer-/Leistungsdatum, nicht Annahmedatum; rechnungsnr ohne angehängtes Datum; brutto = Rechnungsendbetrag | vier von sechs Fehlern der v1 waren Prompt-Fehler: falsches Datum gewählt, Datum an die Nummer gehängt | 6/12 → 10/12; übrig: eine falsch gelesene Ziffer im Nadeldruck (RR_11), ein Kennzeichen (RR_07) |
| kennzahl | v1 | Erstfassung | | |
| empfehlung | v1 | Erstfassung | | |
