# Betriebshandbuch · <Projekt>

*Eine halbe Seite. Entwurf mit Deliverable 2, final mit Deliverable 3.*

### Starten
Voraussetzungen: Python- und Node-Version, `requirements.txt`, Umgebungsvariablen aus `.env.example`. Die Befehle in ihrer Reihenfolge: Pipeline, Suite, Vorlage erzeugen. Erwartete Laufzeit. Wer ein Dockerfile mitliefert: der eine Befehl, der baut und startet.

### Neue Daten kommen, oder das Format ändert sich
Wohin neue Daten kommen (`data/raw/<datum>/`), was auszuführen ist, worauf zu achten ist (Korrekturen an bestehenden Daten, Referenzen, die dadurch ungültig werden), was man im Ergebnis vergleicht. Und: Woran erkennt man, dass sich Format oder Schema der Quelle geändert haben, und welche Stelle der Pipeline betrifft das?

### Kosten pro Lauf
Zeit, Anfragen, Tokens, Euro, jeweils pro Modell. Das Anfragebudget im Free-Tier.

### Bekannte Schwächen
Was die Pipeline nicht kann (gescannte Layouts, fehlende Monate) und was die Suite nicht sieht (die Blindstellen aus der Projektdoku, Schritt 5).

### Wann es bricht
Schema-Änderungen an den Quellen, ein Modellwechsel beim Anbieter, das Budgetlimit, fehlende Umgebungsvariablen. Und woran man es jeweils erkennt.

### Wartung
Die Suite läuft einmal im Monat; bei Rot wird nachgesehen. Wer macht das, wann, was kostet es.

### Aufbewahrung und Löschung
Rohdaten, Zwischenstände, Prompts mit Daten, Modellaufrufe beim Anbieter: wie lange, wer löscht, wie.

---
