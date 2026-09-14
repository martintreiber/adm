# Schritt 3 · Zusammenführen und ablegen

| Tabelle | Primärschlüssel | Fremdschlüssel | aus Quelle | Zeilen |
|---|---|---|---|---|
| fahrzeug | objektnr | – | Stammdaten | 250 |
| kilometerstand | objektnr, stichtag | objektnr → fahrzeug | Stammdaten (zehn Spalten → Zeilen) | 1035 |
| tankung | tankung_id | objektnr → fahrzeug | Tankkarten-PDF | 245 |
| ladung | ladung_id | objektnr → fahrzeug (über ladekarte_nr) | Ladekarten-PDF | 41 |
| rechnung | rechnungsnr | kennzeichen → fahrzeug.kennzeichen (kein FK, Index) | beispiel.csv | 21 |

Beziehungen: fahrzeug 1:n kilometerstand, 1:n tankung, 1:n ladung, 1:n rechnung. Zuordnungslücken: 0 Tankpositionen, 0 Ladezeilen, 0 Rechnungen ohne Fahrzeug; eine Reparaturrechnung (RR_09) nennt ein Kennzeichen, das in den Stammdaten fehlt (Ersatzfahrzeug), sie ist noch nicht integriert. Modellierungsentscheidung: Objektnummer als Schlüssel, weil das Kennzeichen wechselt und in drei Schreibweisen vorkommt; die Ladekartennummer aus den Stammdaten verknüpft die Ladekartenrechnung, das Kennzeichen ist der zweite Weg.
