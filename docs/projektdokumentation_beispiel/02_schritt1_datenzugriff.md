# Schritt 1 · Datenzugriff

| Quelle | Herkunft | Format | Abrufdatum | Freigabe | Zeilen | Was fehlt |
|---|---|---|---|---|---|---|
| Stammdaten | Export des Leasinggebers, synthetisch nachgebaut (`src/synth/generate.py`, Seed 42) | CSV, Semikolon, Latin-1, 2 Kommentarzeilen | Stand 30.09.2025 | Testdaten, frei | 253 | Kilometerstand 31.12.2025 leer; Laufleistung bei jedem vierten Vertrag leer |
| Tankkarten | Abrechnung des Leasinggebers, März 2025 | PDF mit Textebene, 27 Seiten | 24.04.2025 | Testdaten | 245 Positionen | nur ein Monat |
| Ladekarten | Rechnung des Ladenetzbetreibers, Jänner 2025 | PDF mit Textebene, 6 Seiten | 10.03.2025 | Testdaten | 173 Positionen | anderer Monat als die Tankkarten |
| Reparaturen | zwölf Werkstattrechnungen | PDF-Scans ohne Text, drei Layouts | 2024-10 bis 2025-06 | Testdaten | 12 Belege | Schadensart nicht strukturiert |

Verworfen: Reifenkosten (kein Export verfügbar). Personenbezug: Fahrername und Bemerkung in den Stammdaten, Fahrername und Privatadresse auf Reparaturrechnungen, Fahrername hinter der Kartennummer auf der Ladekartenrechnung. Entfernt in Schritt 2 (`clean.py`), die Rechnungs-Scans laufen nur lokal oder maskiert (Schritt 5). Synthetisch: regelbasiert, kalibriert an einem echten Export (`src/synth/params.json`); nicht abgebildet sind Zusammenhänge zwischen Preis und Marke.
