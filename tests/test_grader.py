"""Tier 3: den Grader selbst prüfen. Ein Fall, der bestehen muss, einer, der scheitern muss, je Zahlformat."""
import json, subprocess, shutil
from pathlib import Path
import pytest

GRADER = Path(__file__).resolve().parents[1] / "evals" / "graders" / "zahl.js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node nicht installiert")


def grade(answer: str, referenz: float, toleranz: float = 0.02) -> dict:
    js = f"const g=require({json.dumps(str(GRADER))});console.log(JSON.stringify(g({json.dumps(answer)},{{vars:{{referenz:{referenz},toleranz:{toleranz}}}}})))"
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)


@pytest.mark.parametrize("answer", ["14547.55", "14547,55", "14.547,55", "14,547.55", "Die Summe ist 14.547,55 EUR.",
                                    "Thinking: Der Nutzer fragt nach G123AB, Zeile 16 in der Tabelle.\n\n14547.55"])
def test_richtige_antwort_besteht(answer):
    assert grade(answer, 14547.55)["pass"], answer


@pytest.mark.parametrize("answer", ["1454755", "145.47", "keine Ahnung", "3832,23"])
def test_falsche_antwort_scheitert(answer):
    assert not grade(answer, 14547.55)["pass"], answer
