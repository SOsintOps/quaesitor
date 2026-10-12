"""Import of a Cognitor bundle (.cognitor.zip): entities, photos, transcripts."""
import io
import json
import os
import shutil
import zipfile

import pytest

import ftm_bundle
from conftest import FIXTURES, wait

SAMPLE = FIXTURES / "cognitor_sample.cognitor.zip"


def _import_path(client, path):
    r = client.post("/api/ftm/import", json={"path": str(path)})
    assert r.status_code == 200, r.get_json()
    st = wait(client, "/api/ftm/progress")
    assert not st["error"], st
    return st


def test_inspect_reports_the_bundle(qapp):
    _, client = qapp
    r = client.post("/api/ftm/inspect", json={"path": str(SAMPLE)}).get_json()
    assert r["ok"] and r["bundle"] and r["case_name"] == "Test case"
    assert r["images"] == 6 and r["transcripts"] == 2
    assert r["schemas"]["Person"] == 6 and r["schemas"]["Video"] == 1


def test_import_bundle(qapp):
    q, client = qapp
    st = _import_path(client, SAMPLE)
    assert st["images"] == 6 and st["images_refused"] == 0 and st["transcripts"] == 2
    g = client.get("/api/graph").get_json()
    by_label = {n["label"]: n for n in g["nodes"]}
    for name in ("Mario Rossi", "Anna", "Unknown #1 (Test case)", "Speaker 2 (clip.mp4)"):
        assert name in by_label, name
    mario = by_label["Mario Rossi"]
    assert mario.get("pic") and mario["image"].startswith("/media/media/cognitor/CASE_1/")
    photos = [n for n in g["nodes"] if n.get("ntype") == "photo"]
    assert len(photos) == 6
    for n in photos:
        path = n["image"][len("/media/"):]
        assert client.get("/media/" + path.split("/media/", 1)[-1]).status_code == 200 or \
            os.path.isfile(os.path.join(q.DATA_DIR, *path.split("/")))
    kinds = [e.get("evid") for e in g["edges"]]
    assert kinds.count("seen") == 3 and kinds.count("speaks") == 2 and kinds.count("appears") == 2
    video = next(n for n in g["nodes"] if n.get("ntype") == "video")
    raw = {k: v for r in video.get("records") or [] for k, v in (r.get("raw") or {}).items()}
    assert "Mario Rossi: ciao" in raw.get("bodyText", "")
    # transcripts copied in the sources folder and indexed
    assert st["sources_scan"]
    wait(client, "/api/sources/progress")
    hits = client.post("/api/sources/search", json={"q": "buongiorno", "mode": "partial"}).get_json()
    assert json.dumps(hits).count("cog-CASE_1-v2") >= 1


def test_reimport_bundle_does_not_duplicate(qapp):
    _, client = qapp
    _import_path(client, SAMPLE)
    g1 = client.get("/api/graph").get_json()
    _import_path(client, SAMPLE)
    g2 = client.get("/api/graph").get_json()
    assert len(g1["nodes"]) == len(g2["nodes"]) and len(g1["edges"]) == len(g2["edges"])


def _rebuild(tmp_path, change):
    """A copy of the sample with one change applied to the {name: bytes} map."""
    z = zipfile.ZipFile(SAMPLE)
    files = {n: z.read(n) for n in z.namelist()}
    change(files)
    out = tmp_path / "bad.cognitor.zip"
    with zipfile.ZipFile(out, "w") as w:
        for n, d in files.items():
            w.writestr(n, d)
    return out


def test_tampered_file_is_refused(tmp_path):
    def tamper(files):
        files["entities.ftm.json"] += b"\n"
    with ftm_bundle.Bundle(_rebuild(tmp_path, tamper)) as b:
        with pytest.raises(ftm_bundle.BundleError):
            b.entities_blob()


def test_unexpected_path_is_refused(tmp_path):
    def evil(files):
        files["../evil.txt"] = b"x"
    with pytest.raises(ftm_bundle.BundleError):
        ftm_bundle.Bundle(_rebuild(tmp_path, evil))


def test_non_image_media_is_not_installed(tmp_path):
    def fake(files):
        man = json.loads(files["manifest.json"])
        name = next(n for n in files if n.startswith("media/"))
        files[name] = b"not an image"
        import hashlib
        man["files"][name] = hashlib.sha256(files[name]).hexdigest()
        files["manifest.json"] = json.dumps(man).encode()
    with ftm_bundle.Bundle(_rebuild(tmp_path, fake)) as b:
        out = b.install_media(str(tmp_path / "data"))
        assert len(out) == 5 and len(b.refused) == 1


def test_bundle_upload_as_data_url(qapp):
    """A small bundle also travels as an upload (base64), like any FtM file."""
    import base64
    _, client = qapp
    data = "data:application/zip;base64," + base64.b64encode(SAMPLE.read_bytes()).decode()
    r = client.post("/api/ftm/inspect", json={"data": data}).get_json()
    assert r["ok"] and r["bundle"]


def test_round_trip_through_the_export(qapp):
    """Bundle -> case -> FtM export -> same case: nothing doubles; -> a new case: the
    photos come back, because the export names files already under data/media."""
    import base64
    _, client = qapp
    _import_path(client, SAMPLE)
    g1 = client.get("/api/graph").get_json()
    blob = client.get("/api/ftm/export").data
    assert b'"schema": "Image"' in blob
    data = "data:application/json;base64," + base64.b64encode(blob).decode()
    for _ in range(2):
        client.post("/api/ftm/import", json={"data": data, "dataset": "export"})
        st = wait(client, "/api/ftm/progress")
        assert not st["error"] and st["errors"] == 0
        g2 = client.get("/api/graph").get_json()
        assert len(g2["nodes"]) == len(g1["nodes"]) and len(g2["edges"]) == len(g1["edges"])
    client.post("/api/cases/add", json={"name": "second"})
    client.post("/api/ftm/import", json={"data": data, "dataset": "export"})
    wait(client, "/api/ftm/progress")
    g3 = client.get("/api/graph").get_json()
    assert sum(1 for n in g3["nodes"] if n.get("ntype") == "photo") == 6
    assert sum(1 for n in g3["nodes"] if n.get("pic")) == 5
