-- Tankkosten je Fahrzeug im Abrechnungsmonat: Kraftstoff, Rabatte, Sonstiges, Liter, Kilometer laut Zapfsäule.
-- Positionen ohne zugeordnetes Fahrzeug erscheinen unter objektnr NULL, damit sie nicht verschwinden.
SELECT t.objektnr, t.kennzeichen, f.marke, f.antrieb,
       COUNT(CASE WHEN t.position = 'Kraftstoff' THEN 1 END)                           AS tankungen,
       ROUND(SUM(CASE WHEN t.position = 'Kraftstoff' THEN t.liter END), 2)             AS liter,
       ROUND(SUM(CASE WHEN t.position = 'Kraftstoff' THEN t.betrag_eur END), 2)        AS kraftstoff_eur,
       ROUND(SUM(CASE WHEN t.position LIKE 'Tankstellenrabatt%' THEN t.betrag_eur END), 2) AS rabatt_eur,
       ROUND(SUM(CASE WHEN t.position NOT IN ('Kraftstoff') AND t.position NOT LIKE 'Tankstellenrabatt%' THEN t.betrag_eur END), 2) AS sonstiges_eur,
       ROUND(SUM(t.betrag_eur), 2)                                                     AS summe_eur,
       MIN(CASE WHEN t.position = 'Kraftstoff' THEN t.km_stand END)                    AS km_min,
       MAX(CASE WHEN t.position = 'Kraftstoff' THEN t.km_stand END)                    AS km_max
FROM tankung t
LEFT JOIN fahrzeug f ON f.objektnr = t.objektnr
GROUP BY t.objektnr, t.kennzeichen
ORDER BY summe_eur DESC;
