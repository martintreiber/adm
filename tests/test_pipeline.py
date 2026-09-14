"""Robustheitsnachweis: die Pipeline läuft zweimal und liefert zweimal dasselbe; keine Tabelle hat doppelte Schlüssel."""
import hashlib, sqlite3, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import DB  # noqa: E402  # data/processed/<PROJEKT>.sqlite, Name in src/config.py


def _tables(con):
    return [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]


def _dump() -> str:
    """Hash über alle Tabellen, sortiert; unabhängig von Tabellennamen, damit der Test eure Umbenennungen überlebt."""
    con = sqlite3.connect(DB); h = hashlib.sha256()
    for t in _tables(con):
        for row in con.execute(f"SELECT * FROM {t} ORDER BY 1, 2"):
            h.update(repr(row).encode())
    con.close()
    return h.hexdigest()


def _run():
    subprocess.run([sys.executable, str(ROOT / "src" / "run.py")], check=True, cwd=ROOT)


def test_pipeline_is_idempotent():
    _run(); first = _dump()
    _run(); second = _dump()
    assert first == second


def test_primary_keys_are_unique():
    assert DB.exists(), "erst python src/run.py"
    con = sqlite3.connect(DB)
    for t in _tables(con):
        pk = [r[1] for r in con.execute(f"PRAGMA table_info({t})") if r[5] > 0]
        if not pk: continue
        cols = ", ".join(pk)
        n, distinct = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT {cols}) FROM {t}" if len(pk) == 1 else
                                  f"SELECT COUNT(*), (SELECT COUNT(*) FROM (SELECT DISTINCT {cols} FROM {t})) FROM {t}").fetchone()
        assert n == distinct, f"{t}: doppelte Schlüssel"
    con.close()


def test_every_vehicle_in_belegen_is_known_or_counted():
    """Belege ohne Fahrzeug dürfen vorkommen, aber nur als NULL, nie als erfundene Zuordnung."""
    con = sqlite3.connect(DB)
    bad = con.execute("SELECT COUNT(*) FROM tankung t LEFT JOIN fahrzeug f ON f.objektnr = t.objektnr WHERE t.objektnr IS NOT NULL AND f.objektnr IS NULL").fetchone()[0]
    con.close()
    assert bad == 0
