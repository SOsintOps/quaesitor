"""Copied from Cognitor (tests/test_pyannote.py, commit fb93e01) with the modules in audio/."""
import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

"""Advanced diarization (pyannote): optional, with a fallback that never leaves you stranded."""
from quaesitor.audio import diarize


def test_stato_dice_che_cosa_manca():
    st = diarize.pyannote_status("")
    assert set(st) >= {"ready", "torch", "pyannote", "token", "why"}
    assert st["token"] is False
    if not st["ready"]:
        assert st["why"], "quando non è pronto va detto perché"


def test_il_token_e_dell_analista():
    """Without a token it is never ready, however installed it is."""
    st = diarize.pyannote_status("")
    assert not st["ready"]
    con_token = diarize.pyannote_status("hf_finto")
    assert con_token["token"] is True
    assert con_token["ready"] == (con_token["torch"] and con_token["pyannote"])


def test_senza_pyannote_si_ripiega_e_lo_dichiara(monkeypatch):
    """The fallback to the lightweight diarization is automatic and ends up in the log."""
    detto = []
    monkeypatch.setattr(diarize, "add_speakers",
                        lambda *a, **k: {"segments": [], "speakers": 0})

    out = diarize.add_speakers_auto("finto.mp4", {"segments": []}, token="",
                                    prefer_pyannote=True, log=detto.append)

    assert out["diarizer"] == "leggera"
    assert any("pyannote non utilizzabile" in r for r in detto)


def test_senza_richiesta_non_prova_nemmeno(monkeypatch):
    monkeypatch.setattr(diarize, "add_speakers", lambda *a, **k: {"segments": []})
    monkeypatch.setattr(diarize, "diarize_pyannote",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("non va chiamata")))
    assert diarize.add_speakers_auto("finto.mp4", {"segments": []},
                                     log=lambda *_: None)["diarizer"] == "leggera"


def _pyannote_finto(monkeypatch, turni):
    """Injects fake torch and pyannote.audio: the pipeline returns `turni`."""
    import sys
    import types

    class _Seg:
        def __init__(self, a, b):
            self.start, self.end = a, b

    class _Annotazione:
        def itertracks(self, yield_label=True):
            return iter([(_Seg(a, b), None, f"SPEAKER_{k:02d}") for a, b, k in turni])

    class _Pipeline:
        @staticmethod
        def from_pretrained(name, use_auth_token=""):
            return lambda path, **kw: _Annotazione()

    torch = types.ModuleType("torch")
    torch.cuda = types.SimpleNamespace(is_available=lambda: False)
    pyannote = types.ModuleType("pyannote")
    audio = types.ModuleType("pyannote.audio")
    audio.Pipeline = _Pipeline
    pyannote.audio = audio
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "pyannote", pyannote)
    monkeypatch.setitem(sys.modules, "pyannote.audio", audio)


def test_pyannote_etichetta_i_segmenti_reali(monkeypatch):
    """On 2026-09-02 pyannote read start/end on segments written with t0/t1: the
    KeyError ended in the fallback and pyannote was never used."""
    _pyannote_finto(monkeypatch, [(0.0, 4.0, 0), (4.0, 10.0, 1)])
    transcript = {"segments": [{"t0": 0.0, "t1": 3.0, "text": "a", "speaker": None},
                               {"t0": 5.0, "t1": 9.0, "text": "b", "speaker": None}]}

    out = diarize.add_speakers_auto("finto.mp4", transcript, token="hf_finto",
                                    prefer_pyannote=True, log=lambda *_: None)

    assert out["diarizer"] == "pyannote" and out["speakers"] == 2
    assert [s["speaker"] for s in out["segments"]] == ["PARLANTE 1", "PARLANTE 2"]
    assert out["speaker_turns"][0] == {"speaker": "PARLANTE 1", "t0": 0.0, "t1": 4.0}


def test_pyannote_senza_modello_voce_lascia_i_turni_validi(monkeypatch, tmp_path):
    """The voiceprints on pyannote's turns need the WeSpeaker model: if the download
    fails, the speakers stay and the log says so."""
    monkeypatch.setenv("QUAESITOR_MODELS_DIR", str(tmp_path / "vuota"))
    _pyannote_finto(monkeypatch, [(0.0, 4.0, 0), (4.0, 10.0, 1)])
    monkeypatch.setattr(diarize, "decode_audio", lambda p: __import__("numpy").zeros(160000, "float32"))

    def boom(**kw):
        raise RuntimeError("rete assente")
    monkeypatch.setattr(diarize, "download_models", boom)
    righe = []
    transcript = {"segments": [{"t0": 0.0, "t1": 3.0, "text": "a", "speaker": None}]}
    out = diarize.add_speakers_auto("finto.mp4", transcript, token="hf_finto", prefer_pyannote=True,
                                    log=righe.append, voice_model="wr34")
    assert out["diarizer"] == "pyannote" and out["speakers"] == 2
    assert "voiceprints" not in out and "_voices" not in out
    assert any("impronte vocali non calcolate" in r for r in righe)
