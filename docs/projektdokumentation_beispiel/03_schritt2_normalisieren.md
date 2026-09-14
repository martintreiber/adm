# Schritt 2 · Auslesen und normalisieren

| Quelle | Zeilen gelesen | Werte geändert | Duplikate entfernt | fehlende Werte | Spalten entfernt (PII) |
|---|---|---|---|---|---|
| Stammdaten | 253 | 2 Mehrkilometer Cent→Euro, 1 Zelle mit drei Kennzeichen (erstes genommen), 2 Excel-Datumszahlen | 3 (gleiche Objektnummer) | 1 Fehlerwert `#BEZUG!` in Leasingrate, 25 von 92 aktiven ohne Stand 30.09.2025 | Fahrer, Bemerkung |
| Tankkarten | 245 Positionen, 25 Fahrzeuge | Rabatte `0,76-` als negative Beträge | 0 | 1 Betrag ≠ Liter × Preis | keine (Fahrer steht nicht in der bereinigten Tabelle) |
| Ladekarten | 173 Positionen → 41 Zeilen | fünf Positionszeilen je Netz zu einer | 0 | 2 Zeilen ohne Kennzeichen (eine Karte) | Name hinter der Kartennummer nicht übernommen |

| Frage | Befund | Konsequenz |
|---|---|---|
| Vollständig? | Kilometerstand 30.09.2025 fehlt bei 25 von 92 aktiven Fahrzeugen; Laufleistung fehlt bei jedem vierten Vertrag | für diese keine Prognose; sie stehen mit Hinweis in der Liste, nicht stillschweigend draußen |
| Korrekt? | 5 rückläufige Kilometerstände, 1 Stand mit einer Null zu viel; Tankbeleg: 1 Betrag ≠ Liter × Preis; Ladebeleg: zwei Positionen standen am Seitenende, das Ladenetz erst nach Übertrag und Seitenkopf, der erste Parser ordnete sie dem Übertrag zu (43 statt 41 Zeilen) | bleiben drin und sind markiert; deshalb Stichprobe von drei Fahrzeugen gegen die Belege; den Parser-Fehler fand der Abgleich mit der Referenzdatei |
| Konsistent? | Kennzeichen in drei Schreibweisen über alle Quellen; Mehrkilometer in Cent und Euro; `Ja/ja/X` | `normalize_id`, Division durch 100, Mapping auf ja/nein; alles in `clean.py` |
| Aktuell? | Stammdaten Stand 30.09.2025, Tankbeleg März, Ladebeleg Jänner | Kosten je Fahrzeug sind Monatswerte verschiedener Monate; keine Jahressumme daraus |
| Wem gehört sie? | Leasinggeber und Ladenetzbetreiber liefern, der Kunde entscheidet | Belege bleiben lokal, nur Aggregate in die Vorlage |
| Woher kommt sie? | synthetisch, Generator und Seed im Repo | Provenienz vollständig; bei echten Daten: Exportdatum und Filter je Quelle |

PII: `Fahrer (Nach- und Vorname)` und `Bemerkung` (`config.PII_COLUMNS`, entfernt in `clean.drop_pii`, aufgerufen in jeder Quellfunktion). Der Fahrername auf der Ladekartenrechnung wird beim Lesen nicht übernommen (`clean.ladekarten`, regulärer Ausdruck ohne Namensgruppe). Die Reparaturrechnungen mit Privatadressen laufen deshalb nur durch ein lokales Modell oder werden vorher maskiert.
