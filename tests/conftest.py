"""Shared fixtures: the Flask app on a temporary data folder, one new case per test.

DATA_DIR is read when quaesitor.core is imported, so it is set here, before the import. The
sources folder of the tests is a temporary folder too: nothing is written next to
the program."""
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
_DATA = tempfile.mkdtemp(prefix="quaesitor-test-")
os.environ["DATA_DIR"] = _DATA
sys.path.insert(0, str(ROOT))

from quaesitor import app as quaesitor, archive  # noqa: E402


@pytest.fixture
def qapp(tmp_path, monkeypatch):
    """(quaesitor.app module, test client) with a new current case and a private sources folder."""
    folder = tmp_path / "sources"
    folder.mkdir()
    monkeypatch.setattr(archive, "SOURCES_DEFAULT", str(folder))
    archive._sources_cache["idx"] = None
    client = quaesitor.app.test_client()
    r = client.post("/api/cases/add", json={"name": f"test {tmp_path.name}"})
    assert r.status_code == 200, r.get_json()
    return quaesitor, client


def wait(client, url, key="running", timeout=30):
    """Polls a progress endpoint until the job is over; returns the last state."""
    t0 = time.time()
    while True:
        st = client.get(url).get_json()
        if not st.get(key):
            return st
        if time.time() - t0 > timeout:
            raise AssertionError(f"{url} still running: {st}")
        time.sleep(0.05)
