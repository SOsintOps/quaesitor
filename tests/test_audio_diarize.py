"""Copied from Cognitor (tests/test_diarize.py, commit fb93e01) with the modules in audio/."""
import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

"""Test di fumo della diarizzazione (ROADMAP Fase 2): senza modelli, rete né audio reale."""
import json
import math

import numpy as np
import pytest

from quaesitor.audio import diarize as D
from quaesitor.audio.transcribe import transcribe_video, write_transcript


def test_fbank_shape_and_cmn():
    sr = D.SAMPLE_RATE
    t = np.arange(int(1.5 * sr)) / sr
    wave = (0.3 * np.sin(2 * math.pi * 220 * t)).astype(np.float32)
    f = D.fbank(wave)
    assert f.shape == (1 + (len(wave) - 400) // 160, 80)   # 25 ms / 10 ms, snip_edges
    assert f.dtype == np.float32
    assert np.allclose(f.mean(axis=0), 0.0, atol=1e-3)       # CMN per utterance
    # waves that are too short are padded: at least one frame
    assert D.fbank(np.zeros(100, dtype=np.float32)).shape[0] == 1


def test_window_plan_covers_regions():
    wins = D.window_plan([(0.0, 4.0), (10.0, 10.3), (20.0, 21.0)])
    assert wins[0] == (0.0, D.WINDOW_SEC)
    assert all(b - a <= D.WINDOW_SEC + 1e-6 for a, b in wins)
    assert wins[-1] == (20.0, 21.0)                 # short region but >= MIN_WINDOW_SEC
    assert not any(a >= 10.0 and b <= 10.3 for a, b in wins)   # below the minimum: ignored
    assert max(b for a, b in wins if b <= 4.0) >= 4.0 - D.HOP_SEC / 2


def _fake_embeddings(n_per=6, k=3, seed=0):
    rng = np.random.default_rng(seed)
    centers = rng.normal(size=(k, 256))
    embs, truth = [], []
    for c in range(k):
        for _ in range(n_per):
            v = centers[c] + 0.15 * rng.normal(size=256)
            embs.append(v / np.linalg.norm(v))
            truth.append(c)
    return np.array(embs, dtype=np.float32), truth


def test_cluster_embeddings_auto_and_forced():
    embs, truth = _fake_embeddings()
    labels = D.cluster_embeddings(embs)
    assert labels.max() + 1 == 3
    # labels consistent with the ground truth (up to permutation) and numbered by first appearance
    assert labels[0] == 0
    for c in range(3):
        assert len(set(labels[np.array(truth) == c])) == 1
    forced = D.cluster_embeddings(embs, num_speakers=2)
    assert forced.max() + 1 == 2
    assert D.cluster_embeddings(embs[:1]).tolist() == [0]
    assert D.cluster_embeddings(embs[:0]).size == 0


def test_small_clusters_are_absorbed():
    embs, _ = _fake_embeddings(n_per=5, k=2)
    rng = np.random.default_rng(1)
    outlier = rng.normal(size=256).astype(np.float32)
    embs = np.vstack([embs, (outlier / np.linalg.norm(outlier))[None]])
    labels = D.cluster_embeddings(embs)
    assert labels.max() + 1 == 2                    # the single outlier does not create a speaker


def test_assign_speakers_and_turns():
    wins = [(0.0, 1.5), (0.75, 2.25), (3.0, 4.5), (3.75, 5.25)]
    labels = [0, 0, 1, 1]
    segs = [{"t0": 0.2, "t1": 2.0, "speaker": None, "text": "ciao"},
            {"t0": 3.1, "t1": 5.0, "speaker": None, "text": "salve"},
            {"t0": 9.0, "t1": 9.5, "speaker": None, "text": "fuori"}]   # no window: the nearest
    D.assign_speakers(segs, wins, labels)
    assert [s["speaker"] for s in segs] == ["PARLANTE 1", "PARLANTE 2", "PARLANTE 2"]
    turns = D.speaker_turns(wins, labels)
    assert turns == [{"t0": 0.0, "t1": 2.25, "speaker": "PARLANTE 1"},
                     {"t0": 3.0, "t1": 5.25, "speaker": "PARLANTE 2"}]


def test_write_transcript_with_speakers(tmp_path):
    result = {"video": "x.mp4", "model": "tiny", "duration": 12.0, "languages": ["it"],
              "speakers": 2, "partial": False,
              "segments": [{"t0": 0.0, "t1": 5.0, "lang": "it", "speaker": "PARLANTE 1", "text": "Ciao"},
                           {"t0": 5.0, "t1": 12.0, "lang": "it", "speaker": "PARLANTE 2", "text": "Salve"}]}
    txt = write_transcript(result, tmp_path)
    body = open(txt, encoding="utf-8").read()
    assert "parlanti: 2" in body
    assert "[00:00:00-00:00:05] PARLANTE 1 (it) Ciao" in body
    data = json.loads((tmp_path / "transcript.json").read_text(encoding="utf-8"))
    assert data["speakers"] == 2


class _Seg:
    def __init__(self, a, b, text):
        self.start, self.end, self.text = a, b, text


class _Info:
    duration, language, language_probability = 6.0, "it", 0.9


class _StubModel:
    def transcribe(self, path, **kw):
        return iter([_Seg(0.0, 3.0, "Prima frase."), _Seg(3.0, 6.0, "Seconda frase.")]), _Info()


def test_transcribe_diarize_fallback_without_models(tmp_path, monkeypatch):
    """If the diarization fails (here: models that cannot be downloaded) the transcription stays valid."""
    monkeypatch.setenv("QUAESITOR_MODELS_DIR", str(tmp_path / "nomodels"))

    def boom(*a, **k):
        raise RuntimeError("rete assente")
    monkeypatch.setattr(D, "download_models", boom)
    monkeypatch.setattr(D, "decode_audio", lambda p: np.zeros(16000, dtype=np.float32))
    res = transcribe_video("video.mp4", tmp_path, model=_StubModel(), diarize=True)
    assert len(res["segments"]) == 2
    assert res["speakers"] is None
    assert all(s["speaker"] is None for s in res["segments"])
    assert (tmp_path / "transcript.txt").exists()


def test_transcribe_diarize_uses_fake_pipeline(tmp_path, monkeypatch):
    """With a fake diarization the segments get PARLANTE k and the files are rewritten."""
    def fake_diarize_audio(audio, **kw):
        wins, labels = [(0.0, 1.5), (3.5, 5.0)], [0, 1]
        return {"speakers": 2, "windows": wins, "labels": labels,
                "turns": D.speaker_turns(wins, labels), "speech": 3.0}
    monkeypatch.setattr(D, "decode_audio", lambda p: np.zeros(16000, dtype=np.float32))
    monkeypatch.setattr(D, "diarize_audio", fake_diarize_audio)
    res = transcribe_video("video.mp4", tmp_path, model=_StubModel(), diarize=True)
    assert res["speakers"] == 2
    assert [s["speaker"] for s in res["segments"]] == ["PARLANTE 1", "PARLANTE 2"]
    assert res["speaker_turns"][1]["speaker"] == "PARLANTE 2"
    body = (tmp_path / "transcript.txt").read_text(encoding="utf-8")
    assert "PARLANTE 2 (it) Seconda frase." in body
    assert "voiceprints" not in res and "_voices" not in res     # without embeddings, no voiceprints


def test_le_impronte_finiscono_nel_npz_e_non_nel_json(tmp_path, monkeypatch):
    """A run with embeddings writes voices.npz and the voiceprints key (metadata only):
    the speaker with little speech has no voiceprint and the reason written."""
    import json
    from quaesitor.audio import voices as V
    embs, _ = _fake_embeddings(n_per=5, k=2)
    wins = [(t, t + 3.0) for t in np.arange(0.0, 7.5, 1.5)] + [(20.0, 23.0), (21.5, 24.5), (23.0, 26.0),
                                                                (24.5, 27.5), (26.0, 29.0)]
    labels = [0] * 5 + [1] * 5
    labels[9] = 2                                     # a third speaker with a single window
    embs = np.vstack([embs, embs[-1:]])[:10]

    def fake_diarize_audio(audio, **kw):
        return {"speakers": 3, "windows": wins, "labels": labels, "turns": D.speaker_turns(wins, labels),
                "speech": 20.0, "embeddings": embs, "family": "wr34", "model": V.model_file("wr34")}
    monkeypatch.setattr(D, "decode_audio", lambda p: np.zeros(16000, dtype=np.float32))
    monkeypatch.setattr(D, "diarize_audio", fake_diarize_audio)
    res = transcribe_video("video.mp4", tmp_path, model=_StubModel(), diarize=True)

    assert "_voices" not in res
    vp = res["voiceprints"]
    assert vp["family"] == "wr34" and vp["file"] == "voices.npz"
    assert vp["speakers"]["PARLANTE 1"]["ok"] and vp["speakers"]["PARLANTE 2"]["ok"]
    assert not vp["speakers"]["PARLANTE 3"]["ok"] and "insufficiente" in vp["speakers"]["PARLANTE 3"]["why"]
    sul_disco = json.loads((tmp_path / "transcript.json").read_text(encoding="utf-8"))
    assert sul_disco["voiceprints"] == vp and "_voices" not in sul_disco
    npz = V.leggi_npz(tmp_path)
    assert npz["family"] == "wr34" and npz["embeddings"].shape == (10, 256)
    assert npz["speakers"] == ["PARLANTE 1", "PARLANTE 2", "PARLANTE 3"]
    assert np.isnan(npz["centroids"][2]).all() and not np.isnan(npz["centroids"][0]).any()


@pytest.mark.skipif(not D.vad_cached(), reason="Silero VAD non in cache")
def test_vad_on_silence_finds_nothing():
    # the models are not enough: the runtime that executes them is needed too. On the CI
    # runners both are missing and the guard above is enough, but on a machine with the models
    # already cached and without onnxruntime this test failed instead of skipping.
    pytest.importorskip("onnxruntime")
    sess = D._session(D.models_dir() / "silero_vad.onnx")
    assert D.vad_regions(np.zeros(D.SAMPLE_RATE * 2, dtype=np.float32), sess) == []
