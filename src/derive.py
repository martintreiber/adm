"""Stufe 4, Ableiten: Kennzahlen als SQL ausführen und als CSV ablegen. Das Modell rechnet nicht."""
import sqlite3
import pandas as pd
from config import DB, SQL, PROCESSED


def run() -> dict:
    con = sqlite3.connect(DB)
    results = {}
    for q in sorted(SQL.glob("kennzahl_*.sql")):
        df = pd.read_sql_query(q.read_text(encoding="utf-8"), con)
        out = PROCESSED / f"{q.stem}.csv"
        df.to_csv(out, index=False)
        results[q.stem] = df
        print(f"derive: {q.name} -> {out.name} ({len(df)} Zeilen)")
    con.close()
    return results
