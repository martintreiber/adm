"""Die Pipeline in ihrer Reihenfolge. Aufruf: python src/run.py

Beschaffen -> Bereinigen (je Quelle) -> Integrieren -> Ableiten.
Läuft beliebig oft mit gleichem Ergebnis (siehe tests/test_pipeline.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract, clean, integrate, derive  # noqa: E402

if __name__ == "__main__":
    extract.run()
    clean.run()
    integrate.run()
    derive.run()
    print("fertig")
