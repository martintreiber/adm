"""Tier-2-Grader für die Scan-Extraktion: Referenz aus references/reparaturrechnungen.json über den Dateinamen (vars.datei).

Teilpunkte je Feld; Kennzeichen normalisiert; Beträge ± 0,005. promptfoo ruft get_assert(output, context) auf.
"""
import json, re
from pathlib import Path

REFS = {r["datei"]: r for r in json.loads((Path(__file__).resolve().parents[1] / "references" / "reparaturrechnungen.json").read_text(encoding="utf-8"))["rechnungen"]}


def norm_kz(s):
    return re.sub(r"[\s\-]", "", str(s or "")).upper()


def num(x):
    try:
        return float(str(x).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def get_assert(output, context):
    if isinstance(output, str):
        m = re.findall(r"\{[^{}]*\}", output)
        try:
            output = json.loads(m[-1]) if m else {}
        except json.JSONDecodeError:
            output = {}
    ref = REFS.get(context["vars"]["datei"])
    if not ref:
        return {"pass": False, "score": 0, "reason": f"keine Referenz für {context['vars']['datei']}"}
    checks = {
        "rechnungsnr": str(output.get("rechnungsnr") or "").strip() == ref["rechnungsnr"],
        "datum": str(output.get("datum") or "") == ref["datum"],
        "kennzeichen": norm_kz(output.get("kennzeichen")) == norm_kz(ref["kennzeichen"]),
        "netto_eur": num(output.get("netto_eur")) is not None and abs(num(output.get("netto_eur")) - ref["netto_eur"]) < 0.005,
        "brutto_eur": num(output.get("brutto_eur")) is not None and abs(num(output.get("brutto_eur")) - ref["brutto_eur"]) < 0.005,
    }
    score = sum(checks.values()) / len(checks)
    return {"pass": score == 1.0, "score": score, "reason": ", ".join(f"{k}:{'ok' if v else 'falsch'}" for k, v in checks.items())}
