# Fehlerkatalog · flotte_stammdaten.csv

Erzeugt von `src/synth/generate.py` mit `--n 250 --seed 42`; 253 Zeilen, 43 Spalten. Diese Fehler stecken absichtlich drin. Sie sind die Referenz für den Qualitätsbericht (Schritt 2): Wer sie findet, hat die Pipeline richtig gebaut; wer eine Abfrage darauf laufen lässt, ohne sie zu bereinigen, bekommt falsche Zahlen.

- Die Kennzeichen G 123AB, W 45678C und K 9012D (Objektnr. 383810, 314592, 303278) gehören zu den Rechnungen in `beispiel.csv`; dort stehen sie als G123AB, G-123AB, W-45678C, W 45678C, K-9012D. Kein Fehler, aber die Normalisierungsaufgabe.
- Duplikat: Objektnr. 332098 steht zweimal, einmal als `K 124XG`, einmal als `K-124XG`.
- Duplikat: Objektnr. 344597 steht zweimal, einmal als `BN 85562U`, einmal als `BN-85562U`.
- Duplikat: Objektnr. 336434 steht zweimal, einmal als `G 86297T`, einmal als `G-86297T`.
- Schreibvariante: Objektnr. 313434 mit Kennzeichen `WU758KG` statt `WU 758KG`.
- Schreibvariante: Objektnr. 303478 mit Kennzeichen `GU569TU` statt `GU 569TU`.
- Schreibvariante: Objektnr. 338427 mit Kennzeichen `W922SY` statt `W 922SY`.
- Schreibvariante: Objektnr. 389593 mit Kennzeichen `I48729X` statt `I 48729X`.
- Schreibvariante: Objektnr. 365435 mit Kennzeichen `W35213N` statt `W 35213N`.
- Kilometerstand rückläufig: Objektnr. 314592, Spalte `km-Stand per 30.06.2024` = 39 099 liegt unter dem Vorwert.
- Kilometerstand rückläufig: Objektnr. 303278, Spalte `km-Stand per 31.12.2023` = 77 797 liegt unter dem Vorwert.
- Kilometerstand rückläufig: Objektnr. 397196, Spalte `km-Stand per 31.12.2023` = 80 403 liegt unter dem Vorwert.
- Kilometerstand rückläufig: Objektnr. 336048, Spalte `km-Stand per 31.12.2022` = 51 994 liegt unter dem Vorwert.
- Kilometerstand rückläufig: Objektnr. 332098, Spalte `km-Stand per 30.06.2025` = 67 995 liegt unter dem Vorwert.
- Tippfehler: Objektnr. 377397, Spalte `km-Stand per 31.12.2021` = 1 281 760 (eine Null zu viel).
- Einheitenwechsel: Objektnr. 354987, Mehrkilometer = 6,99 (Cent statt Euro je km wie in den übrigen Zeilen).
- Einheitenwechsel: Objektnr. 358878, Mehrkilometer = 12,96 (Cent statt Euro je km wie in den übrigen Zeilen).
- Datumsformat: Objektnr. 344118, Erstzulassung = 44694 (Excel-Seriennummer statt TT.MM.JJJJ).
- Datumsformat: Objektnr. 313396, Erstzulassung = 45261 (Excel-Seriennummer statt TT.MM.JJJJ).
- Schreibweise: Objektnr. 345082, Leasinggeber `LeasePlan` statt `Leaseplan`.
- Mehrfachwert: Objektnr. 334671, drei Kennzeichen in einer Zelle (Kennzeichenwechsel).
- Excel-Fehlerwert: Objektnr. 305695, Leasingrate = `#BEZUG!`.
- Lücke: 16 von 92 aktiven Fahrzeugen ohne Kilometerstand zum 30.09.2025; für sie ist keine Hochrechnung möglich.

Dazu die Eigenheiten des Formats, die kein Fehler sind, aber gelöst werden müssen: zwei Kommentarzeilen vor der Kopfzeile, Semikolon, Latin-1, Zahlen mit Leerzeichen als Tausendertrenner und Dezimalkomma, leere Zellen für fehlende Werte, Datum als TT.MM.JJJJ, zehn Kilometerstände als Spalten statt Zeilen (der letzte Stichtag noch leer), Ja/Nein in mehreren Schreibweisen (`Ja`, `ja`, `X`, `x`, `nein`), `Fahrzeug Typ` nur zur Hälfte gefüllt (aus `Antrieb` ableitbar: D Diesel, B Benzin, E Elektro, H/B und H/D Hybrid), `Antrieb` als Kürzel, `Bemerkung` als Freitext mit Personennamen.
