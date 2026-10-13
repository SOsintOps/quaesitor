"""Copied from Cognitor (tests/test_translate.py, commit fb93e01) with the modules in audio/."""
import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

"""Test di fumo della traduzione (ROADMAP Fase 3): senza modelli, rete né pacchetti Argos."""
import numpy as np

from quaesitor.audio import translate as T
from quaesitor.audio.transcribe import transcribe_video, write_transcript


def test_align_to_segments_by_overlap_and_nearest():
    segs = [{"t0": 0.0, "t1": 5.0, "text": "a"}, {"t0": 5.0, "t1": 10.0, "text": "b"},
            {"t0": 20.0, "t1": 22.0, "text": "c"}]
    tr = [{"t0": 0.5, "t1": 4.0, "text": "Hello"}, {"t0": 4.2, "t1": 6.0, "text": "there"},
          {"t0": 6.5, "t1": 9.5, "text": "friend"}, {"t0": 30.0, "t1": 31.0, "text": "far"}]
    out = T.align_to_segments(segs, tr)
    assert out == ["Hello", "there friend", "far"]        # "there" covers the 1st most; "far" goes to the nearest
    assert T.align_to_segments([], tr) == []
    assert T.align_to_segments(segs, []) == ["", "", ""]


def test_sentence_split_regex():
    parts = T._SENT_SPLIT.split("Prima frase. Seconda frase! Terza? Quarta… fine.")
    assert parts == ["Prima frase.", "Seconda frase!", "Terza?", "Quarta…", "fine."]


def test_pair_cached_false_in_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("QUAESITOR_MODELS_DIR", str(tmp_path))
    assert not T.pair_cached("en", "it")
    assert T.pair_dir("en", "it") == tmp_path / "translate" / "en_it"


class _FakePair:
    calls = []

    def __init__(self, src, dst, use_gpu=False):
        self.src, self.dst = src, dst

    def translate(self, texts, beam_size=4):
        _FakePair.calls.append(list(texts))
        return [f"<{self.dst}>{t}" for t in texts]


def _transcript(lang, texts):
    return {"video": "v.mp4", "model": "tiny", "duration": 10.0, "languages": [lang],
            "speakers": None, "partial": False,
            "segments": [{"t0": i * 2.0, "t1": i * 2.0 + 2.0, "lang": lang, "speaker": None, "text": t}
                         for i, t in enumerate(texts)]}


def test_translate_english_source_to_italian_with_argos(monkeypatch):
    monkeypatch.setattr(T, "pair_cached", lambda s, d: True)
    monkeypatch.setattr(T, "ArgosPair", _FakePair)
    tr = _transcript("en", ["Hello.", "Bye."])
    T.translate_transcript(tr, ["en", "it"], log=lambda s: None)
    assert tr["translations"] == ["it"]                   # en = already the language of the audio
    assert [s["tr"]["it"] for s in tr["segments"]] == ["<it>Hello.", "<it>Bye."]


class _Seg:
    def __init__(self, a, b, text):
        self.start, self.end, self.text = a, b, text


class _Info:
    duration, language, language_probability = 4.0, "it", 0.95


class _StubModel:
    """Normal transcribe() in Italian; task='translate' returns the English."""
    def transcribe(self, path, **kw):
        if kw.get("task") == "translate":
            return iter([_Seg(0.0, 2.0, "Good morning."), _Seg(2.0, 4.0, "See you.")]), _Info()
        return iter([_Seg(0.0, 2.0, "Buongiorno."), _Seg(2.0, 4.0, "Arrivederci.")]), _Info()


def test_translate_italian_source_to_english_with_whisper(monkeypatch):
    tr = _transcript("it", ["Buongiorno.", "Arrivederci."])
    T.translate_transcript(tr, ["en", "it"], video_path="v.mp4", model=_StubModel(), log=lambda s: None)
    assert tr["translations"] == ["en"]                   # it = already the language of the audio
    assert [s["tr"]["en"] for s in tr["segments"]] == ["Good morning.", "See you."]


def test_pivot_through_english_for_other_sources(monkeypatch, tmp_path):
    """German source: English from Whisper, Italian from Argos en_it on the English text."""
    monkeypatch.setattr(T, "pair_cached", lambda s, d: True)
    monkeypatch.setattr(T, "ArgosPair", _FakePair)
    _FakePair.calls.clear()

    class _DeInfo(_Info):
        language = "de"

    class _DeModel(_StubModel):
        def transcribe(self, path, **kw):
            it, _ = super().transcribe(path, **kw)
            return it, _DeInfo()
    tr = _transcript("de", ["Guten Morgen.", "Tschüss."])
    T.translate_transcript(tr, ["it"], video_path="v.mp4", model=_DeModel(), log=lambda s: None)
    assert tr["translations"] == ["it"]
    assert _FakePair.calls == [["Good morning.", "See you."]]
    assert tr["segments"][0]["tr"]["it"] == "<it>Good morning."
    assert "en" not in tr["segments"][0]["tr"]            # English was only the pivot


def test_write_transcript_translated_file(tmp_path):
    tr = _transcript("en", ["Hello.", "Bye."])
    tr["speakers"] = 1
    for s in tr["segments"]:
        s["speaker"] = "PARLANTE 1"
        s["tr"] = {"it": "Ciao." if s["text"] == "Hello." else ""}
    path = write_transcript(tr, tmp_path, lang="it")
    body = open(path, encoding="utf-8").read()
    assert path.endswith("transcript_it.txt")
    assert "TRADUZIONE (IT)" in body
    assert "[00:00:00-00:00:02] PARLANTE 1 (it) Ciao." in body
    assert "(it) Bye." in body                             # missing translation: original text
    assert not (tmp_path / "transcript.json").exists()    # the .json is not touched


def test_transcribe_video_with_translation_and_fallback(tmp_path, monkeypatch):
    # translation ok
    monkeypatch.setattr(T, "pair_cached", lambda s, d: True)
    monkeypatch.setattr(T, "ArgosPair", _FakePair)
    res = transcribe_video("v.mp4", tmp_path / "ok", model=_StubModel(), translate=("en", "it"))
    assert res["translations"] == ["en"]
    assert (tmp_path / "ok" / "transcript_en.txt").exists()
    assert not (tmp_path / "ok" / "transcript_it.txt").exists()
    # translation that fails: the transcription stays valid
    monkeypatch.setattr(T, "whisper_translate", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    res = transcribe_video("v.mp4", tmp_path / "ko", model=_StubModel(), translate=("en",))
    assert len(res["segments"]) == 2 and not res.get("translations")
    assert (tmp_path / "ko" / "transcript.txt").exists()


def test_diarize_then_translate_keeps_speakers(tmp_path, monkeypatch):
    from quaesitor.audio import diarize as D
    monkeypatch.setattr(D, "decode_audio", lambda p: np.zeros(16000, dtype=np.float32))
    monkeypatch.setattr(D, "diarize_audio", lambda audio, **kw: {
        "speakers": 2, "windows": [(0.0, 2.0), (2.0, 4.0)], "labels": [0, 1],
        "turns": [], "speech": 4.0})
    res = transcribe_video("v.mp4", tmp_path, model=_StubModel(), diarize=True, translate=("en",))
    body = (tmp_path / "transcript_en.txt").read_text(encoding="utf-8")
    assert "parlanti: 2" in body and "PARLANTE 2 (en) See you." in body
    assert res["speakers"] == 2


def test_audio_italiano_con_solo_italiano_richiesto_non_rifa_whisper():
    """On 2026-09-02 a second Whisper pass into English was started, then discarded."""
    class _ModelloCheNonVaChiamato:
        def transcribe(self, *a, **k):
            raise AssertionError("seconda passata inutile")

    tr = _transcript("it", ["Buongiorno."])
    T.translate_transcript(tr, ["it"], video_path="v.mp4", model=_ModelloCheNonVaChiamato(),
                           log=lambda s: None)
    assert tr["translations"] == []
