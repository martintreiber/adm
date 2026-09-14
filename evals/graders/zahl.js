// Tier-2-Grader: eine Zahl aus der Antwort lesen und mit Toleranz gegen die Referenz prüfen.
// Aufruf in der YAML: type: javascript, value: file://graders/zahl.js; Referenz und Toleranz kommen aus den vars.
//
// Zahlformate, die das Modell liefern kann, und wie sie gelesen werden:
//   "14547.55"  -> 14547.55   (ein Punkt, nicht drei Nachkommastellen: Dezimalpunkt)
//   "14547,55"  -> 14547.55   (ein Komma: Dezimalkomma)
//   "14.547,55" -> 14547.55   (beides: das hintere Zeichen trennt die Dezimalen)
//   "14,547.55" -> 14547.55
//   "14.547"    -> 14547      (ein Punkt, genau drei Stellen dahinter: Tausenderpunkt)
// Reasoning-Modelle liefern vor der Antwort einen Denktext ("Thinking: ... G123AB ..."); darin stehen Zahlen, die keine
// Antwort sind. Deshalb zählt nur der letzte Absatz der Ausgabe. Diesen Grader selbst prüfen (Tier 3): tests/test_grader.py.

function letzterAbsatz(text) {
  const parts = String(text).trim().split(/\n\s*\n/);
  return parts[parts.length - 1];
}

function parseZahl(text) {
  const m = letzterAbsatz(text).match(/-?\d[\d.,]*/);
  if (!m) return null;
  let t = m[0].replace(/[.,]+$/, "");
  const dot = t.lastIndexOf("."), comma = t.lastIndexOf(",");
  if (dot >= 0 && comma >= 0) {
    t = comma > dot ? t.replace(/\./g, "").replace(",", ".") : t.replace(/,/g, "");
  } else if (comma >= 0) {
    const parts = t.split(",");
    t = parts.length === 2 && parts[1].length !== 3 ? parts[0] + "." + parts[1] : t.replace(/,/g, "");
  } else if (dot >= 0) {
    const parts = t.split(".");
    t = parts.length === 2 && parts[1].length !== 3 ? t : t.replace(/\./g, "");
  }
  const x = parseFloat(t);
  return Number.isFinite(x) ? x : null;
}

module.exports = (output, context) => {
  const ref = parseFloat(context.vars.referenz);
  const tol = context.vars.toleranz !== undefined ? parseFloat(context.vars.toleranz) : 0.02;
  const x = parseZahl(output);
  if (x === null) return { pass: false, score: 0, reason: "keine Zahl in der Antwort" };
  const ok = Math.abs(x - ref) <= Math.abs(ref) * tol;
  return { pass: ok, score: ok ? 1 : 0, reason: `gefunden ${x}, Referenz ${ref}, Toleranz ${tol * 100} %` };
};
module.exports.parseZahl = parseZahl;
module.exports.letzterAbsatz = letzterAbsatz;
