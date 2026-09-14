"""Regelbasierter Generator: erzeugt aus params.json eine synthetische Flotten-Stammdatei.

Aufruf:  python src/synth/generate.py            -> data/sample/flotte_stammdaten.csv, src/synth/fehlerkatalog.md
Optionen: --n 250 --seed 42

Kalibriert an params.json (Häufigkeiten, Quantile, Fehlquoten aus einem echten Export mit 91 Spalten). Die Spalten sind
auf das reduziert, was jede Flotte führt: Fahrzeug, Vertrag, Kosten, Nutzung, Kilometerstände je Stichtag. Alle Personen,
Kennzeichen, Fahrgestell-, Objekt- und Kartennummern, Kostenstellen und Bemerkungen sind erfunden.
Das Format ist absichtlich so unordentlich wie ein Excel-Export: zwei Kommentarzeilen vor der Kopfzeile, Semikolon, Latin-1,
Zahlen mit Leerzeichen als Tausendertrenner und Dezimalkomma, Datum als TT.MM.JJJJ, Kilometerstände als Spalten.
Eingebaute Fehler stehen im Fehlerkatalog.
"""
import argparse, csv, json, random, re
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P = json.loads((HERE / "params.json").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "sample" / "flotte_stammdaten.csv"
KATALOG = HERE / "fehlerkatalog.md"

NACHNAMEN = ["Gruber", "Huber", "Bauer", "Wagner", "Müller", "Pichler", "Steiner", "Moser", "Mayer", "Hofer", "Leitner", "Berger",
             "Fuchs", "Eder", "Fischer", "Schmid", "Winkler", "Weber", "Schwarz", "Maier", "Schneider", "Reiter", "Mayr", "Schmidt",
             "Wimmer", "Egger", "Brunner", "Lang", "Baumgartner", "Auer", "Binder", "Lechner", "Wolf", "Wallner", "Aigner", "Ebner",
             "Koller", "Lehner", "Haas", "Schuster", "Novak", "Horvath", "Kovacs", "Nguyen", "Yilmaz", "Kaya", "Öztürk", "Petrovic"]
VORNAMEN = ["Anna", "Maria", "Julia", "Sabine", "Andrea", "Claudia", "Eva", "Katharina", "Birgit", "Petra", "Lisa", "Sarah",
            "Thomas", "Michael", "Andreas", "Christian", "Martin", "Markus", "Stefan", "Peter", "Wolfgang", "Daniel", "Florian", "Lukas",
            "Georg", "Franz", "Josef", "Manfred", "Herbert", "Karl", "Ali", "Mehmet", "Ivan", "Nina", "Elena", "Sophie"]
STANDORTE = ["Wien", "Wien", "Wien", "Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt"]
KATEGORIE = {"VF - CS": "Außendienst", "VF": "Außendienst", "VF - S": "Servicetechnik", "SM": "Innendienst", "DW": "Innendienst", "DW +": "Innendienst", "GF": "Geschäftsführung", "Pool": "Pool"}
BEZIRKE = ["W", "W", "W", "W", "W", "G", "L", "S", "K", "I", "P", "KL", "WU", "MD", "BN", "GU", "LL", "VB", "SL"]
WMI = {"VW": "WVW", "BMW": "WBA", "SKODA": "TMB", "OPEL": "W0V", "MERCEDES": "W1K", "AUDI": "WAU", "PEUGEOT": "VR3",
       "VOLVO": "YV1", "Polestar": "LPS", "SEAT": "VSS", "FORD": "WF0", "MINI": "WMW"}
STICHTAGE = [date(2021, 12, 31), date(2022, 6, 30), date(2022, 12, 31), date(2023, 6, 30), date(2023, 12, 31), date(2024, 6, 30),
             date(2024, 12, 31), date(2025, 6, 30), date(2025, 9, 30), date(2025, 12, 31)]
KM_COL = lambda d: f"km-Stand per {d.strftime('%d.%m.%Y')}"
HEADER = ["Objektnr.", "Kennzeichen", "Fahrgestell-Nr.", "Marke", "Modell", "Antrieb", "Fahrzeug Typ", "kW", "CO2 g/km (WLTP)", "Erstzulassung",
          "Status", "abgemeldet per", "Leasinggeber", "Vertragsbeginn", "Vertragsende", "Vertragsende ursprünglich", "Vertrag verlängert",
          "Laufzeit (Monate)", "Laufleistung gesamt (km)", "Freikilometer", "Mehrkilometer (EUR/km)", "Minderkilometer (EUR/km)",
          "Leasingrate exkl. MwSt", "davon Servicerate", "Anschaffungswert inkl. MwSt", "Fahrer (Nach- und Vorname)", "Fahrerkategorie",
          "Kostenstelle", "Standort", "Ladekarte Nr.", "Ladung@home", "Überprüfung fällig"] + [KM_COL(d) for d in STICHTAGE] + ["Bemerkung"]


def weighted(counter, rng, drop_empty=True):
    items = [(k, v) for k, v in counter.items() if (k != "" or not drop_empty)]
    ks, ws = zip(*items)
    return rng.choices(ks, weights=ws)[0]


def from_quantiles(q, rng, ndigits=2):
    qs = sorted((float(k), v) for k, v in q.items()); u = rng.random()
    for (a, va), (b, vb) in zip(qs, qs[1:]):
        if a <= u <= b:
            return round(va + (vb - va) * ((u - a) / (b - a) if b > a else 0), ndigits)
    return round(qs[-1][1], ndigits)


def de_num(x, ndigits=2):
    if x is None: return ""
    if ndigits == 0: return f"{int(round(x)):,}".replace(",", " ")
    return f"{x:,.{ndigits}f}".replace(",", "\x00").replace(".", ",").replace("\x00", " ")


def de_date(d): return d.strftime("%d.%m.%Y") if d else ""


def add_months(d, m):
    y, mo = d.year + (d.month - 1 + m) // 12, (d.month - 1 + m) % 12 + 1
    return date(y, mo, min(d.day, [31, 29 if y % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1]))


def rand_date(a, b, rng): return a + timedelta(days=rng.randint(0, (b - a).days))


def plate(rng, pattern=None):
    pattern = pattern or weighted(P["kennzeichen_muster"], rng)
    body = pattern.split(" ", 1)[1]
    s = "".join(rng.choice("123456789") if c == "9" else rng.choice("ABCDEFGHJKLMNPRSTUVWXYZ") for c in body if c in "9A")
    return f"{rng.choice(BEZIRKE)} {s}"


def person(rng): return f"{rng.choice(NACHNAMEN)} {rng.choice(VORNAMEN)}"


def build(n, seed):
    rng = random.Random(seed)
    N = P["numerisch"]; K = P["kategorien"]
    fehler = []; rows = []; used = set()
    objnr = rng.sample(range(300000, 399999), n + 10); karten = iter(rng.sample(range(140000, 180000), n + 10))
    for i in range(n):
        status = weighted(K["Status"], rng)
        marke = weighted(K["Marke"], rng); modell = weighted(P["modelle_je_marke"][marke], rng)
        bev = bool(re.search(r"ID\.|EQ|i4|iX|Polestar|e-tron|Enyaq|E-|Tourer Pro|Klasse E", modell))
        antrieb = "E" if bev else weighted({k: v for k, v in K["Antrieb"].items() if k not in ("E", "")}, rng)
        typ = ("BEV" if bev else ("PHEV" if antrieb.startswith("H") else "ICE")) if rng.random() > K["Fahrzeug Typ"][""] / P["n"] else ""
        if status == "in Bestellung":
            erst = beginn = ende_urspr = abgemeldet = None; laufzeit = ""
        else:
            laufzeit = int(weighted({k: v for k, v in K["Laufzeit Vertragsabschluss"].items() if k.isdigit()}, rng))
            if status == "aktiv":   # Vertrag läuft noch: Beginn so, dass das Ende nach dem Stichtag 30.09.2025 liegt
                lo, hi = max(date(2019, 1, 1), add_months(date(2025, 11, 1), -laufzeit)), date(2025, 9, 1)
            else:
                lo, hi = date(2016, 1, 1), date(2023, 6, 1)
            erst = rand_date(lo, hi, rng); beginn = erst + timedelta(days=rng.randint(0, 20))
            ende_urspr = add_months(beginn, laufzeit)
            abgemeldet = min(ende_urspr + timedelta(days=rng.randint(-60, 30)), date(2025, 11, 30)) if status == "inaktiv" else None
        verlaengert = status != "in Bestellung" and rng.random() < 0.10
        ende_eff = add_months(ende_urspr, 12) if verlaengert else ende_urspr
        rate = min(from_quantiles(P["km_pro_monat_quantile"], rng, 0), 4200)   # Ausreißer der Quelle (6.900 km/Monat) nicht übernehmen
        # vertragliche Laufleistung: grob zur Fahrleistung passend, auf 5.000 gerundet; jeder vierte Vertrag ohne Angabe
        km_gesamt = de_num(round(rate * laufzeit * rng.uniform(0.7, 1.3) / 5000) * 5000, 0) if erst and rng.random() > 0.25 else ""
        freikm = weighted(K["Freikilometer"], rng) if rng.random() > 0.25 else ""
        km = {}; prev = 0
        for st in STICHTAGE:
            if not erst or st < erst or (abgemeldet and st > abgemeldet + timedelta(days=90)) or st > date(2025, 10, 1):
                km[st] = None; continue
            val = max(prev, int(rate * (st - erst).days / 30.4 * rng.uniform(0.9, 1.1)))
            km[st] = val if rng.random() > 0.08 else None
            if km[st] is not None: prev = val
        kz = plate(rng)
        while kz in used: kz = plate(rng)
        used.add(kz)
        gesamt = from_quantiles(N["Gesamt-kosten exkl. MwSt"]["quantile"], rng); service = round(gesamt * rng.uniform(0.15, 0.4), 2)
        mehr = from_quantiles(N["Mehrkilometer"]["quantile"], rng, 4) if rng.random() > N["Mehrkilometer"]["fehlend"] else None
        r = {
            "Objektnr.": objnr[i], "Kennzeichen": kz,
            "Fahrgestell-Nr.": (WMI.get(marke, "WXX") + "".join(rng.choice("ABCDEFGHJKLMNPRSTUVWXYZ0123456789") for _ in range(14))) if rng.random() > P["fehlquote"]["VIN Number"] else "",
            "Marke": marke, "Modell": modell, "Antrieb": antrieb, "Fahrzeug Typ": typ,
            "kW": "" if rng.random() < N["kW (P2)"]["fehlend"] else de_num(from_quantiles(N["kW (P2)"]["quantile"], rng, 0), 0),
            "CO2 g/km (WLTP)": "" if bev or rng.random() < N["CO² lt. Her-steller nach WLTP"]["fehlend"] else de_num(from_quantiles(N["CO² lt. Her-steller nach WLTP"]["quantile"], rng, 0), 0),
            "Erstzulassung": de_date(erst), "Status": status, "abgemeldet per": de_date(abgemeldet),
            "Leasinggeber": weighted(K["Fahrzeugeigentümer"], rng),
            "Vertragsbeginn": de_date(beginn), "Vertragsende": de_date(ende_eff), "Vertragsende ursprünglich": de_date(ende_urspr), "Vertrag verlängert": "Ja" if verlaengert else "",
            "Laufzeit (Monate)": str(laufzeit), "Laufleistung gesamt (km)": km_gesamt, "Freikilometer": freikm,
            "Mehrkilometer (EUR/km)": de_num(mehr, 4) if mehr is not None else "", "Minderkilometer (EUR/km)": de_num(mehr, 4) if mehr is not None else "",
            "Leasingrate exkl. MwSt": de_num(gesamt), "davon Servicerate": de_num(service),
            "Anschaffungswert inkl. MwSt": de_num(from_quantiles(N["AW inkl. MwSt. u Nova"]["quantile"], rng)),
            "Fahrer (Nach- und Vorname)": person(rng), "Fahrerkategorie": KATEGORIE[weighted(K["Fahrer-kategorie"], rng)],
            "Kostenstelle": (f"KST0{rng.randint(50, 130):03d}" if rng.random() < 0.5 else str(rng.randint(201000, 202000))), "Standort": rng.choice(STANDORTE),
            "Ladekarte Nr.": str(next(karten)) if bev and status != "in Bestellung" else "",
            "Ladung@home": weighted(K["Ladung@home"], rng, drop_empty=False) if bev else "",
            "Überprüfung fällig": f"{rng.randint(2026, 2027)} {rng.choice(['Jänner', 'März', 'Mai', 'Juli', 'September', 'Oktober', 'Dezember'])}" if status == "aktiv" and rng.random() < 0.8 else "",
            "Bemerkung": rng.choice([f"Übernahme {person(rng)} ab {de_date(rand_date(date(2023, 1, 1), date(2025, 10, 1), rng))}", f"Karenz ab {rng.choice(['Mai', 'September', 'Jänner'])} {rng.randint(2023, 2025)}",
                                     f"Austritt {de_date(rand_date(date(2024, 1, 1), date(2025, 12, 31), rng))}", f"ex {rng.choice(NACHNAMEN).upper()}", "Poolfahrzeug", "Winterreifen im Depot"]) if rng.random() < 0.23 else "",
        }
        for st in STICHTAGE: r[KM_COL(st)] = de_num(km[st], 0) if km[st] is not None else ""
        r["_km"] = km
        rows.append(r)

    for kz, j in zip(["G 123AB", "W 45678C", "K 9012D"], range(3)):
        rows[j]["Kennzeichen"] = kz; rows[j]["Status"] = "aktiv"; rows[j]["abgemeldet per"] = ""
    fehler.append(f"Die Kennzeichen G 123AB, W 45678C und K 9012D (Objektnr. {rows[0]['Objektnr.']}, {rows[1]['Objektnr.']}, {rows[2]['Objektnr.']}) gehören zu den Rechnungen in `beispiel.csv`; dort stehen sie als G123AB, G-123AB, W-45678C, W 45678C, K-9012D. Kein Fehler, aber die Normalisierungsaufgabe.")
    for j in (5, 40, 77):
        d = dict(rows[j]); d["Kennzeichen"] = rows[j]["Kennzeichen"].replace(" ", "-"); rows.append(d)
        fehler.append(f"Duplikat: Objektnr. {rows[j]['Objektnr.']} steht zweimal, einmal als `{rows[j]['Kennzeichen']}`, einmal als `{d['Kennzeichen']}`.")
    for j in (9, 23, 61, 88, 120):
        alt = rows[j]["Kennzeichen"]; rows[j]["Kennzeichen"] = alt.replace(" ", "")
        fehler.append(f"Schreibvariante: Objektnr. {rows[j]['Objektnr.']} mit Kennzeichen `{rows[j]['Kennzeichen']}` statt `{alt}`.")
    cnt = 0
    for r in rows:
        vals = [(st, r["_km"][st]) for st in STICHTAGE if r["_km"][st] is not None]
        if len(vals) >= 3 and cnt < 5:
            st, v = vals[-2]; r[KM_COL(st)] = de_num(int(v * 0.6), 0); cnt += 1
            fehler.append(f"Kilometerstand rückläufig: Objektnr. {r['Objektnr.']}, Spalte `{KM_COL(st)}` = {r[KM_COL(st)]} liegt unter dem Vorwert.")
    r = rows[14]; st = next((s for s in STICHTAGE if r["_km"][s]), None)
    if st: r[KM_COL(st)] = de_num(r["_km"][st] * 10, 0); fehler.append(f"Tippfehler: Objektnr. {r['Objektnr.']}, Spalte `{KM_COL(st)}` = {r[KM_COL(st)]} (eine Null zu viel).")
    for j in (30, 31, 32):
        if rows[j]["Mehrkilometer (EUR/km)"]:
            rows[j]["Mehrkilometer (EUR/km)"] = de_num(float(rows[j]["Mehrkilometer (EUR/km)"].replace(",", ".")) * 100, 2)
            fehler.append(f"Einheitenwechsel: Objektnr. {rows[j]['Objektnr.']}, Mehrkilometer = {rows[j]['Mehrkilometer (EUR/km)']} (Cent statt Euro je km wie in den übrigen Zeilen).")
    for j in (44, 45):
        if rows[j]["Erstzulassung"]:
            d = date(*reversed([int(x) for x in rows[j]["Erstzulassung"].split(".")])); rows[j]["Erstzulassung"] = str((d - date(1899, 12, 30)).days)
            fehler.append(f"Datumsformat: Objektnr. {rows[j]['Objektnr.']}, Erstzulassung = {rows[j]['Erstzulassung']} (Excel-Seriennummer statt TT.MM.JJJJ).")
    rows[50]["Leasinggeber"] = "LeasePlan"; fehler.append(f"Schreibweise: Objektnr. {rows[50]['Objektnr.']}, Leasinggeber `LeasePlan` statt `Leaseplan`.")
    rows[52]["Kennzeichen"] = f"{rows[52]['Kennzeichen']} / {plate(rng)} / {plate(rng)}"; fehler.append(f"Mehrfachwert: Objektnr. {rows[52]['Objektnr.']}, drei Kennzeichen in einer Zelle (Kennzeichenwechsel).")
    rows[53]["Leasingrate exkl. MwSt"] = "#BEZUG!"; fehler.append(f"Excel-Fehlerwert: Objektnr. {rows[53]['Objektnr.']}, Leasingrate = `#BEZUG!`.")
    letzte = KM_COL(STICHTAGE[-2])
    akt = [r for r in rows if r["Status"] == "aktiv"]
    for r in akt[::6]: r[letzte] = ""
    fehler.append(f"Lücke: {len(akt[::6])} von {len(akt)} aktiven Fahrzeugen ohne Kilometerstand zum {STICHTAGE[-2].strftime('%d.%m.%Y')}; für sie ist keine Hochrechnung möglich.")
    return rows, fehler


def write(rows, fehler, n, seed):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="latin-1", errors="replace", newline="") as f:
        f.write(";Stammdatenexport Flotte (synthetisch);Stand 30.09.2025" + ";" * (len(HEADER) - 3) + "\r\n")
        f.write(";" * 32 + "Kilometerstände je Stichtag" + ";" * (len(HEADER) - 33) + "\r\n")
        w = csv.writer(f, delimiter=";", lineterminator="\r\n"); w.writerow(HEADER)
        for r in rows: w.writerow([str(r.get(h, "")) for h in HEADER])
    KATALOG.write_text("# Fehlerkatalog · flotte_stammdaten.csv\n\n"
                       f"Erzeugt von `src/synth/generate.py` mit `--n {n} --seed {seed}`; {len(rows)} Zeilen, {len(HEADER)} Spalten. "
                       "Diese Fehler stecken absichtlich drin. Sie sind die Referenz für den Qualitätsbericht (Schritt 2): "
                       "Wer sie findet, hat die Pipeline richtig gebaut; wer eine Abfrage darauf laufen lässt, ohne sie zu bereinigen, bekommt falsche Zahlen.\n\n"
                       + "\n".join(f"- {x}" for x in fehler) + "\n\nDazu die Eigenheiten des Formats, die kein Fehler sind, aber gelöst werden müssen: "
                       "zwei Kommentarzeilen vor der Kopfzeile, Semikolon, Latin-1, Zahlen mit Leerzeichen als Tausendertrenner und Dezimalkomma, "
                       "leere Zellen für fehlende Werte, Datum als TT.MM.JJJJ, zehn Kilometerstände als Spalten statt Zeilen (der letzte Stichtag noch leer), "
                       "Ja/Nein in mehreren Schreibweisen (`Ja`, `ja`, `X`, `x`, `nein`), `Fahrzeug Typ` nur zur Hälfte gefüllt (aus `Antrieb` ableitbar: D Diesel, B Benzin, E Elektro, H/B und H/D Hybrid), "
                       "`Antrieb` als Kürzel, `Bemerkung` als Freitext mit Personennamen.\n", encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(rows)} Zeilen, {len(HEADER)} Spalten; {KATALOG.relative_to(ROOT)}: {len(fehler)} Einträge")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=250); ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args(); rows, fehler = build(a.n, a.seed); write(rows, fehler, a.n, a.seed)
