"""Stufe 2, Bereinigen je Quelle: lesen, Typen, Formate, Schlüssel, Duplikate, PII. Eine Funktion je Quelle.

Jede Funktion liest ihre Datei aus data/interim/, schreibt eine bereinigte CSV dorthin zurück und gibt ihre Zahlen aus.
Die Zahlen gehören in den Qualitätsbericht (Projektdoku, Schritt 2).
"""
import json, re
from datetime import date, timedelta
import pandas as pd
from config import INTERIM, QUELLEN, PII_COLUMNS


# ---------------------------------------------------------------- Hilfsfunktionen: hier fallen die Entscheidungen
def normalize_id(value):
    """'G 123AB', 'G-123AB', 'g123ab' werden zu 'G123AB'. Mehrere Kennzeichen in einer Zelle ('A / B / C'): das erste."""
    if pd.isna(value) or not str(value).strip():
        return None
    first = str(value).split("/")[0]
    return re.sub(r"[\s\-]", "", first).upper()


def to_number(value):
    """Deutsches Zahlenformat: '1 234,56' und '1.234,56' -> 1234.56; '12,5' -> 12.5; leer, '-' und Excel-Fehler -> NaN.
    Achtung: ein Punkt gilt hier als Tausenderpunkt. Liefert eure Quelle '123.02' mit Dezimalpunkt, braucht sie eine eigene Funktion."""
    if pd.isna(value):
        return float("nan")
    s = str(value).strip().replace(" ", "").replace("\xa0", "")
    if s in ("", "-") or s.startswith("#"):
        return float("nan")
    s = s.replace(".", "").replace(",", ".")
    if s.endswith("-"):  # '0,76-' ist ein negativer Betrag (Rabatt)
        s = "-" + s[:-1]
    try:
        return float(s)
    except ValueError:
        return float("nan")


def to_date(value):
    """'04.06.2025' -> 2025-06-04 (Tag zuerst!), '2025-06-04' bleibt, Excel-Seriennummer '43360' -> 2018-09-17, sonst NaT."""
    if pd.isna(value) or not str(value).strip():
        return pd.NaT
    s = str(value).strip()
    if re.fullmatch(r"\d{5}", s):
        return pd.Timestamp(date(1899, 12, 30) + timedelta(days=int(s)))
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
        return pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
    return pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")


def drop_pii(df: pd.DataFrame, quelle: str) -> pd.DataFrame:
    """Personenspalten entfernen. Hier, im Code, nicht im Prompt."""
    weg = [c for c in PII_COLUMNS if c in df.columns]
    if weg:
        print(f"  {quelle}: PII entfernt: {', '.join(weg)}")
    return df.drop(columns=weg)


# ---------------------------------------------------------------- Quelle 1: Rechnungen (CSV, sauber)
def rechnungen() -> pd.DataFrame:
    q = QUELLEN["rechnungen"]
    df = pd.read_csv(INTERIM / q["datei"], sep=q["sep"], encoding=q["encoding"], dtype=str)
    n0 = len(df)
    df["rechnungsnr"] = df["rechnungsnr"].str.strip()
    df["kennzeichen"] = df["kennzeichen"].map(normalize_id)
    df["netto_eur"] = df["netto_eur"].map(to_number)
    df["mwst_pct"] = df["mwst_pct"].map(to_number)
    df["datum"] = df["datum"].map(to_date).dt.date
    dups = df.duplicated(subset=["rechnungsnr"], keep="first").sum()
    df = df.drop_duplicates(subset=["rechnungsnr"], keep="first")
    missing = df["netto_eur"].isna().sum()
    df = drop_pii(df, "rechnungen")
    df.to_csv(INTERIM / "rechnungen_clean.csv", index=False)
    print(f"clean rechnungen: {n0} Zeilen gelesen, {dups} Duplikat(e) entfernt, {missing} Zeile(n) ohne Betrag markiert")
    return df


# ---------------------------------------------------------------- Quelle 2: Stammdaten (CSV-Export aus Excel, unordentlich)
def stammdaten() -> tuple[pd.DataFrame, pd.DataFrame]:
    q = QUELLEN["stammdaten"]
    df = pd.read_csv(INTERIM / q["datei"], sep=q["sep"], encoding=q["encoding"], skiprows=q["skiprows"], dtype=str)
    df.columns = [" ".join(c.split()) for c in df.columns]   # Zeilenumbrüche und Doppelleerzeichen in Überschriften
    n0 = len(df)
    mehrfach = df["Kennzeichen"].str.contains("/", na=False).sum()
    df["kennzeichen"] = df["Kennzeichen"].map(normalize_id)
    for col in ["kW", "CO2 g/km (WLTP)", "Laufzeit (Monate)", "Laufleistung gesamt (km)", "Freikilometer", "Mehrkilometer (EUR/km)",
                "Minderkilometer (EUR/km)", "Leasingrate exkl. MwSt", "davon Servicerate", "Anschaffungswert inkl. MwSt"]:
        df[col] = df[col].map(to_number)
    fehlerwerte = int(df["Leasingrate exkl. MwSt"].isna().sum())
    for col in ["Erstzulassung", "abgemeldet per", "Vertragsbeginn", "Vertragsende", "Vertragsende ursprünglich"]:
        df[col] = df[col].map(to_date).dt.date
    # Einheiten: Mehrkilometer sind EUR/km; Werte über 1 sind Cent (Einheitenwechsel in einer Teilmenge)
    cent = df["Mehrkilometer (EUR/km)"] > 1
    df.loc[cent, ["Mehrkilometer (EUR/km)", "Minderkilometer (EUR/km)"]] /= 100
    # Schreibweisen vereinheitlichen
    df["Leasinggeber"] = df["Leasinggeber"].str.strip().str.replace("LeasePlan", "Leaseplan")
    df["Ladung@home"] = df["Ladung@home"].str.strip().str.lower().map({"ja": "ja", "x": "ja", "nein": "nein"})
    df["Antrieb"] = df["Antrieb"].map({"D": "Diesel", "B": "Benzin", "E": "Elektro", "H/B": "Hybrid", "H/D": "Hybrid"})
    # Duplikate: dieselbe Objektnummer zweimal (mit anderer Kennzeichen-Schreibweise)
    dups = df.duplicated(subset=["Objektnr."], keep="first").sum()
    df = df.drop_duplicates(subset=["Objektnr."], keep="first")
    # Kilometerstände: von Spalten in Zeilen (eine Zeile je Fahrzeug und Stichtag)
    km_cols = [c for c in df.columns if c.startswith("km-Stand per")]
    km = df.melt(id_vars=["Objektnr."], value_vars=km_cols, var_name="stichtag", value_name="km")
    km["stichtag"] = km["stichtag"].str.replace("km-Stand per ", "").map(to_date).dt.date
    km["km"] = km["km"].map(to_number)
    km = km.dropna(subset=["km"]).sort_values(["Objektnr.", "stichtag"])
    ruecklaeufig = int((km.groupby("Objektnr.")["km"].diff() < 0).sum())
    df = df.drop(columns=km_cols)
    df = drop_pii(df, "stammdaten")
    df.to_csv(INTERIM / "stammdaten_clean.csv", index=False)
    km.to_csv(INTERIM / "kilometerstand_clean.csv", index=False)
    print(f"clean stammdaten: {n0} Zeilen gelesen, {dups} Duplikat(e) entfernt, {mehrfach} Zelle(n) mit mehreren Kennzeichen, "
          f"{int(cent.sum())} Mehrkilometer-Wert(e) von Cent auf Euro, {fehlerwerte} Fehlerwert(e) in Leasingrate, "
          f"{len(km)} Kilometerstände, davon {ruecklaeufig} rückläufig (bleiben drin, markiert im Bericht)")
    return df, km


# ---------------------------------------------------------------- Quelle 3: Tankkarten (Text-PDF des Leasinggebers)
def tankkarten() -> pd.DataFrame:
    import pdfplumber
    q = QUELLEN["tankkarten"]
    with pdfplumber.open(INTERIM / q["datei"]) as pdf:
        seiten = [p.extract_text() or "" for p in pdf.pages]
    zeilen = []; kz = obj = None
    kopf = re.compile(r"^([A-Z]{1,2}[\s\-]?\d{2,5}[A-Z]{1,2}) Obj: (\d+)")
    tank = re.compile(r"^(DKV EUROSERVICE|SHELL|OMV DOWN)\s?(\d{8}) (\d+) (?:(\d+)km )?([\d.,]+) Lit ([\d,]+) (\w+) ([\d.,]+)$")
    sonst = re.compile(r"^(DKV EUROSERVICE|SHELL|OMV DOWN)\s?(\d{8}) (\d+) ((?!\d)[A-Za-z.\- ]+?) ([\d.,]+-?)$")
    for nr, text in enumerate(seiten, 1):
        for line in text.splitlines():
            m = kopf.match(line)
            if m:
                kz, obj = m[1], m[2]; continue
            m = tank.match(line)
            if m and kz:
                zeilen.append(dict(seite=nr, kennzeichen=kz, objektnr=obj, anbieter=m[1].split()[0], datum=m[2], km_stand=m[4],
                                   liter=m[5], preis_je_liter=m[6], kraftstoff=m[7], position="Kraftstoff", betrag_eur=m[8])); continue
            m = sonst.match(line)
            if m and kz:
                zeilen.append(dict(seite=nr, kennzeichen=kz, objektnr=obj, anbieter=m[1].split()[0], datum=m[2], km_stand=None,
                                   liter=None, preis_je_liter=None, kraftstoff=None, position=m[4], betrag_eur=m[5]))
    df = pd.DataFrame(zeilen)
    df["kennzeichen"] = df["kennzeichen"].map(normalize_id)
    df["datum"] = pd.to_datetime(df["datum"], format="%Y%m%d").dt.date
    for col in ["km_stand", "liter", "preis_je_liter", "betrag_eur"]:
        df[col] = df[col].map(to_number)
    # Plausibilität: Betrag gegen Liter × Preis
    diff = (df["position"] == "Kraftstoff") & ((df["liter"] * df["preis_je_liter"] - df["betrag_eur"]).abs() > 0.05)
    gesamt = re.search(r"Gesamtbetrag ([\d.,]+) EUR", seiten[0])
    df.to_csv(INTERIM / "tankungen_clean.csv", index=False)
    print(f"clean tankkarten: {len(seiten)} Seiten, {len(df)} Positionen für {df['kennzeichen'].nunique()} Fahrzeuge, "
          f"Summe {df['betrag_eur'].sum():.2f} gegen Gesamtbetrag Seite 1 {gesamt[1] if gesamt else '?'}, {int(diff.sum())} Betrag/Liter-Widerspruch")
    return df


# ---------------------------------------------------------------- Quelle 4: Ladekarten (Text-PDF des Ladenetzbetreibers)
def ladekarten() -> pd.DataFrame:
    import pdfplumber
    q = QUELLEN["ladekarten"]
    with pdfplumber.open(INTERIM / q["datei"]) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    karte = re.compile(r"^Kartennr\. (\d+) \[[^,\]]*, ?([^\]]*)\]")     # Name wird nicht übernommen (PII)
    pos = re.compile(r"^\d\d\.\d\.\d\d\s+DR\d+\s+(Ladedauer|Blockierdauer|Freiminuten|Ladevorgänge|Abgegebene Energie) \(([^)]+)\) ([\d.,]+) (Min|Stk|kWh) ([\d,]+) ([\d.,]+) EUR$")
    zeilen = []; kartennr = kz = None; offen = None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = karte.match(line)
        if m:
            kartennr, kz = m[1], m[2].strip(); continue
        m = pos.match(line)
        if m and kartennr:
            # Das Ladenetz steht in der Zeile darunter. Am Seitenende liegen dazwischen Übertrag, Fußzeile und der Kopf der nächsten Seite.
            seitenwechsel = re.compile(r"^(Übertrag |R E C H N U N G|Pos +Art-Nr|Beispiel Ladenetz|Handelsgericht)")
            netz = next((l.strip() for l in lines[i + 1:i + 8] if l.strip() and not seitenwechsel.match(l.strip())), "")
            zeilen.append(dict(kartennr=kartennr, kennzeichen=kz, netz=netz, leistungsklasse=m[2], art=m[1], menge=m[3], einheit=m[4], preis=m[5], betrag_eur=m[6]))
    df = pd.DataFrame(zeilen)
    for col in ["menge", "preis", "betrag_eur"]:
        df[col] = df[col].map(to_number)
    df["kennzeichen"] = df["kennzeichen"].map(normalize_id).fillna("")
    # Eine Zeile je Karte, Netz und Leistungsklasse: Vorgänge, kWh, Minuten, Betrag (aus fünf Positionszeilen wird eine)
    key = ["kartennr", "kennzeichen", "netz", "leistungsklasse"]
    mengen = df.groupby(key + ["art"])["menge"].sum().unstack("art").reset_index()
    betrag = df.groupby(key)["betrag_eur"].sum().reset_index()
    out = mengen.merge(betrag, on=key).rename(columns={"Ladevorgänge": "ladevorgaenge", "Abgegebene Energie": "energie_kwh",
                                                       "Ladedauer": "ladedauer_min", "Blockierdauer": "blockierdauer_min"})
    out = out.drop(columns=[c for c in ["Freiminuten"] if c in out.columns]); out.columns.name = None
    out["kennzeichen"] = out["kennzeichen"].replace("", None)
    ohne_kz = int(out["kennzeichen"].isna().sum())
    netto = re.search(r"Nettobetrag ([\d.,]+) EUR", text)
    out.to_csv(INTERIM / "ladungen_clean.csv", index=False)
    print(f"clean ladekarten: {len(df)} Positionen, {len(out)} Zeilen je Karte/Netz/Klasse, {out['kartennr'].nunique()} Karten, "
          f"{ohne_kz} ohne Kennzeichen, Summe {out['betrag_eur'].sum():.2f} gegen Nettobetrag {netto[1] if netto else '?'}")
    return out


def run() -> dict:
    return {"rechnungen": rechnungen(), "stammdaten": stammdaten(), "tankkarten": tankkarten(), "ladekarten": ladekarten()}
