"""Scans als Bilder für das Modell: erste Seite jeder Reparaturrechnung als PNG nach data/interim/scans/.

Aufruf: python src/scans_rendern.py            (nach python src/run.py; braucht pypdfium2, kommt mit pdfplumber)
Die PNGs sind die Eingabe für evals/extraktion_scans.yaml. Sie enthalten Fahrernamen und Privatadressen:
nur an ein lokales Modell schicken, oder vorher maskieren.
"""
from pathlib import Path
import pypdfium2 as pdfium
from config import SOURCE, INTERIM

QUELLE = SOURCE / "belege" / "reparaturen"
ZIEL = INTERIM / "scans"


def run(dpi: int = 110) -> list:
    ZIEL.mkdir(parents=True, exist_ok=True)
    out = []
    for pdf_path in sorted(QUELLE.glob("RR_*.pdf")):
        page = pdfium.PdfDocument(str(pdf_path))[0]
        png = ZIEL / f"{pdf_path.stem}.png"
        page.render(scale=dpi / 72).to_pil().convert("RGB").save(png, optimize=True)
        out.append(png)
    print(f"scans: {len(out)} PNG in {ZIEL.relative_to(INTERIM.parent.parent)} ({dpi} dpi)")
    return out


if __name__ == "__main__":
    run()
