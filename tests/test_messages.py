"""Messages of the server: written in English, translated by the interface (SERVER_MSG in i18n.js)."""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "quaesitor"
# the audio modules keep the Italian messages of Cognitor on purpose (quaesitor/audio/README.md)
SKIP = ("audio", "generated", "ontology_i18n.py")
ITALIAN = re.compile(r"\b(nessun\w*|mancante|fallit\w+|impossibile|trovat[oaie]|caso|nodo|nodi|"
                     r"collegament\w+|della|delle|scegli|almeno|servono|illeggibil\w)\b|\bnon |è|già|più",
                     re.I)


def _sources():
    return [p for p in PKG.rglob("*.py") if not any(s in p.parts or p.name == s for s in SKIP)]


def _message_literals(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = getattr(f, "id", None) or getattr(f, "attr", None) or ""
        owner = getattr(getattr(f, "value", None), "id", "")
        if owner == "logging" or name in ("jsonify", "NodeError", "print") or name.endswith("Error"):
            for c in ast.walk(n):
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    yield c.lineno, c.value


def _server_rows():
    js = (PKG / "static" / "i18n.js").read_text(encoding="utf-8")
    body = re.search(r"const SERVER_MSG_ROWS = (\{.*?\n\});", js, re.S).group(1)
    return json.loads(body)


def test_errors_are_english(qapp):
    _, client = qapp
    r = client.post("/api/node/add", json={"ntype": "phone", "value": "12"})
    assert r.status_code == 400 and r.get_json()["error"] == "invalid phone number"
    r = client.post("/api/cases/add", json={})
    assert r.get_json()["error"] == "case name missing"
    r = client.post("/api/link/add", json={"ids": ["x"]})
    assert r.get_json()["error"] == "at least two nodes are needed"


def test_no_italian_in_messages_and_logs():
    found = []
    for p in _sources():
        for line, s in _message_literals(p):
            if ITALIAN.search(s):
                found.append(f"{p.relative_to(ROOT)}:{line}: {s!r}")
    assert not found, "\n".join(found)


def test_server_messages_are_translated_and_current():
    rows = _server_rows()
    # string constants of the code (adjacent literals already joined by the parser)
    code = "\n".join(c.value for p in _sources() for c in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
                     if isinstance(c, ast.Constant) and isinstance(c.value, str))
    computed = {"invalid latitude", "invalid longitude"}          # f"invalid {what}"
    stale = [en for en in rows if en not in computed and en not in code]
    assert not stale, stale
    for en, tr in rows.items():
        assert len(tr) == 5 and all(tr), en
    src = "\n".join(p.read_text(encoding="utf-8") for p in _sources())
    used = re.findall(r'jsonify\(\{"error": f?"([^"{]+)', src)
    # every literal error of a route is translated (its whole text or its head)
    heads = {u.split(": ")[0].strip() for u in used if re.search(r"[a-z]", u)}
    missing = {h for h in heads if not any(h == k or h.startswith(k + " ") or k.startswith(h) for k in rows)}
    assert missing <= {"this case was written by Quaesitor 1.x and cannot be opened"}, missing
