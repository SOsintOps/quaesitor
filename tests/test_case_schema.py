"""Schema version of the cases: a case written by 1.x (Italian keys) is not opened."""
import sqlite3

from quaesitor import store


def _make_old(cid):
    """Turns a case into one written by 1.x: data and no schema version."""
    c = sqlite3.connect(store._case_file(cid))
    c.execute("DELETE FROM meta WHERE key = 'schema_version'")
    c.execute("INSERT INTO ann_added(id, seq, data) VALUES('x', 1, '{\"id\": \"x\", \"rel\": \"manuale\"}')")
    c.commit()
    c.close()


def test_new_case_has_the_current_version(qapp):
    _, client = qapp
    assert store.get_meta("schema_version") == str(store.SCHEMA_VERSION)
    assert not any(c["old"] for c in client.get("/api/cases").get_json()["items"])


def test_old_case_is_listed_and_refused(qapp):
    _, client = qapp
    old = client.post("/api/cases/add", json={"name": "old one"}).get_json()["case"]["id"]
    client.post("/api/cases/add", json={"name": "new one"})
    _make_old(old)
    items = {c["id"]: c for c in client.get("/api/cases").get_json()["items"]}
    assert items[old]["old"]
    r = client.post("/api/cases/switch", json={"id": old})
    assert r.status_code == 409 and r.get_json()["code"] == "case.old"
    assert store.current_case() != old
    other = next(i for i in items if i != old)
    r = client.post("/api/cases/merge", json={"ids": [old, other], "name": "merged"})
    assert r.status_code == 409 and r.get_json()["code"] == "case.old"


def test_empty_case_without_version_is_stamped(qapp):
    _, client = qapp
    cid = client.post("/api/cases/add", json={"name": "empty"}).get_json()["case"]["id"]
    client.post("/api/cases/add", json={"name": "other"})
    c = sqlite3.connect(store._case_file(cid))
    c.execute("DELETE FROM meta WHERE key = 'schema_version'")
    c.commit()
    c.close()
    assert client.post("/api/cases/switch", json={"id": cid}).status_code == 200
    assert store.get_meta("schema_version") == str(store.SCHEMA_VERSION)
