-- Ladekosten je Karte und Fahrzeug im Abrechnungsmonat: kWh, Euro, Preis je kWh, Anteil Schnellladen.
SELECT l.kartennr, l.objektnr, COALESCE(f.kennzeichen, l.kennzeichen) AS kennzeichen, f.marke, f.modell,
       COUNT(DISTINCT l.netz)                                                          AS netze,
       ROUND(SUM(l.ladevorgaenge))                                                     AS ladevorgaenge,
       ROUND(SUM(l.energie_kwh), 2)                                                    AS energie_kwh,
       ROUND(SUM(l.betrag_eur), 2)                                                     AS betrag_eur,
       ROUND(SUM(l.betrag_eur) / NULLIF(SUM(l.energie_kwh), 0), 3)                     AS eur_je_kwh,
       ROUND(100.0 * SUM(CASE WHEN l.leistungsklasse LIKE '%DC%' THEN l.energie_kwh END) / NULLIF(SUM(l.energie_kwh), 0)) AS anteil_dc_pct,
       CASE WHEN l.objektnr IS NULL THEN 'Karte nicht in Stammdaten' ELSE '' END       AS hinweis
FROM ladung l
LEFT JOIN fahrzeug f ON f.objektnr = l.objektnr
GROUP BY l.kartennr
ORDER BY betrag_eur DESC;
