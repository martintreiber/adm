"""Stufe 3, Integrieren: bereinigte Quellen in die SQLite schreiben, Datenmodell aus schema.sql, Quellen über Schlüssel verknüpfen.

Jeder Lauf löscht die Datenbank und baut sie neu (idempotent). Zeilen, die keinen Partner finden, werden gezählt, nicht verworfen.
"""
import sqlite3
import pandas as pd
from config import INTERIM, DB, SQL, PROCESSED


def run() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript((SQL / "schema.sql").read_text(encoding="utf-8"))

    # Quelle 1
    rech = pd.read_csv(INTERIM / "rechnungen_clean.csv")
    rech.to_sql("rechnung", con, if_exists="append", index=False)

    # Quelle 2: Stammdaten -> fahrzeug (Spalten auf die Namen des Datenmodells), Kilometerstände -> kilometerstand
    st = pd.read_csv(INTERIM / "stammdaten_clean.csv", dtype={"Objektnr.": str, "Kostenstelle": str, "Ladekarte Nr.": str})
    fahrzeug = pd.DataFrame({
        "objektnr": st["Objektnr."], "kennzeichen": st["kennzeichen"], "fahrgestellnr": st["Fahrgestell-Nr."], "marke": st["Marke"],
        "modell": st["Modell"], "antrieb": st["Antrieb"], "kw": st["kW"], "co2_g_km": st["CO2 g/km (WLTP)"], "erstzulassung": st["Erstzulassung"],
        "status": st["Status"], "abgemeldet_am": st["abgemeldet per"], "leasinggeber": st["Leasinggeber"], "vertragsbeginn": st["Vertragsbeginn"],
        "vertragsende": st["Vertragsende"], "laufzeit_monate": st["Laufzeit (Monate)"], "laufleistung_km": st["Laufleistung gesamt (km)"],
        "freikilometer": st["Freikilometer"], "mehrkm_eur_km": st["Mehrkilometer (EUR/km)"], "leasingrate_eur": st["Leasingrate exkl. MwSt"],
        "servicerate_eur": st["davon Servicerate"], "anschaffungswert_eur": st["Anschaffungswert inkl. MwSt"], "fahrerkategorie": st["Fahrerkategorie"],
        "kostenstelle": st["Kostenstelle"], "standort": st["Standort"], "ladekarte_nr": st["Ladekarte Nr."].where(st["Ladekarte Nr."].notna(), None),
    })
    fahrzeug["ladekarte_nr"] = fahrzeug["ladekarte_nr"].map(lambda x: str(x).split(".")[0] if pd.notna(x) else None)
    fahrzeug.to_sql("fahrzeug", con, if_exists="append", index=False)
    km = pd.read_csv(INTERIM / "kilometerstand_clean.csv", dtype={"Objektnr.": str}).rename(columns={"Objektnr.": "objektnr"})
    km.to_sql("kilometerstand", con, if_exists="append", index=False)

    # Quelle 3: Tankungen. Zuordnung: Objektnummer aus dem Beleg gegen fahrzeug; Kennzeichen als zweiter Weg.
    tk = pd.read_csv(INTERIM / "tankungen_clean.csv", dtype={"objektnr": str})
    bekannt = set(fahrzeug["objektnr"]); kz_map = dict(zip(fahrzeug["kennzeichen"], fahrzeug["objektnr"]))
    tk["objektnr"] = [o if o in bekannt else kz_map.get(k) for o, k in zip(tk["objektnr"], tk["kennzeichen"])]
    tk_ohne = int(tk["objektnr"].isna().sum())
    tk.rename(columns={"seite": "beleg_seite"}).to_sql("tankung", con, if_exists="append", index=False)

    # Quelle 4: Ladungen. Zuordnung über die Ladekartennummer in den Stammdaten, sonst über das Kennzeichen.
    ld = pd.read_csv(INTERIM / "ladungen_clean.csv", dtype={"kartennr": str})
    karte_map = dict(zip(fahrzeug["ladekarte_nr"].dropna(), fahrzeug.loc[fahrzeug["ladekarte_nr"].notna(), "objektnr"]))
    ld["objektnr"] = [karte_map.get(k) or kz_map.get(z) for k, z in zip(ld["kartennr"], ld["kennzeichen"])]
    ld_ohne = int(ld["objektnr"].isna().sum())
    ld.to_sql("ladung", con, if_exists="append", index=False)

    # Rechnungen gegen Stammdaten: wie viele Kennzeichen finden ein Fahrzeug?
    rech_ohne = int((~rech["kennzeichen"].isin(kz_map)).sum())
    con.commit()
    n = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ["fahrzeug", "kilometerstand", "rechnung", "tankung", "ladung"]}
    con.close()
    print(f"integrate: {DB.name}: " + ", ".join(f"{t} {c}" for t, c in n.items()) +
          f"; ohne Fahrzeug: {tk_ohne} Tankpositionen, {ld_ohne} Ladezeilen, {rech_ohne} Rechnungen")
