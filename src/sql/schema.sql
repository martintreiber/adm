-- Datenmodell. Eine Tabelle je Entität, Schlüssel benannt, Beziehungen als Fremdschlüssel.
-- Wird bei jedem Lauf neu angelegt (integrate.py). Datum als ISO-Text (YYYY-MM-DD), Geld als REAL in EUR.

-- Quelle 1: Werkstattrechnungen (beispiel.csv). Schlüssel Rechnungsnummer; Fahrzeug über das normalisierte Kennzeichen.
CREATE TABLE rechnung (
  rechnungsnr TEXT PRIMARY KEY,
  datum       TEXT,
  lieferant   TEXT NOT NULL,
  kennzeichen TEXT NOT NULL,
  netto_eur   REAL,
  mwst_pct    REAL
);
CREATE INDEX idx_rechnung_kennzeichen ON rechnung (kennzeichen);

-- Quelle 2: Stammdaten. Ein Fahrzeug je Objektnummer. Das Kennzeichen ist normalisiert (G123AB), aber kein Schlüssel:
-- es kann wechseln, und die Belege schreiben es anders. Vertragsdaten liegen hier mit drin (1:1 zum Fahrzeug).
CREATE TABLE fahrzeug (
  objektnr            TEXT PRIMARY KEY,
  kennzeichen         TEXT NOT NULL,
  fahrgestellnr       TEXT,
  marke               TEXT NOT NULL,
  modell              TEXT,
  antrieb             TEXT,            -- Diesel, Benzin, Elektro, Hybrid
  kw                  REAL,
  co2_g_km            REAL,
  erstzulassung       TEXT,
  status              TEXT NOT NULL,   -- aktiv, inaktiv, in Bestellung
  abgemeldet_am       TEXT,
  leasinggeber        TEXT,
  vertragsbeginn      TEXT,
  vertragsende        TEXT,
  laufzeit_monate     REAL,
  laufleistung_km     REAL,            -- vertraglich vereinbarte Gesamtkilometer
  freikilometer       REAL,
  mehrkm_eur_km       REAL,
  leasingrate_eur     REAL,
  servicerate_eur     REAL,
  anschaffungswert_eur REAL,
  fahrerkategorie     TEXT,            -- die Person selbst ist entfernt (PII)
  kostenstelle        TEXT,
  standort            TEXT,
  ladekarte_nr        TEXT
);
CREATE INDEX idx_fahrzeug_kennzeichen ON fahrzeug (kennzeichen);

-- Kilometerstände: eine Zeile je Fahrzeug und Stichtag (in der Quelle: eine Spalte je Stichtag).
CREATE TABLE kilometerstand (
  objektnr  TEXT NOT NULL REFERENCES fahrzeug (objektnr),
  stichtag  TEXT NOT NULL,
  km        REAL NOT NULL,
  PRIMARY KEY (objektnr, stichtag)
);

-- Quelle 3: Tankkarten. Eine Zeile je Position auf dem Beleg. objektnr aus dem Beleg; Zuordnung geprüft gegen fahrzeug.
CREATE TABLE tankung (
  tankung_id      INTEGER PRIMARY KEY,
  objektnr        TEXT REFERENCES fahrzeug (objektnr),
  kennzeichen     TEXT NOT NULL,
  datum           TEXT NOT NULL,
  anbieter        TEXT,
  position        TEXT NOT NULL,       -- Kraftstoff, Tankstellenrabatt, Maut, ...
  km_stand        REAL,
  liter           REAL,
  preis_je_liter  REAL,
  kraftstoff      TEXT,
  betrag_eur      REAL NOT NULL,
  beleg_seite     INTEGER
);

-- Quelle 4: Ladekarten. Eine Zeile je Karte, Ladenetz und Leistungsklasse im Abrechnungsmonat.
-- Zuordnung zum Fahrzeug über die Ladekartennummer in den Stammdaten; objektnr NULL, wenn die Karte dort fehlt.
CREATE TABLE ladung (
  ladung_id         INTEGER PRIMARY KEY,
  kartennr          TEXT NOT NULL,
  objektnr          TEXT REFERENCES fahrzeug (objektnr),
  kennzeichen       TEXT,
  netz              TEXT NOT NULL,
  leistungsklasse   TEXT,
  ladevorgaenge     REAL,
  energie_kwh       REAL,
  ladedauer_min     REAL,
  blockierdauer_min REAL,
  betrag_eur        REAL NOT NULL
);
