"""Tier-2-Grader: Felder mit Toleranzen vergleichen, Teilpunkte, Kennzeichen normalisiert.

promptfoo ruft get_assert(output, context) auf. context["vars"] enthält die Eingabe,
die Referenz kommt aus references/beispiel_extraktion.json über die Rechnungsnummer.
Diesen Grader selbst prüfen (Tier 3): ein Fall, der bestehen muss, einer, der scheitern muss.
"""
import json, re
from pathlib import Path

REFS = json.loads((Path(__file__).resolve().parents[1] / "references" / "beispiel_extraktion.json").read_text(encoding="utf-8"))


def norm_kz(s):
    return re.sub(r"[\s\-]", "", str(s or "")).upper()


def get_assert(output, context):
    if isinstance(output, str):
        m = re.search(r"\{[\s\S]*\}", output)
        output = json.loads(m.group(0)) if m else {}
    ref = next((r["erwartet"] for r in REFS if r["erwartet"]["rechnungsnr"] == output.get("rechnungsnr")), None)
    if not ref:
        return {"pass": False, "score": 0, "reason": f"keine Referenz für {output.get('rechnungsnr')}"}
    checks = {
        "rechnungsnr": output.get("rechnungsnr") == ref["rechnungsnr"],
        "datum": output.get("datum") == ref["datum"],
        "kennzeichen": norm_kz(output.get("kennzeichen")) == norm_kz(ref["kennzeichen"]),
        "netto_eur": abs(float(output.get("netto_eur") or 0) - ref["netto_eur"]) < 0.005,
    }
    score = sum(checks.values()) / len(checks)
    return {"pass": score == 1.0, "score": score, "reason": ", ".join(f"{k}:{'ok' if v else 'falsch'}" for k, v in checks.items())}
