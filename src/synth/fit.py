"""Kalibrierung: liest die echte Stammdaten-Datei (nur lokal, nie im Repo) und schreibt Aggregate nach params.json.

Aufruf:  python src/synth/fit.py "/pfad/zur/echten/datei.csv"

In params.json landen nur Häufigkeiten, Quantile, Fehlquoten und Datumsbereiche. Keine Einzelzeile, keine Namen,
keine Kennzeichen, keine Fahrgestell- oder Objektnummern, keine Kostenstellen, keine Bemerkungen.
Die Spaltenüberschriften werden übernommen, damit die synthetische Datei dasselbe Format hat.
"""
import csv, io, json, re, sys
from collections import Counter
from datetime import date
from pathlib import Path

OUT = Path(__file__).resolve().parent / "params.json"

# Spalten nach Rolle. Alles, was hier nicht steht, wird nicht ausgewertet (Namen, IDs, Freitext, Händler, Kostenstellen).
KATEGORIEN = ["Fahrzeugeigentümer", "Antrieb", "Fahrzeug Typ", "Marke", "VST abzugs-fähig", "km Laufleistung gesamt",
              "Laufzeit Vertragsabschluss", "Freikilometer", "Vetrag verlängert", "Fahrer-kategorie", "Ladung@home",
              "ARE P58", "Status", "Rotes Kennzeichen", "IFRS16 FLEET relevant", "Sublease Type", "Benützungs bewilligung ausgestellt",
              "monatliche Fee exkl. UST in Service Rate enthalten"]
NUMERISCH = ["CO² lt. Her-steller nach WLTP", "kW (P2)", "Gewicht (G)", "Mehrkilometer", "Minderkilometerr", "Mindertage",
             "Vertragsgebühr", "Motorbezogene Versicherungssteuer", "Kosten Minderwertgutachten", "Schlussrechnung gesamt",
             "AW inkl. MwSt. u Nova", "Anteil Privat-nutzung LOA 0082", "red. Sach-bezug LOA 5750", "Gesamt-kosten exkl. MwSt",
             "Funding/ Finance Lease (incl. Executory Costs)", "Service Rate (non finance lease rate)"]
DATEN = ["vorauss. Liefertermin", "Datum Erst-zulassung", "An-/Ummelde datum", "Übergabe-datum", "HR-Meldung erledigt",
         "abge- meldet per", "Vertrags-beginn", "Vertragsende Effektiv inkl. Änderungen", "Vertragsende ursprünglich"]
FEHLQUOTE_NUR = ["Objektnr. LP", "Kunden nummer", "ausliefernder Händler", "NRGkick Dinitech", "Objektnr. Leasing supplier",
                 "In-Country Manager*in (Nach- und Vorname)", "Cost Center NEU ab 1.10.2024", "BU CF Depht Structure", "Reifen Depot",
                 "§57a Überprüfung", "Beschaffung Start", "ZLSchNr.", "Bemerkung", "VIN Number", "IFA Number", "letzter bekannter km-Stand ( lt. Minderwertgutachten)",
                 "km Differenz zu Vertrag"]


def norm(h): return re.sub(r"\s+", " ", h).strip()


def num(s):
    s = s.strip().replace(" ", "").replace(".", "").replace(",", ".")
    try: return float(s)
    except ValueError: return None


def dat(s):
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", s.strip())
    return date(int(m[3]), int(m[2]), int(m[1])) if m else None


def quantile(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1)
    return round(xs[f] + (xs[c] - xs[f]) * (k - f), 4)


def main(path):
    raw = Path(path).read_bytes().decode("latin-1")
    lines = raw.splitlines(keepends=True)
    rows = list(csv.reader(io.StringIO("".join(lines[2:])), delimiter=";"))
    header = rows[0]; names = [norm(h) for h in header]
    data = [r for r in rows[1:] if any(c.strip() for c in r)]
    idx = {n: i for i, n in enumerate(names)}
    col = lambda n: [r[idx[n]].strip() for r in data]
    N = len(data)
    p = {"quelle": f"Flottenstammdaten, {N} Zeilen, {len(names)} Spalten; aggregiert, keine Einzelwerte", "n": N,
         "header": header, "kategorien": {}, "modelle_je_marke": {}, "numerisch": {}, "daten": {}, "fehlquote": {}}
    for n in KATEGORIEN:
        c = Counter(col(n)); p["kategorien"][n] = dict(c.most_common())
    mm = {}
    for r in data:
        marke, modell = r[idx["Marke"]].strip(), r[idx["Modell"]].strip()
        modell = re.sub(r"^SHD\s*", "Klasse ", modell)  # Katalogkürzel des Kunden neutralisieren
        mm.setdefault(marke, Counter())[modell] += 1
    p["modelle_je_marke"] = {k: dict(v.most_common()) for k, v in mm.items()}
    for n in NUMERISCH:
        vals = [num(x) for x in col(n)]; xs = [v for v in vals if v is not None]
        p["numerisch"][n] = {"n": len(xs), "fehlend": round(1 - len(xs) / N, 3),
                             "quantile": {q: quantile(xs, q) for q in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)} if xs else None}
    for n in DATEN:
        ds = [dat(x) for x in col(n)]; ds = [d for d in ds if d]
        p["daten"][n] = {"n": len(ds), "fehlend": round(1 - len(ds) / N, 3),
                         "min": ds and min(ds).isoformat(), "max": ds and max(ds).isoformat()}
    for n in FEHLQUOTE_NUR:
        p["fehlquote"][n] = round(sum(1 for x in col(n) if not x) / N, 3)
    # Kilometerstände: Stichtage, Fehlquote je Stichtag, km je Monat über alle Fahrzeuge
    km_cols = [(i, n) for i, n in enumerate(names) if n.startswith("km-Stand per")]
    stich = []
    for i, n in km_cols:
        m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", n); d = date(int(m[3]), int(m[2]), int(m[1]))
        stich.append({"spalte": n, "datum": d.isoformat(), "fehlend": round(sum(1 for r in data if not r[i].strip()) / N, 3)})
    p["km_stichtage"] = stich
    raten = []
    for r in data:
        pts = [(date.fromisoformat(s["datum"]), num(r[i])) for (i, _), s in zip(km_cols, stich) if num(r[i]) is not None]
        if len(pts) >= 2 and pts[-1][1] > pts[0][1]:
            months = (pts[-1][0] - pts[0][0]).days / 30.4
            if months >= 3: raten.append((pts[-1][1] - pts[0][1]) / months)
    p["km_pro_monat_quantile"] = {q: quantile(raten, q) for q in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)}
    p["kennzeichen_muster"] = dict(Counter(re.sub(r"[A-Z]", "A", re.sub(r"\d", "9", x)) for x in col("Kennzeichen")).most_common(6))
    p["antrieb_je_typ"] = {}
    for r in data:
        t, a = r[idx["Fahrzeug Typ"]].strip(), r[idx["Antrieb"]].strip()
        if t: p["antrieb_je_typ"].setdefault(t, Counter())[a] += 1
    p["antrieb_je_typ"] = {k: dict(v) for k, v in p["antrieb_je_typ"].items()}
    OUT.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"params.json: {N} Zeilen ausgewertet, {len(p['kategorien'])} Kategorien, {len(p['numerisch'])} numerische Spalten, {len(stich)} Stichtage")


if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("Aufruf: python src/synth/fit.py <echte_datei.csv>")
    main(sys.argv[1])
