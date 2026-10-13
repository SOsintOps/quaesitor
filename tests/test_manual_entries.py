"""Nodes added by hand: the entry and its card are saved with English keys."""
import json
import re

from quaesitor import store
from quaesitor.ontology import FIELD_ALIASES

ITALIAN = set(FIELD_ALIASES) | {"cognome", "nascita", "colore", "civico", "citta", "manuale", "sesso",
                                "nota", "testo", "valore", "aggiunto_il", "latitudine", "longitudine"}


def _add(client, **body):
    r = client.post("/api/node/add", json=body)
    assert r.status_code == 200, r.get_json()
    return r.get_json()


def _saved_entries():
    return [json.loads(r["data"]) for r in store.conn().execute("SELECT data FROM ann_added")]


def _words(obj):
    """Every key of a saved entry, and the value of 'rel'."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            if k == "rel":
                out.add(v)
            out |= _words(v)
    return out


def test_person_place_vehicle(qapp):
    _, client = qapp
    p = _add(client, ntype="name", surname="Stark", given_name="Arya", birth="1999-03-12", sex="female")
    assert p["node"]["label"] == "Stark Arya (12/03/1999)"
    raw = p["node"]["records"][0]["raw"]
    assert raw["Surname"] == "Stark" and raw["Given name"] == "Arya" and raw["Date of birth"] == "12/03/1999"
    assert raw["Sex"] == "female" and p["node"]["records"][0]["collection"] == "added by hand"
    pl = _add(client, ntype="place", value="Winterfell", address="Via del Lupo", house_number="7",
              parent=p["id"])
    raw = pl["node"]["records"][0]["raw"]
    assert raw["City"] == "Winterfell" and raw["Address"] == "Via del Lupo" and raw["House number"] == "7"
    assert pl["edge"]["rel"] == "manual"
    v = _add(client, ntype="vehicle", value="ab 123 cd", color="white")
    assert v["node"]["records"][0]["raw"]["Colour"] == "White"
    for e in _saved_entries():
        assert not (_words(e) & ITALIAN), _words(e) & ITALIAN


def test_same_address_is_one_place(qapp):
    _, client = qapp
    a = _add(client, ntype="place", value="Brescia", address="Via Roma", house_number="12")
    b = _add(client, ntype="place", value="Brescia", address="Via Roma 12")
    assert a["id"] == b["id"] and b.get("record")


def test_import_columns_in_italian_and_english(qapp):
    import base64
    _, client = qapp
    csv = ("nome1;tipo1;nascita1;collegamento;nome2;tipo2;indirizzo2;civico2\n"
           "Rossi Mario;persona;12/03/1980;residenza;Brescia;luogo;Via Roma;12\n")
    data = base64.b64encode(csv.encode()).decode()
    assert client.post("/api/import/commit", json={"filename": "it.csv", "data": data}).get_json()["ok"]
    for e in _saved_entries():
        assert not (_words(e) & ITALIAN), _words(e) & ITALIAN
    g = client.get("/api/graph").get_json()
    place = next(n for n in g["nodes"] if n["ntype"] == "place")
    assert re.search(r"Via Roma", place["label"])


def test_link_names_are_english(qapp):
    _, client = qapp
    a = _add(client, ntype="place", value="Brescia", address="Via Roma", house_number="12")
    b = _add(client, ntype="place", value="Brescia", address="Via Roma", house_number="14")
    p = _add(client, ntype="name", surname="Rossi", given_name="Mario")
    r = client.post("/api/link/add", json={"ids": [p["id"], a["id"]]})
    assert r.status_code == 200, r.get_json()
    edges = client.get("/api/graph").get_json()["edges"]
    rels = {e["rel"] for e in edges}
    assert "manual_link" in rels
    street = next(e for e in edges if e["rel"] == "same_street")
    assert {street["source"], street["target"]} == {a["id"], b["id"]} and street["label"] == "same street"


def test_import_template_of_the_page_imports(qapp):
    """The template offered by the import wizard (app.js) is read by the import as it is."""
    import base64
    from pathlib import Path
    _, client = qapp
    js = (Path(__file__).resolve().parent.parent / "quaesitor" / "static" / "app.js").read_text(encoding="utf-8")
    block = re.search(r"const IMPORT_TEMPLATE = (\[.*?\n\]);", js, re.S).group(1)
    rows = json.loads(block.replace("'", '"'))
    csv = "\n".join(";".join(r) for r in rows) + "\n"
    data = base64.b64encode(csv.encode()).decode()
    j = client.post("/api/import/commit", json={"filename": "import_template.csv", "data": data}).get_json()
    assert j["ok"], j
    g = client.get("/api/graph").get_json()
    types = {n["ntype"] for n in g["nodes"]}
    assert {"name", "phone", "account", "email", "link", "place", "vehicle"} <= types
    styles = {(e.get("lstyle"), e.get("curve")) for e in g["edges"]}
    assert ("dashed", "unbundled-bezier") in styles
