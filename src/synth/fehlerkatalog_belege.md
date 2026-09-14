# Fehlerkatalog · Belege (Tank, Laden, Reparaturen)

Erzeugt von `src/synth/generate_belege.py --seed 42`. Tankkarten: 27 Seiten, 245 Positionen, Gesamt 5.850,33 EUR. Ladekarten: 6 Seiten, 41 Positionen, Netto 1.816,44 EUR. Reparaturen: 12 Belege.
Die Referenzen in `evals/references/` sind beim Erzeugen entstanden; sie sind die Wahrheit, gegen die eine Extraktion geprüft wird.

- Tankkarten, Seite 9, WU 93342D: Betrag 68,26 passt nicht zu Liter × Preis (43,22 × 1,51 = 65,26). Die Referenz führt den Belegwert; die Plausibilitätsprüfung muss ihn finden.
- Tankkarten, Seite 13, W 95412F: Kilometerstand 9490 liegt unter dem Stand in den Stammdaten und unter den anderen Tankungen des Monats (Tippfehler an der Zapfsäule).
- Tankkarten, Seite 17: Kennzeichen als `KL-25881B` geschrieben, in den Stammdaten als `KL 25881B`.
- Tankkarten: Summe je Fahrzeug über alle 25 Seiten muss den Gesamtbetrag 5.850,33 EUR auf Seite 1 ergeben; das ist der Abgleich zweier Stellen desselben Belegs.
- Ladekarten, Kartennr. 175339: kein Kennzeichen hinter dem Namen; die Karte ist keinem Fahrzeug zuordenbar (in den Stammdaten: W 764FP, nur über den Fahrernamen zu finden).
- Ladekarten, Kartennr. 167759: Kennzeichen mit Leerzeichen `I 36683J`, sonst überall mit Bindestrich.
- Ladekarten, Kartennr. 143972: Zwischensumme um 0,01 EUR höher als die Summe der Positionen (Rundung beim Anbieter). Die Referenz führt die Positionen.
- Ladekarten: Der Übertrag am Seitenende muss dem Übertrag am nächsten Seitenanfang gleichen; die Summe aller Zwischensummen je Karte ist der Nettobetrag 1.816,44 EUR. Positionen laufen über Seitenenden: Zwischen einer Positionszeile und der Zeile mit dem Ladenetz können Übertrag, Fußzeile und Seitenkopf stehen.
- Reparaturen RR_03: Rechnungsendbetrag 1.617,81 ist um 0,10 EUR höher als Netto + MwSt. Die Referenz führt den Belegwert.
- Reparaturen RR_12: Duplikat von RR_05 (dieselbe Rechnungsnummer, derselbe Betrag), als 'RECHNUNG - DUPLIKAT' gekennzeichnet. Zählt einmal.
- Reparaturen RR_06: kein Kilometerstand auf der Rechnung.
- Reparaturen RR_09: Kennzeichen W 99999X kommt in den Stammdaten nicht vor (Ersatzfahrzeug); die Zuordnung zum Fahrzeug fehlt.
- Reparaturen: Fahrername und Privatadresse stehen auf mehreren Rechnungen (Adressat, Zessionserklärung). Vor einer Extraktion mit einem Cloud-Modell sind sie zu maskieren oder die Rechnungen laufen lokal.
