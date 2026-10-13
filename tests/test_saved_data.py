"""What the program saves and shows, independent of its language.

The signature of a graph keeps what must not change when keys and option values
change language: node types, icons, sex, degrees, the number of cards and of
their fields. It is taken on the Game of Thrones case study, on the two sample
imports and on three nodes per ontology type, built from the ontology itself
(options by position), so the same test runs before and after a renaming. Labels and ids are left out.

Set QUAESITOR_WRITE_SIGNATURE=1 to rewrite tests/fixtures/data_signature.json.
"""
import base64
import collections
import json
import os
from pathlib import Path

from quaesitor import ontology as onto

ROOT = Path(__file__).resolve().parent.parent
SIGNATURE = Path(__file__).resolve().parent / "fixtures" / "data_signature.json"
SOURCES = ("got_kinship.csv", "got_kinship_hypotheses.csv", "sample_import_it.csv", "sample_import_en.csv")


def _import(client, name):
    data = base64.b64encode((ROOT / "examples" / name).read_bytes()).decode("ascii")
    r = client.post("/api/import/commit", json={"filename": name, "data": data})
    assert r.status_code == 200 and r.get_json()["ok"], r.get_json()


def _fields(ntype, i):
    """A value for every field of the type: options taken by position."""
    out = {}
    for n, f in enumerate(onto.TYPES[ntype]["fields"]):
        if f["type"] == "select" and f["options"]:
            out[f["key"]] = f["options"][(i + n) % len(f["options"])]
        elif f["type"] == "check":
            continue
        elif f["type"] == "number":
            out[f["key"]] = str(3 + n)
        elif f["type"] == "date":
            out[f["key"]] = "2020-01-0%d" % (1 + n % 9)
        else:
            out[f["key"]] = f"V{i}x{n}"
    return out


def _signature(client):
    g = client.get("/api/graph").get_json()
    deg = collections.Counter()
    for e in g["edges"]:
        deg[e["source"]] += 1
        deg[e["target"]] += 1
    nodes = collections.Counter(
        f"{n['ntype']}|{n.get('ficon') or ''}|{n.get('sex') or ''}|{deg[n['id']]}|{len(n.get('records') or [])}"
        f"|{sum(len(r.get('raw') or {}) for r in n.get('records') or [])}"
        for n in g["nodes"])
    return {"nodes": dict(sorted(nodes.items())), "edges": len(g["edges"])}


def _build(client):
    sig = {}
    for name in SOURCES:
        client.post("/api/cases/add", json={"name": name})
        _import(client, name)
        sig[name] = _signature(client)
    client.post("/api/cases/add", json={"name": "ontology"})
    for t in [t for t in onto.TYPES if not t.startswith("ftm")]:
        for i in range(3):
            r = client.post("/api/node/add", json={"kind": t, "ntype": t, "fields": _fields(t, i)})
            assert r.status_code == 200, (t, r.get_json())
    sig["ontology"] = _signature(client)
    return sig


def test_signature_unchanged(qapp):
    _, client = qapp
    sig = _build(client)
    if os.environ.get("QUAESITOR_WRITE_SIGNATURE"):
        SIGNATURE.write_text(json.dumps(sig, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    want = json.loads(SIGNATURE.read_text(encoding="utf-8"))
    for k in want:
        assert sig[k] == want[k], k
