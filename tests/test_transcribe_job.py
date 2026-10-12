"""Video transcription as a job: a fake Whisper and a fake diarization, the real import."""
import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")

from conftest import wait  # noqa: E402


class _Seg:
    def __init__(self, a, b, text):
        self.start, self.end, self.text = a, b, text


class _Info:
    duration, language, language_probability = 6.0, "it", 0.99


class _StubModel:
    def __init__(self, gate=None):
        self.gate = gate

    def transcribe(self, path, **kw):
        def gen():
            yield _Seg(0.0, 3.0, "Prima frase del sospettato.")
            if self.gate:
                self.gate()
            yield _Seg(3.0, 6.0, "Seconda frase della vittima.")
        return gen(), _Info()


@pytest.fixture
def fake_audio(monkeypatch):
    from audio import diarize as D
    from audio import transcribe as T

    def fake_diarize_audio(audio, **kw):
        wins, labels = [(0.0, 1.5), (3.5, 5.0)], [0, 1]
        return {"speakers": 2, "windows": wins, "labels": labels,
                "turns": D.speaker_turns(wins, labels), "speech": 3.0}
    monkeypatch.setattr(D, "decode_audio", lambda p: np.zeros(16000, dtype=np.float32))
    monkeypatch.setattr(D, "diarize_audio", fake_diarize_audio)
    monkeypatch.setattr(T, "load_model", lambda *a, **k: _StubModel())
    return T


def _video(tmp_path, name="intercettazione.mp4", content=b"fake video bytes"):
    p = tmp_path / name
    p.write_bytes(content)
    return p


def _run(client, path, **kw):
    body = dict(dict(path=str(path), model_size="tiny", diarize=True), **kw)
    r = client.post("/api/transcribe", json=body)
    assert r.status_code == 200, r.get_json()
    return wait(client, "/api/transcribe/progress")


def test_transcription_builds_video_speakers_and_links(qapp, fake_audio, tmp_path):
    q, client = qapp
    st = _run(client, _video(tmp_path))
    assert not st["error"], st
    res = st["result"]
    assert res["segments"] == 2 and res["speakers"] == 2 and res["node"].startswith("video:")
    g = client.get("/api/graph").get_json()
    video = next(n for n in g["nodes"] if n.get("ntype") == "video")
    raw = {k: v for r in video.get("records") or [] for k, v in (r.get("raw") or {}).items()}
    assert "Speaker 1 (intercettazione.mp4): Prima frase" in raw.get("bodyText", "")
    names = {n["label"] for n in g["nodes"]}
    assert {"Speaker 1 (intercettazione.mp4)", "Speaker 2 (intercettazione.mp4)"} <= names
    assert sum(1 for e in g["edges"] if e.get("evid") == "speaks") == 2
    # the transcript is in the sources and the search finds it
    assert res["sources"] and res["sources_scan"]
    wait(client, "/api/sources/progress")
    hits = client.post("/api/sources/search", json={"q": "sospettato", "mode": "partial"}).get_json()
    assert "intercettazione" in str(hits)


def test_same_file_again_updates_the_same_nodes(qapp, fake_audio, tmp_path):
    _, client = qapp
    v = _video(tmp_path)
    _run(client, v)
    g1 = client.get("/api/graph").get_json()
    st = _run(client, v)
    assert st["result"]["nodes"] == 0 and st["result"]["links"] == 0
    g2 = client.get("/api/graph").get_json()
    assert len(g1["nodes"]) == len(g2["nodes"]) and len(g1["edges"]) == len(g2["edges"])


def test_stop_keeps_the_partial_transcript(qapp, fake_audio, tmp_path, monkeypatch):
    q, client = qapp
    monkeypatch.setattr(fake_audio, "load_model", lambda *a, **k: _StubModel(gate=q._tr_stop.set))
    st = _run(client, _video(tmp_path, "parziale.mp4"), diarize=False)
    assert not st["error"] and st["result"]["partial"] and st["result"]["segments"] == 1
    assert any(n.get("ntype") == "video" for n in client.get("/api/graph").get_json()["nodes"])


def test_without_the_packages(qapp, monkeypatch, tmp_path):
    q, client = qapp
    monkeypatch.setattr(q._audio, "available", lambda: (False, "missing packages: faster-whisper"))
    r = client.post("/api/transcribe", json={"path": str(_video(tmp_path))})
    assert r.status_code == 503 and "faster-whisper" in r.get_json()["reason"]
    assert client.get("/api/transcribe/status").get_json()["models"][0] == "tiny"


def test_bad_requests(qapp, fake_audio, tmp_path):
    _, client = qapp
    assert client.post("/api/transcribe", json={"path": str(tmp_path / "none.mp4")}).status_code == 400
    assert client.post("/api/transcribe", json={"path": str(_video(tmp_path)),
                                                 "model_size": "huge"}).status_code == 400
