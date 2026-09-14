"""Stufe 1, Beschaffen: Rohdateien unverändert nach data/interim/ kopieren und den Abruf protokollieren."""
import json, shutil
from datetime import date
from config import ROOT, SOURCE, SAMPLE, INTERIM, QUELLEN


def run() -> list:
    INTERIM.mkdir(parents=True, exist_ok=True)
    if SOURCE == SAMPLE:
        print("ACHTUNG: keine Rohdaten in data/raw/ oder data/raw/<datum>/. Die Pipeline läuft auf den Testdaten in data/sample/.")
    files = []
    for name, q in QUELLEN.items():
        src = SOURCE / q["datei"]
        if not src.exists():
            raise SystemExit(f"Quelle '{name}' fehlt: {src}")
        dst = INTERIM / q["datei"]; dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst); files.append(src)
    # "abruf" ist das Datum dieses Laufs. Das Abrufdatum der Quelle gehört in den Ordnernamen data/raw/<datum>/ und in Doku Schritt 1.
    log = {"quelle": str(SOURCE.relative_to(ROOT)), "dateien": {n: q["datei"] for n, q in QUELLEN.items()},
           "groesse_bytes": {n: (SOURCE / q["datei"]).stat().st_size for n, q in QUELLEN.items()}, "lauf": date.today().isoformat()}
    (INTERIM / "provenienz.json").write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"extract: {len(files)} Datei(en) aus {SOURCE.relative_to(ROOT)}")
    return files
