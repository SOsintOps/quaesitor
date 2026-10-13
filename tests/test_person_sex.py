"""Sex of the persons: import column, icon, editor, Follow the Money both ways."""
import base64
import json

import pytest

from quaesitor.normalize import parse_sex

from conftest import wait

CSV = ("name1,type1,sex1,relation,arrow,name2,type2,gender2\n"
       "Eddard Stark,person,M,father of,->,Arya Stark,person,female\n"
       "Eddard Stark,person,M,father of,->,Jon Snow,person,\n")


def _import_csv(client, text):
    data = base64.b64encode(text.encode("utf-8")).decode("ascii")
    r = client.post("/api/import/commit", json={"filename": "kin.csv", "data": data})
    assert r.status_code == 200 and r.get_json()["ok"], r.get_json()


def _node(client, label):
    g = client.get("/api/graph").get_json()
    return next(n for n in g["nodes"] if n["label"] == label)


@pytest.mark.parametrize("value, sex", [("M", "male"), ("f", "female"), ("Femmina", "female"),
                                        ("homme", "male"), ("Weiblich", "female"), ("", ""),
                                        ("?", ""), ("other", "")])
def test_parse_sex(value, sex):
    assert parse_sex(value) == sex


def test_import_sets_sex_and_icon(qapp):
    _, client = qapp
    _import_csv(client, CSV)
    eddard, arya, jon = (_node(client, n) for n in ("Eddard Stark", "Arya Stark", "Jon Snow"))
    assert eddard["sex"] == "male" and eddard["ficon"] == "person-male"
    assert arya["sex"] == "female" and arya["ficon"] == "person-female"
    assert not jon.get("sex") and not jon.get("ficon")      # not known: the icon of the type


def test_editor_sets_and_clears_sex(qapp):
    _, client = qapp
    _import_csv(client, CSV)
    jon = _node(client, "Jon Snow")
    assert client.post("/api/node/sex", json={"id": jon["id"], "sex": "male"}).get_json()["ok"]
    assert _node(client, "Jon Snow")["ficon"] == "person-male"
    client.post("/api/node/sex", json={"id": jon["id"], "sex": ""})
    assert not _node(client, "Jon Snow").get("ficon")


def test_target_keeps_target_icon(qapp):
    _, client = qapp
    _import_csv(client, CSV)
    eddard = _node(client, "Eddard Stark")
    client.post("/api/node/target", json={"id": eddard["id"], "target": True})
    n = _node(client, "Eddard Stark")
    assert n["ntype"] == "target" and n["sex"] == "male" and not n.get("ficon")


def test_ftm_export_and_import_carry_gender(qapp):
    _, client = qapp
    _import_csv(client, CSV)
    lines = client.post("/api/ftm/export", json={}).get_data(as_text=True).splitlines()
    people = {e["properties"]["name"][0]: e for e in map(json.loads, lines) if e["schema"] == "Person"}
    assert people["Arya Stark"]["properties"].get("gender") == ["female"]
    assert "gender" not in people["Jon Snow"]["properties"]
    # back in, in a new case: the gender becomes the sex of the person
    client.post("/api/cases/add", json={"name": "round trip"})
    body = "\n".join(lines).encode("utf-8")
    data = "data:application/json;base64," + base64.b64encode(body).decode()
    assert client.post("/api/ftm/import", json={"data": data, "dataset": "t"}).status_code == 200
    assert not wait(client, "/api/ftm/progress")["error"]
    assert _node(client, "Arya Stark")["ficon"] == "person-female"
