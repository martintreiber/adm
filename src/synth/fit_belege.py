"""Kalibrierung für Tank- und Ladebelege: liest die echten PDFs (nur lokal) und schreibt Aggregate nach params_belege.json.

Aufruf:  python src/synth/fit_belege.py <tankkarten.pdf> <ladekarten.pdf>

Es landen nur Häufigkeiten, Quantile und Preislisten in der Datei: keine Kennzeichen, Karten-, Objekt- oder
Rechnungsnummern, keine Namen, keine Stationsnamen, kein Kunde.
"""
import json, re, sys
from collections import Counter
from pathlib import Path
import pdfplumber

OUT = Path(__file__).resolve().parent / "params_belege.json"
num = lambda s: float(s.replace(".", "").replace(",", "."))


def quant(xs, qs=(0, 0.1, 0.25, 0.5, 0.75, 0.9, 1)):
    xs = sorted(xs)
    if not xs: return None
    out = {}
    for q in qs:
        k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1)
        out[str(q)] = round(xs[f] + (xs[c] - xs[f]) * (k - f), 4)
    return out


def text(path):
    with pdfplumber.open(path) as pdf:
        return [p.extract_text() or "" for p in pdf.pages]


def tank(path):
    pages = text(path); t = "\n".join(pages)
    veh = re.findall(r"^[A-Z]{1,2} ?\d{2,5}[A-Z]{1,2} Obj: \d+", t, re.M)
    lines = re.findall(r"^(DKV EUROSERVICE|SHELL|OMV DOWN)\s?(\d{8}) \d+ (?:(\d+)km )?([\d.,]+) Lit ([\d,]+) (\w+) ([\d.,]+)$", t, re.M)
    per = Counter(); cur = None; sonst = Counter(); sonst_val = {}
    for l in t.splitlines():
        if re.match(r"^[A-Z]{1,2} ?\d{2,5}[A-Z]{1,2} Obj:", l): cur = l.split(" Obj")[0]
        elif cur and " Lit " in l: per[cur] += 1
        m = re.match(r"^(?:DKV EUROSERVICE|SHELL|OMV DOWN)\s?\d{8} \d+ ((?!\d)[A-Za-z.\- ]+?) ([\d.,]+)(-?)$", l)
        if m: sonst[m[1]] += 1; sonst_val.setdefault(m[1], []).append(num(m[2]) * (-1 if m[3] else 1))
    tank_sum = [num(x) for x in re.findall(r"Summe Fahrzeug: [A-Z0-9 ]+ ([\d.,]+)", t)]
    return {"seiten": len(pages), "fahrzeuge": len(veh), "tankungen": len(lines),
            "tankungen_je_fahrzeug": dict(Counter(per.values())),
            "anbieter": dict(Counter(l[0].strip() for l in lines)), "kraftstoff": dict(Counter(l[5] for l in lines)),
            "liter_quantile": quant([num(l[3]) for l in lines]), "preis_je_liter_quantile": quant([num(l[4]) for l in lines]),
            "km_stand_anteil": round(sum(1 for l in lines if l[2]) / len(lines), 3),
            "sonstige_positionen_je_fahrzeug": {k: round(v / len(veh), 3) for k, v in sonst.items()},
            "sonstige_betrag_quantile": {k: quant(v) for k, v in sonst_val.items()},
            "summe_je_fahrzeug_quantile": quant(tank_sum)}


def lade(path):
    pages = text(path); t = "\n".join(pages)
    cards = re.findall(r"Kartennr\. \d+ \[", t)
    pos = re.findall(r"^(\d\d\.\d\.\d\d) (DR\d+) (.+?) \(([^)]+)\) ([\d.,]+) (Min|Stk|kWh) ([\d,]+) ([\d.,]+) EUR\n(.+)$", t, re.M)
    preise = {}
    for p in pos:
        if p[6] != "0,000": preise.setdefault(p[8], {}).setdefault(p[3], {})[p[2]] = num(p[6])
    # je Karte: Anzahl Netze; je (Karte, Netz, Klasse): kWh, Ladevorgänge, Minuten
    blocks = re.split(r"Kartennr\. \d+ \[", t)[1:]
    netze_je_karte = [len(set(re.findall(r"EUR\n(.+)$", b, re.M))) for b in blocks]
    kwh = [num(p[4]) for p in pos if p[5] == "kWh"]; stk = [num(p[4]) for p in pos if p[5] == "Stk"]
    dauer = [num(p[4]) for p in pos if p[2] == "Ladedauer"]
    ratio = [d / k for d, k in zip(dauer, kwh) if k]
    tot = re.findall(r"Nettobetrag ([\d.,]+) EUR", t)
    return {"seiten": len(pages), "karten": len(cards), "positionen": len(pos),
            "netze": dict(Counter(p[8] for p in pos)), "klassen": dict(Counter(p[3] for p in pos)),
            "arten": dict(Counter(p[2] for p in pos)), "preise_je_netz_klasse_art": preise,
            "netze_je_karte": dict(Counter(netze_je_karte)), "kwh_quantile": quant(kwh), "ladevorgaenge_quantile": quant(stk),
            "min_je_kwh_quantile": quant(ratio), "blockier_anteil": round(sum(1 for p in pos if p[2] == "Blockierdauer") / max(1, len(cards)), 3),
            "netto_gesamt": num(tot[-1]) if tot else None}


if __name__ == "__main__":
    if len(sys.argv) != 3: raise SystemExit("Aufruf: python src/synth/fit_belege.py <tankkarten.pdf> <ladekarten.pdf>")
    p = {"quelle": "Tankkartenabrechnung (Leasinggeber) und Ladekartenrechnung (Ladenetzbetreiber), je ein Monat; aggregiert",
         "tank": tank(sys.argv[1]), "lade": lade(sys.argv[2])}
    OUT.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"params_belege.json: Tank {p['tank']['fahrzeuge']} Fahrzeuge / {p['tank']['tankungen']} Tankungen; Lade {p['lade']['karten']} Karten / {p['lade']['positionen']} Positionen")
