"""Synthetische Belege zur Flotte: Tankkartenabrechnung, Ladekartenrechnung, Reparaturrechnungen. Referenzwerte entstehen mit.

Aufruf:  python src/synth/generate_belege.py [--seed 42]
Liest:   data/sample/flotte_stammdaten.csv (Fahrzeuge), src/synth/params_belege.json (Kalibrierung)
Schreibt: data/sample/belege/tankkarten_2025-03.pdf            Text-PDF, ein Fahrzeug je Seite, wie der Leasinggeber es schickt
          data/sample/belege/ladekarten_2025-01.pdf            Text-PDF, Positionen je Karte und Ladenetz, mit Übertrag über Seiten
          data/sample/belege/reparaturen/RR_01.pdf ... RR_12.pdf   drei Layouts: Karosserie digital + gescannte Zession,
                                                                   Markenwerkstatt als Scan (Nadeldruck), ein Duplikat
          evals/references/tankungen_2025-03.csv, ladungen_2025-01.csv, reparaturrechnungen.json   die Wahrheit hinter den PDFs
          src/synth/fehlerkatalog_belege.md
Braucht pypdfium2 und Pillow für die Scans (kommen mit pdfplumber). Ohne sie entstehen die Reparaturrechnungen als Text-PDF.
"""
import argparse, csv, io, json, random, re
from datetime import date, timedelta
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdfmini import Doc, scan

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
P = json.loads((HERE / "params_belege.json").read_text(encoding="utf-8"))
BELEGE = ROOT / "data" / "sample" / "belege"; REFS = ROOT / "evals" / "references"
FLOTTE = ROOT / "data" / "sample" / "flotte_stammdaten.csv"
KUNDE = ["Beispiel Flotte GmbH", "Musterstraße 1", "1010 Wien"]; KUNDEN_UID = "ATU12345678"
NACH = ["Gruber", "Huber", "Bauer", "Wagner", "Pichler", "Steiner", "Moser", "Hofer", "Leitner", "Berger", "Fuchs", "Eder", "Winkler", "Novak", "Horvath", "Yilmaz"]
VOR = ["Anna", "Julia", "Sabine", "Eva", "Petra", "Thomas", "Michael", "Andreas", "Martin", "Stefan", "Peter", "Daniel", "Lukas", "Georg", "Nina", "Elena"]
STRASSEN = ["Hauptstraße", "Bahnhofstraße", "Lindengasse", "Feldweg", "Schulgasse", "Mühlgasse", "Wiesenweg", "Kirchenplatz"]
ORTE = [("1210", "Wien"), ("8042", "Graz"), ("4020", "Linz"), ("5020", "Salzburg"), ("9020", "Klagenfurt"), ("6020", "Innsbruck"), ("3100", "St. Pölten"), ("2700", "Wr. Neustadt")]
STATIONEN = ["ANNENHEIM", "FELDKIRCHEN", "INNSBRUCK", "EBEN SUED", "HOF", "NEUMARKT/W", "KLAGENFURT", "WELS", "LINZ URFAHR", "GRAZ WEST", "ST. POELTEN", "WR. NEUDORF", "AMSTETTEN", "VILLACH", "BRUCK/MUR"]
fmt = lambda x, d=2: f"{x:,.{d}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")
num = lambda s: float(str(s).replace(" ", "").replace(".", "").replace(",", ".")) if str(s).strip() not in ("", "-") else None
dd = lambda d: d.strftime("%d.%m.%Y")


def q(qd, rng, nd=2):
    qs = sorted((float(k), v) for k, v in qd.items()); u = rng.random()
    for (a, va), (b, vb) in zip(qs, qs[1:]):
        if a <= u <= b: return round(va + (vb - va) * ((u - a) / (b - a) if b > a else 0), nd)
    return round(qs[-1][1], nd)


def weighted(c, rng): ks, ws = zip(*c.items()); return rng.choices(ks, weights=ws)[0]


def person(rng): return f"{rng.choice(VOR)} {rng.choice(NACH)}"


def flotte():
    raw = FLOTTE.read_bytes().decode("latin-1").splitlines(keepends=True)
    rows = list(csv.reader(io.StringIO("".join(raw[2:])), delimiter=";"))
    names = [re.sub(r"\s+", " ", h).strip() for h in rows[0]]
    km_cols = [(n, date(*reversed([int(x) for x in re.search(r"(\d{2})\.(\d{2})\.(\d{4})", n).groups()]))) for n in names if n.startswith("km-Stand per")]
    out = []
    for r in rows[1:]:
        if len(r) != len(names): continue
        d = dict(zip(names, (c.strip() for c in r)))
        if d["Status"] != "aktiv" or "/" in d["Kennzeichen"]: continue
        kz = re.sub(r"[\s\-]", "", d["Kennzeichen"]); m = re.match(r"([A-Z]{1,2})(\d+[A-Z]+)", kz)
        readings = [(dt, num(d[n])) for n, dt in km_cols if num(d[n]) is not None]
        out.append({"kz": f"{m[1]} {m[2]}", "kz_h": f"{m[1]}-{m[2]}", "kz_n": kz, "obj": d["Objektnr."], "marke": d["Marke"],
                    "modell": d["Modell"], "antrieb": d["Antrieb"], "fahrer": d["Fahrer (Nach- und Vorname)"], "kst": d["Kostenstelle"],
                    "vin": d["Fahrgestell-Nr."], "erst": d["Erstzulassung"], "ladekarte": d["Ladekarte Nr."], "readings": readings})
    return out


def km_at(v, when, rng):
    r = [x for x in v["readings"] if x[0] <= when]
    if r: dt, km = r[-1]; return int(km + (when - dt).days / 30.4 * rng.uniform(1500, 3200))
    return rng.randint(5000, 60000)


# ---------------------------------------------------------------- Tankkarten
def tank(veh, rng, fehler):
    T = P["tank"]; start, ende = date(2025, 3, 1), date(2025, 3, 31); beleg_dt = date(2025, 4, 24)
    n_veh = 25
    cand = [v for v in veh if v["antrieb"] in ("D", "B", "H/B", "H/D")]; bev = [v for v in veh if v["antrieb"] == "E"]
    picks = rng.sample(cand, n_veh - 3) + rng.sample(bev, 3)
    refs = []; pages = []
    karten = {"DKV EUROSERVICE": ("2493594", "0000642878934001", "DKV"), "OMV DOWN": ("2492101", "040/6093485", "OMV"), "SHELL": ("2495185", "5002333404", "Shell")}
    for i, v in enumerate(picks):
        lines = []; total = 0.0
        n_t = 0 if v["antrieb"] == "E" else int(weighted({k: w for k, w in T["tankungen_je_fahrzeug"].items()}, rng))
        kraft = "Benzin" if v["antrieb"] in ("B", "H/B") else "Diesel"
        km = km_at(v, start, rng); dates = sorted(start + timedelta(days=rng.randint(0, 30)) for _ in range(n_t))
        for j, dt in enumerate(dates):
            anb = weighted(T["anbieter"], rng); karte, rnr, marke = karten[anb]
            km += rng.randint(150, 1200); liter = q(T["liter_quantile"], rng); preis = q(T["preis_je_liter_quantile"], rng); betrag = round(liter * preis, 2)
            kf = kraft
            if i == 4 and j == 0: kf = "Kraftsto"  # abgeschnittene Bezeichnung wie in der Quelle
            kmtxt = f"{km}km " if rng.random() < T["km_stand_anteil"] else ""
            st = rng.choice(STATIONEN)
            lines.append((anb, dt, karte, f"{kmtxt}{fmt(liter)} Lit {fmt(preis)} {kf} {fmt(betrag)}", f"{marke} {st} / RNr: {rnr}"))
            refs.append(dict(beleg="46/00133", seite=i + 2, kennzeichen=v["kz"], objektnr=v["obj"], datum=dt.isoformat(), anbieter=anb.split()[0], kartennr=karte, station=st, position="Kraftstoff", km_stand=km if kmtxt else "", liter=liter, preis_je_liter=preis, kraftstoff=kf, betrag_eur=betrag))
            total += betrag
            rab = round(betrag * rng.uniform(0.012, 0.022), 2)
            lines.append((anb, dt, karte, f"Tankstellenrabatt {fmt(rab)}-", f"{marke} {st} / RNr: {rnr}"))
            refs.append(dict(beleg="46/00133", seite=i + 2, kennzeichen=v["kz"], objektnr=v["obj"], datum=dt.isoformat(), anbieter=anb.split()[0], kartennr=karte, station=st, position="Tankstellenrabatt", km_stand="", liter="", preis_je_liter="", kraftstoff="", betrag_eur=-rab)); total -= rab
        for pos, quote in T["sonstige_positionen_je_fahrzeug"].items():
            if pos.startswith("Tankstellenrabatt"): continue
            if pos == "E-Ladung Aufschlag" and v["antrieb"] != "E": continue
            n_p = (1 if rng.random() < quote else 0) + (1 if pos == "Maut" and rng.random() < 0.3 else 0)
            for _ in range(n_p):
                betrag = q(T["sonstige_betrag_quantile"][pos], rng); dt = start + timedelta(days=rng.randint(0, 30))
                anb = "DKV EUROSERVICE" if pos != "KFZ-Reinigung" else "OMV DOWN"; karte, rnr, marke = karten[anb]
                st = {"Maut": "ASFINAG", "Bearb.Kosten Tankstelle": "DKV EURO S", "KFZ-Reinigung": rng.choice(STATIONEN), "E-Ladung Aufschlag": "DKV EURO S"}[pos]
                if pos == "Bearb.Kosten Tankstelle": karte, rnr = "2493595", "0000642878934002"
                lines.append((anb, dt, karte, f"{pos} {fmt(betrag)}", f"{marke} {st} / RNr: {rnr}"))
                refs.append(dict(beleg="46/00133", seite=i + 2, kennzeichen=v["kz"], objektnr=v["obj"], datum=dt.isoformat(), anbieter=anb.split()[0], kartennr=karte, station=st, position=pos, km_stand="", liter="", preis_je_liter="", kraftstoff="", betrag_eur=betrag)); total += betrag
        lines.sort(key=lambda l: (l[1], l[3]))
        # eingebaute Fehler
        if i == 7 and lines:
            k = next((j for j, l in enumerate(lines) if " Lit " in l[3]), None)
            if k is not None:
                a, dt, ka, txt, st = lines[k]; m = re.search(r"([\d,]+) Lit ([\d,]+) (\w+) ([\d,]+)$", txt); alt = num(m[4]); neu = round(alt + 3.0, 2)
                lines[k] = (a, dt, ka, txt.replace(m[4], fmt(neu)), st); total += 3.0
                for r_ in refs:
                    if r_["kennzeichen"] == v["kz"] and r_["position"] == "Kraftstoff" and r_["betrag_eur"] == alt: r_["betrag_eur"] = neu; break
                fehler.append(f"Tankkarten, Seite {i + 2}, {v['kz']}: Betrag {fmt(neu)} passt nicht zu Liter × Preis ({m[1]} × {m[2]} = {fmt(alt)}). Die Referenz führt den Belegwert; die Plausibilitätsprüfung muss ihn finden.")
        if i == 11:
            k = next((j for j, l in enumerate(lines) if "km " in l[3]), None)
            if k is not None:
                a, dt, ka, txt, st = lines[k]; m = re.search(r"(\d+)km", txt); falsch = int(m[1]) - 40000
                lines[k] = (a, dt, ka, txt.replace(f"{m[1]}km", f"{max(falsch, 100)}km"), st)
                for r_ in refs:
                    if r_["kennzeichen"] == v["kz"] and r_["km_stand"] == int(m[1]): r_["km_stand"] = max(falsch, 100); break
                fehler.append(f"Tankkarten, Seite {i + 2}, {v['kz']}: Kilometerstand {max(falsch, 100)} liegt unter dem Stand in den Stammdaten und unter den anderen Tankungen des Monats (Tippfehler an der Zapfsäule).")
        kz_show = v["kz_h"] if i == 15 else v["kz"]
        if i == 15: fehler.append(f"Tankkarten, Seite {i + 2}: Kennzeichen als `{kz_show}` geschrieben, in den Stammdaten als `{v['kz']}`.")
        pages.append((v, kz_show, lines, round(total, 2)))
    # Seiten schreiben
    d = Doc(); by_anb = {}
    for v, kz_show, lines, total in pages:
        for a, dt, ka, txt, st in lines:
            key = (a.split()[0], "Kraftstoff-Kosten" if (" Lit " in txt or "rabatt" in txt) else "Sonstige-Kosten")
            m = re.search(r"([\d.,]+)(-?)$", txt); by_anb[key] = round(by_anb.get(key, 0) + num(m[1]) * (-1 if m[2] else 1), 2)
    gesamt = round(sum(by_anb.values()), 2)
    def kopf(d, seite, code, titel):
        y = 800
        for s in [code, "Details auf Datenträger gesendet an:", f"{KUNDE[0]:<40}rechnungen@beispiel-flotte.at", "zH Frau Muster", f"{KUNDE[1]:<50}{seite}", f"{KUNDE[2]} 905305", "alle", f"UID: {KUNDEN_UID} PKW", titel, "9504801013", "ABRECHNUNG FÜR DIE ZEIT 01.03.25 BIS 31.03.25"]:
            d.text(40, y, s, 8.5, "C"); y -= 10.5
        return y
    d.page(); y = kopf(d, 1, "ZSTBE", "L P - Z A H L U N G S B E L E G  Nr. 46/00133 vom 24.04.25")
    fn = {"DKV": "*1)", "SHELL": "*2)", "OMV": "*3)"}
    for (anb, art), val in sorted(by_anb.items()):
        d.text(40, y, f"{anb:<6}{art} PKW Inland".ljust(44) + f"{fmt(val):>12} {fn[anb]}", 8.5, "C"); y -= 10.5
    d.text(40, y, "-" * 50, 8.5, "C"); y -= 10.5; d.text(40, y, "Summe PKW Inland".ljust(44) + f"{fmt(gesamt):>12}", 8.5, "C"); y -= 10.5
    d.text(40, y, "-" * 50, 8.5, "C"); y -= 10.5; d.text(40, y, f"ZAHLBAR BIS ZUM 23.07.25  Gesamtbetrag {fmt(gesamt)} EUR", 8.5, "CB"); y -= 10.5
    d.text(40, y, "OHNE JEDEN ABZUG " + "=" * 45, 8.5, "C"); y -= 21
    for s in ["Zahlungs-Beleg gilt nicht als VSt-abzugsfähiges Dokument.", "*1) Betrag zur Begleichung Ihrer offenen Rechnungen an: DKV", "*2) Betrag zur Begleichung Ihrer offenen Rechnungen an: Shell", "*3) Betrag zur Begleichung Ihrer offenen Rechnungen an: OMV"]:
        d.text(40, y, s, 8.5, "C"); y -= 10.5
    for i, (v, kz_show, lines, total) in enumerate(pages):
        d.page(); y = kopf(d, i + 2, "ZSTAF", "Aufstellung für LP-Zahlungsbeleg zu Nr. 46/00133 vom 24.04.25")
        for s in [f"{kz_show} Obj: {v['obj']} Objekt-KSt.:", f"{v['marke']} {v['modell']}", f"{v['fahrer']} / Kst: {v['kst']}", "-" * 57]:
            d.text(40, y, s, 8.5, "C"); y -= 10.5
        for a, dt, ka, txt, st in lines:
            d.text(40, y, f"{a:<15}{dt.strftime('%Y%m%d')} {ka} {txt}", 8.5, "C"); y -= 10.5
            d.text(40, y, st, 8.5, "C"); y -= 10.5
        d.text(40, y, "-" * 62, 8.5, "C"); y -= 10.5; d.text(40, y, f"Summe Fahrzeug: {kz_show} {fmt(total)}", 8.5, "CB"); y -= 10.5; d.text(40, y, "-" * 62, 8.5, "C")
    d.page(); y = 800
    for s in ["ZSTSO", KUNDE[0], "zH Frau Muster", f"{KUNDE[1]:<50}{len(pages) + 2}", f"{KUNDE[2]} 905305", f"UID: {KUNDEN_UID}   März 2025", "AUFSTELLUNG TANK- und LADEKARTENABRECHNUNG", "ABRECHNUNG FÜR DIE ZEIT 1.03.25 BIS 31.03.25", "", "LeasePlan Zahlungsbeleg", "Lieferant           LPAT-Belegnummer      Betrag"]:
        d.text(40, y, s, 8.5, "C"); y -= 10.5
    for (anb, art), val in sorted(by_anb.items()):
        d.text(40, y, f"{anb + ':':<6}{art} PKW Inland".ljust(38) + "4600133" + f"{fmt(val):>14}", 8.5, "C"); y -= 10.5
    d.text(40, y, "Gesamt:".ljust(45) + f"{fmt(gesamt):>14}", 8.5, "CB"); y -= 21
    d.text(40, y, "Diese Aufstellung ermöglicht einen Summenabgleich je Lieferant und Abrechnungsperiode.", 8.5, "C")
    BELEGE.mkdir(parents=True, exist_ok=True); d.save(BELEGE / "tankkarten_2025-03.pdf")
    with open(REFS / "tankungen_2025-03.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(refs[0].keys())); w.writeheader(); w.writerows(refs)
    fehler.append(f"Tankkarten: Summe je Fahrzeug über alle {len(pages)} Seiten muss den Gesamtbetrag {fmt(gesamt)} EUR auf Seite 1 ergeben; das ist der Abgleich zweier Stellen desselben Belegs.")
    return len(pages) + 2, len(refs), gesamt


# ---------------------------------------------------------------- Ladekarten
def lade(veh, rng, fehler):
    L = P["lade"]; bev = [v for v in veh if v["antrieb"] == "E"]; picks = rng.sample(bev, min(10, len(bev)))
    preise = L["preise_je_netz_klasse_art"]; netze = list(preise.keys()); klassen = L["klassen"]
    codes = {}
    def code(art, kl): return codes.setdefault((art, kl), f"DR{rng.randint(1000, 9999)}")
    refs = []; blocks = []
    for ci, v in enumerate(picks):
        karte = v["ladekarte"] or str(rng.randint(140000, 180000)); kz = v["kz_h"]
        if ci == 6: kz = ""; fehler.append(f"Ladekarten, Kartennr. {karte}: kein Kennzeichen hinter dem Namen; die Karte ist keinem Fahrzeug zuordenbar (in den Stammdaten: {v['kz']}, nur über den Fahrernamen zu finden).")
        if ci == 8: kz = v["kz"]; fehler.append(f"Ladekarten, Kartennr. {karte}: Kennzeichen mit Leerzeichen `{kz}`, sonst überall mit Bindestrich.")
        n_netze = int(weighted({k: w for k, w in L["netze_je_karte"].items() if int(k) <= 6}, rng))
        positions = []
        for netz in rng.sample(netze, min(n_netze, len(netze))):
            kl = weighted({k: w for k, w in klassen.items() if k in preise[netz]}, rng) if any(k in preise[netz] for k in klassen) else rng.choice(list(preise[netz]))
            p_kwh = preise[netz][kl].get("Abgegebene Energie", 0.66); p_block = preise[netz][kl].get("Blockierdauer")
            stk = max(1, int(q(L["ladevorgaenge_quantile"], rng, 0))); kwh = round(q(L["kwh_quantile"], rng) * max(0.5, stk / 3), 2)
            dauer = round(kwh * (rng.uniform(0.6, 1.8) if "über 50" in kl else rng.uniform(1.2, 3.0) if "50kW" in kl else rng.uniform(12, 18) if "3,7" in kl else rng.uniform(4, 9)), 2); block = round(rng.uniform(5, 40), 2) if p_block and rng.random() < 0.5 else 0.0
            frei = round(dauer - block, 2) if block else dauer
            e_betrag = round(kwh * p_kwh, 2); b_betrag = round(block * p_block, 2) if block else 0.0
            positions.append((netz, kl, dauer, block, p_block, frei, stk, kwh, p_kwh, e_betrag, b_betrag))
            refs.append(dict(rechnung="25018707", kartennr=karte, kennzeichen=kz.replace("-", " ") if kz else "", netz=netz, leistungsklasse=kl, ladevorgaenge=stk, ladedauer_min=dauer, blockierdauer_min=block, freiminuten_min=frei, energie_kwh=kwh, preis_je_kwh=p_kwh, betrag_eur=round(e_betrag + b_betrag, 2)))
        blocks.append((ci + 1, karte, person(rng), kz, positions))
    # Seiten
    d = Doc(); seite = [0]; y = [0]; uebertrag = [0.0]; total_pages = 1 + len(blocks) // 2
    def kopf():
        seite[0] += 1; d.page(); yy = 815
        for s, f_ in [("R E C H N U N G", "HB")]:
            d.text(40, yy, f"{s}   25018707 vom 10.03.2025", 9, f_); d.text_right(555, yy, f"Seite {seite[0]} von {total_pages}", 8); yy -= 12
        if seite[0] == 1:
            for s in ["Beispiel Ladenetz GmbH & Co KG · invoice@beispiel-ladenetz.at · T +43 1 000 00 00", "", KUNDE[0], KUNDE[1], KUNDE[2], "", "Rechnungsdatum: 10.03.2025    Kundennummer: 229797    Lieferanten-UID: ATU99999999", f"Rechnungsnummer: 25018707    Vertragsnummer: F90766    Kunden-UID: {KUNDEN_UID}", "Ihr Produkt: Charge & Roam REC 0,31", "Abrechnungszeitraum: 01.01.2025 bis 31.01.2025"]:
                d.text(40, yy, s, 8.5); yy -= 10.5
        d.text(40, yy, "Pos   Art-Nr   Bezeichnung                                    Menge         Preis       Gesamt", 8, "HB"); d.line(40, yy - 3, 555, yy - 3); yy -= 12
        if seite[0] > 1: d.text_right(555, yy, f"Übertrag {fmt(uebertrag[0])} EUR", 8.5, "HI"); yy -= 12
        y[0] = yy
    def fuss():
        d.text_right(555, 60, f"Übertrag {fmt(uebertrag[0])} EUR", 8.5, "HI")
        d.text(40, 40, "Beispiel Ladenetz GmbH & Co KG · Europaplatz 0 · 1150 Wien · FN 000000x · UID: ATU99999999 · IBAN: AT00 0000 0000 0000 0000", 6.5, "H", 0.4)
    def line(s, font="H", right=None, dy=10):
        if y[0] < 80: fuss(); kopf()
        d.text(40, y[0], s, 8.5, font)
        if right is not None: d.text_right(555, y[0], right, 8.5, font)
        y[0] -= dy
    kopf(); netto = 0.0
    for ci, karte, name, kz, positions in blocks:
        line(f"Kartennr. {karte} [{name}, {kz}]", "HB"); line(f"{ci}.2 Nutzung - Partnerladenetze", "HB")
        zs = 0.0; pi = 0
        for netz, kl, dauer, block, p_block, frei, stk, kwh, p_kwh, e_betrag, b_betrag in positions:
            for art, menge, einheit, preis, betrag in [("Ladedauer", dauer, "Min", 0.0, 0.0)] + ([("Blockierdauer", block, "Min", p_block, b_betrag)] if block else []) + [("Freiminuten", frei, "Min", 0.0, 0.0), ("Ladevorgänge", float(stk), "Stk", 0.0, 0.0), ("Abgegebene Energie", kwh, "kWh", p_kwh, e_betrag)]:
                pi += 1
                line(f"{ci:02d}.2.{pi:02d}  {code(art, kl)}   {art} ({kl})", right=f"{fmt(menge)} {einheit}    {fmt(preis, 3)}    {fmt(betrag)} EUR")
                line(netz, "H", dy=11); zs += betrag; uebertrag[0] = round(uebertrag[0] + betrag, 2)
        zs = round(zs, 2)
        if ci == 4: zs = round(zs + 0.01, 2); fehler.append(f"Ladekarten, Kartennr. {karte}: Zwischensumme um 0,01 EUR höher als die Summe der Positionen (Rundung beim Anbieter). Die Referenz führt die Positionen.")
        line(f"Zwischensumme Nutzung - Partnerladenetze", "HB", right=f"{fmt(zs)} EUR"); line(f"Zwischensumme Kartennr. {karte}", "HB", right=f"{fmt(zs)} EUR", dy=14); netto += zs
    netto = round(netto, 2); ust = round(netto * 0.2, 2)
    line("Nettobetrag", "HB", right=f"{fmt(netto)} EUR"); line("+ 20% USt. von " + fmt(netto) + " EUR", right=f"{fmt(ust)} EUR"); line("Rechnungsbetrag", "HB", right=f"{fmt(round(netto + ust, 2))} EUR", dy=14)
    line("Bitte überweisen Sie den Rechnungsbetrag unter Angabe der Rechnungsnummer 25018707. Zahlungsbedingung: 14 Tage.", "H")
    d.text(40, 40, "Beispiel Ladenetz GmbH & Co KG · Europaplatz 0 · 1150 Wien · FN 000000x · UID: ATU99999999", 6.5, "H", 0.4)
    d.save(BELEGE / "ladekarten_2025-01.pdf")
    with open(REFS / "ladungen_2025-01.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(refs[0].keys())); w.writeheader(); w.writerows(refs)
    fehler.append(f"Ladekarten: Der Übertrag am Seitenende muss dem Übertrag am nächsten Seitenanfang gleichen; die Summe aller Zwischensummen je Karte ist der Nettobetrag {fmt(netto)} EUR. Positionen laufen über Seitenenden: Zwischen einer Positionszeile und der Zeile mit dem Ladenetz können Übertrag, Fußzeile und Seitenkopf stehen.")
    return seite[0], len(refs), netto


# ---------------------------------------------------------------- Reparaturrechnungen
SCHAEDEN = [("WSS/Glasbruch erneuern", "Verglasung"), ("Stoßstange hinten lackieren", "Lack"), ("Tür vorne links Parkschaden", "Karosserie"), ("Hagelschaden Dach und Haube", "Karosserie"), ("Felge vorne rechts", "Räder"), ("Außenspiegel rechts ersetzen", "Karosserie")]


def positionen(rng, art):
    aw_satz = rng.choice([16.75, 17.90, 18.50]); aw = rng.randint(12, 40)
    pos = [("AW2", f"{aw}", "Arbeit Spengler", round(aw * aw_satz, 2)), ("NKP", "1", "Nebenkostenpauschale", rng.choice([38.50, 41.60]))]
    teile = {"Verglasung": [("Frontscheibe grün Regen/Licht", (700, 1100)), ("Reparatursatz Scheibe, kalt", (45, 90)), ("Puffer", (1.5, 4)), ("Schallisolierung Frontscheibe", (35, 110))],
             "Lack": [("Stoßfänger hinten grundiert", (250, 480)), ("Lackmaterial", (80, 160)), ("Halter Stoßfänger", (20, 60))],
             "Karosserie": [("Türblech", (300, 600)), ("Kleinteile Tür", (20, 60)), ("Lackmaterial", (80, 160)), ("Dichtung", (30, 70))],
             "Räder": [("Felge 18 Zoll Alu", (280, 520)), ("Ventil", (5, 12)), ("Auswuchten", (15, 25))]}[art]
    for name, (lo, hi) in teile:
        menge = rng.choice([1, 1, 1, 2]); preis = round(rng.uniform(lo, hi), 2)
        pos.append((f"{rng.randint(51300000000, 83199999999)}", str(menge), name, round(menge * preis, 2)))
    pos += [("KLM", "1", "Klein- und Hilfsmaterial", round(rng.uniform(12, 25), 2)), ("ENT", "1", "Entsorgung", round(rng.uniform(12, 22), 2))]
    return pos


def reparaturen(veh, rng, fehler, scans=True):
    out = BELEGE / "reparaturen"; out.mkdir(parents=True, exist_ok=True); refs = []
    picks = rng.sample(veh, 11); layouts = ["A", "B", "A", "B", "B", "A", "B", "A", "B", "A", "B"]
    for k, (v, lay) in enumerate(zip(picks, layouts), 1):
        schaden, art = rng.choice(SCHAEDEN); dt = date(2024, 10, 1) + timedelta(days=rng.randint(0, 270))
        pos = positionen(rng, art); netto = round(sum(p[3] for p in pos), 2); mwst = round(netto * 0.2, 2); brutto = round(netto + mwst, 2)
        sb = rng.choice([350.0, 370.0]); schnr = f"73{rng.randint(20, 75)}/{rng.randint(1000, 44999)}/{dt.year}"; km = km_at(v, dt, rng)
        kz = v["kz"]; fahrer = v["fahrer"]; adr = (f"{rng.choice(STRASSEN)} {rng.randint(1, 99)}", *rng.choice(ORTE))
        ref = dict(datei=f"RR_{k:02d}.pdf", layout={"A": "Karosserie, digital + gescannte Zessionserklärung", "B": "Markenwerkstatt, Scan (Nadeldruck)"}[lay], seiten=2,
                   werkstatt="Karosserie Nord GmbH" if lay == "A" else "Autohaus Süd BMW Service", datum=dt.isoformat(), kennzeichen=kz, fahrgestellnr=v["vin"], km_stand=km,
                   schadensnr=schnr, versicherung="Beispiel Versicherung AG", selbstbehalt=sb, netto_eur=netto, mwst_eur=mwst, brutto_eur=brutto, duplikat_von=None,
                   positionen=[dict(nummer=p[0], menge=p[1], bezeichnung=p[2], betrag_eur=p[3]) for p in pos], unsicherheit="")
        if k == 3: ref["brutto_eur"] = round(brutto + 0.10, 2); fehler.append(f"Reparaturen RR_03: Rechnungsendbetrag {fmt(ref['brutto_eur'])} ist um 0,10 EUR höher als Netto + MwSt. Die Referenz führt den Belegwert.")
        if k == 6: ref["km_stand"] = ""; km = None; fehler.append("Reparaturen RR_06: kein Kilometerstand auf der Rechnung.")
        if k == 9: kz = "W 99999X"; ref["kennzeichen"] = kz; ref["unsicherheit"] = "Kennzeichen nicht in den Stammdaten (Ersatzfahrzeug)"; fehler.append("Reparaturen RR_09: Kennzeichen W 99999X kommt in den Stammdaten nicht vor (Ersatzfahrzeug); die Zuordnung zum Fahrzeug fehlt.")
        if lay == "A": ref["rechnungsnr"] = f"AR25{rng.randint(6000000, 6999999)}"
        else: ref["rechnungsnr"] = f"20-{rng.randint(221000, 239999)}"
        d = Doc(); d.page()
        if lay == "A":
            d.rect(0, 775, 595, 67, (1, 0.93, 0.13)); d.text(40, 800, "DER Spezialist für Lack & Karosserie.", 11, "HB"); d.text_right(555, 800, "www.karosserie-nord.example", 9)
            yy = 720
            for s in ["Reparatur von Karosserieschäden", "Dellen-, Hagel- & Lackreparatur", "Tausch & Reparatur von Windschutzscheiben"]: d.text_right(555, yy, s, 8); yy -= 10
            yy = 640
            for s in ["Herr/Frau", fahrer, adr[0], f"{adr[1]} {adr[2]}"]: d.text(60, yy, s, 9); yy -= 11
            yy = 640
            for s in ["Firma", "Beispiel Versicherung AG", "Musterplatz 1", "1120 Wien"]: d.text(320, yy, s, 9); yy -= 11
            d.text(320, 570, "Rechnung", 12, "HB"); d.text(320, 556, "Rechnungsdatum = Liefer-/Leistungsdatum", 7)
            d.text(320, 540, f"Kundennr.:            {rng.randint(200000, 219999)}", 8, "HI"); d.text(320, 528, f"Rechnung / Datum:    {ref['rechnungsnr']}/{dd(dt)}", 9, "HB")
            d.text(320, 512, f"Auftrag / Datum:      {rng.randint(10100000, 10199999)}/{dd(dt - timedelta(days=rng.randint(0, 5)))}", 8, "HI"); d.text(320, 500, f"Ihr Berater:           {person(rng)}", 8, "HI")
            yy = 528
            for a, b in [("Marke u. Modell:", f"{v['marke']} {v['modell']}"), ("Amtl. Kennzeichen:", kz), ("Fahrgestnr.:", v["vin"]), ("Erstzulassung:", v["erst"]), ("km-Stand", str(km) if km else "")]:
                d.text(60, yy, a, 8); d.text(150, yy, b, 8, "HI"); yy -= 11
            d.text(230, 470, schnr, 8)
            yy = 455; d.line(60, yy + 10, 555, yy + 10); d.text(60, yy, "Nummer", 7, "HI"); d.text(160, yy, "Beschreibung", 7, "HI"); d.text_right(400, yy, "AW/Menge", 7, "HI"); d.text_right(460, yy, "Preis", 7, "HI"); d.text_right(530, yy, "Endpreis EUR", 7, "HI"); d.text_right(555, yy, "Mw-%", 7, "HI"); d.line(60, yy - 3, 555, yy - 3); yy -= 16
            d.text(160, yy, art, 8); yy -= 11
            for n_, menge, bez, betrag in pos:
                d.text(60, yy, n_, 8); d.text(160, yy, bez, 8); d.text_right(400, yy, fmt(float(menge)), 8); d.text_right(460, yy, fmt(betrag / float(menge)), 8); d.text_right(530, yy, fmt(betrag), 8); d.text_right(555, yy, "20", 8); yy -= 11
            yy -= 8; d.line(300, yy + 6, 555, yy + 6)
            d.text(300, yy - 4, "Excl. MWSt.", 8); d.text_right(530, yy - 4, fmt(netto), 8); yy -= 12
            d.text(300, yy - 4, f"MWSt. 20,00 % von {fmt(netto)}", 8); d.text_right(530, yy - 4, fmt(mwst), 8); yy -= 14; d.line(300, yy + 4, 555, yy + 4)
            d.text(300, yy - 6, "Summe Brutto", 9, "HB"); d.text_right(530, yy - 6, fmt(ref["brutto_eur"]), 9, "HB"); yy -= 12; d.line(300, yy - 2, 555, yy - 2)
            d.text(60, 150, "Zahlungskonditionen Ohne Abzug nach Rechnungserhalt", 7); d.text(60, 130, "Wir bedanken uns für Ihr Vertrauen und wünschen Ihnen eine sichere Fahrt!", 8)
            d.text(60, 50, "Karosserie Nord GmbH | A-8054 Graz | Kärntner Straße 0 | UID-Nr.: ATU00000000 | FN 000000x | IBAN: AT00 0000 0000 0000 0000", 6.5, "H", 0.4)
            # Seite 2: Zessionserklärung (wird gescannt)
            d.page(); yy = 780
            d.text(80, yy, "An die", 9); yy -= 22; d.text(80, yy, "Beispiel", 11, "HI"); d.line(150, yy - 2, 330, yy - 2); d.text(340, yy, "Versicherung", 9); yy -= 26
            for a, b in [("Polizzennummer:", ""), ("Schadennummer:", schnr), ("Wagenmarke und Type:", f"{v['marke']} {v['modell'][:24]}"), ("Behördliches Kennzeichen:", kz.replace(" ", "-"))]:
                d.text(80, yy, a, 9); d.text(250, yy, b, 11, "HI"); d.line(240, yy - 2, 420, yy - 2); yy -= 26
            yy -= 10; d.text(230, yy, "ZESSIONSERKLÄRUNG", 15, "HB"); yy -= 40
            for a, b in [("Kunde:", fahrer), ("Adresse:", adr[0]), ("Telefon:", f"0699 / {rng.randint(1000000, 9999999)}"), ("Art des Schadens:", "Kasko")]:
                d.text(80, yy, a, 9); d.text(200, yy, b, 11, "HI"); d.line(190, yy - 2, 480, yy - 2); yy -= 26
            for s in ["Der Reparaturauftrag soll direkt mit der Werkstätte verrechnet werden und ich/wir ersuche(n) um Überweisung an:", "", "                       Karosserie Nord GmbH · Kärntner Straße 0 · A-8054 Graz", "                       Bank: Beispielbank   BIC: BEISATWW   IBAN: AT00 0000 0000 0000 0000", "",
                      "Ich/wir verpflichte(n) mich/uns, der oben angeführten Versicherung jenen Betrag zurückzuerstatten, den diese", "aufgrund unrichtiger oder unvollständiger Darstellung des Unfallganges und dessen Folgen bezahlt hat.", "",
                      "Wird die Bezahlung seitens der Versicherung für eine von mir/uns in Auftrag gegebene Arbeit teilweise oder ganz", "abgelehnt, verpflichte(n) ich/wir mich/uns als Auftraggeber, die Rechnung umgehend zu begleichen."]:
                d.text(80, yy, s, 8); yy -= 12
            yy -= 20; d.text(80, yy, "Leasingfahrzeug:", 9); d.text(400, yy, "ja  O        Nein  X", 9); yy -= 30; d.text(80, yy, "Vorsteuerabzug berechtigt:", 9); d.text(400, yy, "ja  O        Nein  X", 9)
            d.text(80, 120, dd(dt - timedelta(days=rng.randint(10, 40))), 11, "HI"); d.line(80, 116, 200, 116); d.text(80, 105, "Datum", 8); d.text(400, 130, fahrer.split()[-1], 14, "HI"); d.line(380, 116, 560, 116); d.text(380, 105, "Unterschrift des Kunden", 8)
            ref["adressat"] = "Fahrer privat + Versicherung"; ref["unsicherheit"] = (ref["unsicherheit"] + "; " if ref["unsicherheit"] else "") + "Seite 2 (Zession) nur als Scan"
        else:
            def kopfB(titel, seite):
                d.text(60, 810, "AUTOHAUS SÜD", 16, "HB"); d.text(60, 800, "BMW Vertragshändler", 6); d.text_right(555, 808, "BMW Service", 16, "HB"); d.text_right(555, 796, "Kunde", 9)
                d.box(60, 700, 495, 90)
                for x_, y_, a, b in [(63, 780, "Auftrags-Nr.", str(rng.randint(180000, 199999))), (130, 780, "Annahmedatum", (dt - timedelta(days=rng.randint(1, 20))).strftime("%d.%m.%y")), (200, 780, "Auftraggeber", str(rng.randint(100000, 799999))), (340, 780, "Ihr Berater", person(rng)),
                                       (340, 760, titel, ""), (340, 745, "Nummer", f"{ref['rechnungsnr']}   Liefer-/Leist.-Datum {dt.strftime('%d.%m.%y')}   K   30   Seite {seite}"), (63, 765, "Firma", f"{KUNDE[0]}, {KUNDE[1]}, {KUNDE[2]}") if rng.random() < 0.5 else (63, 765, "Frau/Herr", f"{fahrer}, {adr[0]}, {adr[1]} {adr[2]}"),
                                       (63, 725, "Marke", v["marke"]), (200, 725, "Kunden-Nr.", str(rng.randint(100000, 799999))), (340, 725, "Zulassungsdatum", v["erst"]), (450, 725, "KM-Stand", f"{km:,}".replace(",", ".") if km else ""),
                                       (63, 708, "Type", v["modell"][:26]), (200, 708, "Pol.-Kennzeichen", kz), (300, 708, "Fahrgestell-Nr.", v["vin"]), (450, 708, "Motor-Nr.", str(rng.randint(50000000, 69999999)))]:
                    d.text(x_, y_ + 7, a, 5, "H", 0.35); d.text(x_, y_ - 2, b, 8, "C")
                d.text(60, 690, "Nummer            Menge    Bezeichnung                    Einzelpreis         Gesamtpreis MW", 8, "C"); d.text(60, 682, "-" * 100, 8, "C")
            kopfB("R E C H N U N G", 1); yy = 668
            for s in [f"Steuernummer : {KUNDEN_UID}", "Versicherung :  Beispiel Versicherung AG", "Musterplatz 1", "1120  Wien", "Art: K", f"Schadensnr.:        {schnr}", f"Selbstbehalt:          {fmt(sb)}", "", f"Position ----> 01  {schaden}", "                          Kasko Beispiel", f"                          SN:{schnr}", ""]:
                d.text(60, yy, s, 8.5, "C"); yy -= 10.5
            summe_arbeit = 0.0; summe_teile = 0.0
            for n_, menge, bez, betrag in pos:
                d.text(60, yy, f"{n_:<18}{menge:>4}   {bez:<40}", 8.5, "C"); d.text_right(540, yy, f"{fmt(betrag)}  2", 8.5, "C"); yy -= 10.5
                if n_ in ("AW2", "NKP", "KLM", "ENT"): summe_arbeit += betrag
                else: summe_teile += betrag
            yy -= 6; d.text(230, yy, "Summe Position", 8.5, "C"); d.text_right(520, yy, fmt(netto), 8.5, "C"); yy -= 10.5; d.text(230, yy, "-" * 62, 8.5, "C"); yy -= 12
            d.text(300, yy, "Summe Arbeit", 8.5, "C"); d.text_right(520, yy, fmt(round(summe_arbeit, 2)), 8.5, "C"); yy -= 10.5; d.text(300, yy, "Summe Teile", 8.5, "C"); d.text_right(520, yy, fmt(round(summe_teile, 2)), 8.5, "C"); yy -= 16
            d.text(300, yy, "Nettobetrag", 8.5, "C"); d.text_right(520, yy, fmt(netto), 8.5, "C"); yy -= 10.5; d.text(300, yy, f"20 % MWSt       {fmt(netto)} 20,0%", 8.5, "C"); d.text_right(520, yy, f"{fmt(mwst)}  2", 8.5, "C"); yy -= 12
            d.text(300, yy, "-" * 34, 8.5, "C"); yy -= 10.5; d.text(300, yy, "Rechnungsendbetrag       EUR", 8.5, "CB"); d.text_right(520, yy, fmt(ref["brutto_eur"]), 8.5, "CB"); yy -= 10.5; d.text(300, yy, "=" * 34, 8.5, "C"); yy -= 22
            d.text(60, yy, "Zahlbar innerhalb von 30 Tagen ohne Abzug.", 8.5, "C"); yy -= 10.5; d.text(60, yy, f"Bei Überweisung folgenden Code angeben {ref['rechnungsnr'].replace('-', '')} /00{rng.randint(100000, 799999)}", 8.5, "C")
            d.text_right(555, 40, "Fortsetzung auf Seite 2", 8.5, "C"); d.text(20, 300, "Autohaus Süd GmbH · Mühlgasse 0 · A-2380 Beispielsdorf · UID ATU00000000", 5, "H", 0.4)
            d.page(); kopfB("R E C H N U N G", 2); d.text(60, 200, "Wir danken für Ihren Auftrag", 8.5, "C"); d.text(60, 189, "und wünschen eine Gute Fahrt!", 8.5, "C"); d.text(60, 150, f"Erstellt durch: {person(rng)}", 8.5, "C"); d.text_right(555, 40, "Ende des Beleges", 8.5, "C")
            ref["adressat"] = "Firma oder Fahrer privat"; ref["unsicherheit"] = (ref["unsicherheit"] + "; " if ref["unsicherheit"] else "") + "nur als Scan, Nadeldruck"
        tmp = out / f"_tmp_{k:02d}.pdf"; d.save(tmp)
        final = out / f"RR_{k:02d}.pdf"
        if scans:
            if lay == "B": scan(tmp, final, seed=k, contrast=0.7, noise=20)
            else:
                # Seite 1 digital, Seite 2 gescannt: zusammenführen
                import pypdfium2 as pdfium
                s2 = out / f"_tmp_{k:02d}_s2.pdf"; scan(tmp, s2, seed=k)
                src = pdfium.PdfDocument(str(tmp)); sc = pdfium.PdfDocument(str(s2)); new = pdfium.PdfDocument.new()
                new.import_pages(src, [0]); new.import_pages(sc, [1]); new.save(str(final)); s2.unlink()
        else: tmp.replace(final)
        if tmp.exists(): tmp.unlink()
        refs.append(ref)
        if lay == "B" and k == 5:
            # Duplikat als 12. Beleg: dieselbe Rechnung, einseitig, anderes Layoutmerkmal
            d2 = Doc(); d2.page(); ref2 = dict(ref); ref2["datei"] = "RR_12.pdf"; ref2["seiten"] = 1; ref2["duplikat_von"] = "RR_05.pdf"; ref2["layout"] = "Markenwerkstatt, Scan, RECHNUNG - DUPLIKAT"
            d2.text(60, 810, "AUTOHAUS SÜD", 16, "HB"); d2.text_right(555, 808, "BMW Service", 16, "HB"); d2.text(340, 770, "RECHNUNG - DUPLIKAT", 9, "CB"); d2.text(340, 755, f"Nummer {ref['rechnungsnr']}   {dt.strftime('%d.%m.%y')}   K   30   Seite 1", 8, "C")
            d2.text(63, 765, f"{fahrer}, {adr[0]}, {adr[1]} {adr[2]}", 8, "C"); d2.text(63, 725, f"Marke {v['marke']}   Type {v['modell'][:26]}   Pol.-Kennzeichen {kz}   Fahrgestell-Nr. {v['vin']}   KM-Stand {km if km else ''}", 8, "C")
            yy = 700
            for s in ["Versicherung :  Beispiel Versicherung AG, Musterplatz 1, 1120 Wien", "Art: K", f"Schadensnr.:        {schnr}", f"Selbstbehalt:          {fmt(sb)}", "", f"Position ----> 01  {schaden}", ""]:
                d2.text(60, yy, s, 8.5, "C"); yy -= 10.5
            for n_, menge, bez, betrag in pos: d2.text(60, yy, f"{n_:<18}{menge:>4}   {bez:<40}", 8.5, "C"); d2.text_right(540, yy, f"{fmt(betrag)}  2", 8.5, "C"); yy -= 10.5
            yy -= 8; d2.text(300, yy, "Nettobetrag", 8.5, "C"); d2.text_right(520, yy, fmt(netto), 8.5, "C"); yy -= 10.5; d2.text(300, yy, "20 % MWSt", 8.5, "C"); d2.text_right(520, yy, fmt(mwst), 8.5, "C"); yy -= 12
            d2.text(300, yy, "Rechnungsendbetrag       EUR", 8.5, "CB"); d2.text_right(520, yy, fmt(ref["brutto_eur"]), 8.5, "CB"); d2.text_right(555, 40, "Ende des Beleges", 8.5, "C")
            t2 = out / "_tmp_12.pdf"; d2.save(t2)
            if scans: scan(t2, out / "RR_12.pdf", seed=12, contrast=0.75, noise=18); t2.unlink()
            else: t2.replace(out / "RR_12.pdf")
            refs.append(ref2); fehler.append("Reparaturen RR_12: Duplikat von RR_05 (dieselbe Rechnungsnummer, derselbe Betrag), als 'RECHNUNG - DUPLIKAT' gekennzeichnet. Zählt einmal.")
    refs.sort(key=lambda r: r["datei"])
    (REFS / "reparaturrechnungen.json").write_text(json.dumps({"quelle": "beim Erzeugen mitgeschrieben (src/synth/generate_belege.py), 14.09.2026", "hinweis": "Werte sind die Belegwerte; wo der Beleg in sich widersprüchlich ist, steht es im Fehlerkatalog", "rechnungen": refs}, ensure_ascii=False, indent=1), encoding="utf-8")
    fehler.append("Reparaturen: Fahrername und Privatadresse stehen auf mehreren Rechnungen (Adressat, Zessionserklärung). Vor einer Extraktion mit einem Cloud-Modell sind sie zu maskieren oder die Rechnungen laufen lokal.")
    return len(refs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=42); ap.add_argument("--no-scans", action="store_true"); a = ap.parse_args()
    rng = random.Random(a.seed); veh = flotte(); fehler = []
    ts, tn, tg = tank(veh, random.Random(a.seed + 1), fehler)
    ls, ln, lnetto = lade(veh, random.Random(a.seed + 2), fehler)
    rn = reparaturen(veh, random.Random(a.seed + 3), fehler, scans=not a.no_scans)
    (HERE / "fehlerkatalog_belege.md").write_text("# Fehlerkatalog · Belege (Tank, Laden, Reparaturen)\n\n"
        f"Erzeugt von `src/synth/generate_belege.py --seed {a.seed}`. Tankkarten: {ts} Seiten, {tn} Positionen, Gesamt {fmt(tg)} EUR. Ladekarten: {ls} Seiten, {ln} Positionen, Netto {fmt(lnetto)} EUR. Reparaturen: {rn} Belege.\n"
        "Die Referenzen in `evals/references/` sind beim Erzeugen entstanden; sie sind die Wahrheit, gegen die eine Extraktion geprüft wird.\n\n" + "\n".join(f"- {x}" for x in fehler) + "\n", encoding="utf-8")
    print(f"tankkarten: {ts} Seiten / {tn} Referenzzeilen · ladekarten: {ls} Seiten / {ln} Referenzzeilen · reparaturen: {rn} Belege · fehlerkatalog_belege.md: {len(fehler)} Einträge")
