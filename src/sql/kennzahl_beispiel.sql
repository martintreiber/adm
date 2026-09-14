-- Beispielkennzahl: Nettosumme und Anzahl Rechnungen je Fahrzeug.
-- Zeilen ohne Betrag werden gezählt, aber nicht summiert.
SELECT kennzeichen,
       COUNT(*)                                   AS anzahl_rechnungen,
       SUM(CASE WHEN netto_eur IS NULL THEN 1 ELSE 0 END) AS ohne_betrag,
       ROUND(SUM(netto_eur), 2)                   AS netto_summe_eur
FROM rechnung
GROUP BY kennzeichen
ORDER BY netto_summe_eur DESC;
