-- Mehrkilometer-Prognose je aktivem Fahrzeug mit Vertrag: Kilometer bis Vertragsende hochrechnen und mit der
-- vertraglichen Laufleistung plus Freikilometer vergleichen. Fahrzeuge ohne Kilometerstand werden ausgewiesen, nicht ausgelassen.
-- Die Spalte hinweis zuerst lesen: 'zu kurze Laufzeit' heißt, die Hochrechnung stützt sich auf unter 90 Tage und ist nicht belastbar.
WITH letzter AS (
  SELECT k.objektnr, k.stichtag, k.km
  FROM kilometerstand k
  JOIN (SELECT objektnr, MAX(stichtag) AS stichtag FROM kilometerstand GROUP BY objektnr) m
    ON m.objektnr = k.objektnr AND m.stichtag = k.stichtag
)
SELECT f.objektnr, f.kennzeichen, f.marke, f.modell, f.vertragsende, f.laufleistung_km, f.freikilometer,
       l.stichtag                                   AS letzter_stichtag,
       l.km                                         AS letzter_km,
       ROUND(julianday(l.stichtag) - julianday(f.vertragsbeginn))                       AS tage_gelaufen,
       ROUND(julianday(f.vertragsende) - julianday(f.vertragsbeginn))                   AS tage_gesamt,
       ROUND(l.km / (julianday(l.stichtag) - julianday(f.vertragsbeginn)) * 30.4)       AS km_je_monat,
       ROUND(l.km / (julianday(l.stichtag) - julianday(f.vertragsbeginn))
             * (julianday(f.vertragsende) - julianday(f.vertragsbeginn)))               AS prognose_km_vertragsende,
       ROUND(l.km / (julianday(l.stichtag) - julianday(f.vertragsbeginn))
             * (julianday(f.vertragsende) - julianday(f.vertragsbeginn))
             - f.laufleistung_km - COALESCE(f.freikilometer, 0))                        AS mehrkilometer_prognose,
       CASE WHEN l.km IS NULL THEN 'kein Kilometerstand'
            WHEN julianday(l.stichtag) - julianday(f.vertragsbeginn) < 90 THEN 'zu kurze Laufzeit'
            ELSE 'ok' END                                                                AS hinweis
FROM fahrzeug f
LEFT JOIN letzter l ON l.objektnr = f.objektnr
WHERE f.status = 'aktiv' AND f.laufleistung_km IS NOT NULL AND f.vertragsende IS NOT NULL
ORDER BY CASE hinweis WHEN 'ok' THEN 0 ELSE 1 END, mehrkilometer_prognose DESC;   -- erst die belastbaren Zeilen, dann die mit Hinweis
