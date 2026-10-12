"""Follow the Money import: the defects fixed on 2026-10-12 for the Cognitor bundle."""
import json

import ftm

from conftest import wait


def _ents(*items):
    return {e["id"]: e for e in items}


def _person(i, name, **props):
    return {"id": i, "schema": "Person", "properties": dict(name=[name], **props)}


def _import(client, entities):
    body = "".join(json.dumps(e) + "\n" for e in entities).encode("utf-8")
    import base64
    data = "data:application/json;base64," + base64.b64encode(body).decode()
    r = client.post("/api/ftm/import", json={"data": data, "dataset": "t"})
    assert r.status_code == 200, r.get_json()
    st = wait(client, "/api/ftm/progress")
    assert not st["error"], st
    return st


def _graph(client):
    return client.get("/api/graph").get_json()


def test_every_node_entity_has_its_own_row():
    """A Person reached only through Image.pictured kept no row of its own: when the
    Image row failed, the Person vanished."""
    ents = _ents(_person("p1", "Mario Rossi"),
                 {"id": "i1", "schema": "Image", "properties": {"fileName": ["x.jpg"], "pictured": ["p1"]}})
    table = ftm.rows_from_entities(ents, native_types=set())
    head = table[0]
    names = [r[head.index("name1")] for r in table[1:]]
    assert names == ["Mario Rossi"]          # the Image without its file is left out, with its link


def test_image_with_its_file_becomes_a_photo_linked_to_the_person():
    ents = _ents(_person("p1", "Mario Rossi"),
                 {"id": "i1", "schema": "Image", "properties": {"fileName": ["media/a.jpg"], "title": ["face"],
                                                                "pictured": ["p1"]}})
    table = ftm.rows_from_entities(ents, native_types=set(), media={"media/a.jpg": "media/cognitor/c/a.jpg"})
    head = table[0]
    rows = [dict(zip(head, r)) for r in table[1:]]
    photo = [r for r in rows if r["type1"] == "photo" and not r.get("relation")]
    assert photo and photo[0]["name1"] == "media/cognitor/c/a.jpg" and photo[0]["label1"] == "face"
    link = [r for r in rows if r.get("relation") == "pictured"]
    assert link and link[0]["name2"] == "Mario Rossi"


def test_native_types_keep_body_text_and_description(qapp):
    _, client = qapp
    body = "x" * 5000
    _import(client, [{"id": "v1", "schema": "Video", "properties": {
        "fileName": ["clip.mp4"], "title": ["clip.mp4"], "duration": ["31"], "bodyText": [body],
        "description": ["a video"], "summary": ["first"], "notes": ["second"]}}])
    g = _graph(client)
    (v,) = [n for n in g["nodes"] if n.get("ntype") == "video"]
    raw = {k: v_ for r in v.get("records") or [] for k, v_ in (r.get("raw") or {}).items()}
    assert raw.get("bodyText") == body
    assert any("a video" == str(x) for x in raw.values())
    assert "first" in str(v.get("note")) and "second" in str(v.get("note"))


def test_reserved_free_columns_do_not_override_fixed_ones(qapp):
    _, client = qapp
    _import(client, [_person("p1", "Mario Rossi", title=["Dr."], nationality=["it"]),
                     {"id": "veh", "schema": "Vehicle", "properties": {
                         "registrationNumber": ["AB123CD"], "type": ["car"]}}])
    g = _graph(client)
    labels = {n.get("label") for n in g["nodes"]}
    assert "Mario Rossi" in labels and "Dr." not in labels
    assert any(n.get("ntype") == "vehicle" for n in g["nodes"])


def test_partial_birth_date_does_not_drop_the_person(qapp):
    _, client = qapp
    st = _import(client, [_person("p1", "Anna Neri", birthDate=["1980"])])
    assert st["errors"] == 0
    assert any(n.get("label") == "Anna Neri" for n in _graph(client)["nodes"])


def test_reimport_does_not_duplicate(qapp):
    _, client = qapp
    ents = [_person("p1", "Mario Rossi"), _person("p2", "Anna Neri"),
            {"id": "a1", "schema": "Associate", "properties": {
                "person": ["p1"], "associate": ["p2"], "relationship": ["seen together"],
                "summary": ["3 photos, 1 video segments"]}}]
    _import(client, ents)
    g1 = _graph(client)
    _import(client, ents)
    g2 = _graph(client)
    assert len(g1["nodes"]) == len(g2["nodes"]) and len(g1["edges"]) == len(g2["edges"])
    seen = [e for e in g2["edges"] if e.get("evid") == "seen"]
    assert len(seen) == 1 and seen[0]["seen_n"] == 4
