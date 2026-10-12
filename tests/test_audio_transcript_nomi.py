"""Copied from Cognitor (tests/test_transcript_nomi.py, commit fb93e01) with the modules in audio/."""
import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

"""Il trascritto con i nomi delle persone al posto delle etichette dei parlanti."""
import json

from audio.transcribe import write_named_transcript


def _run(tmp_path):
    d = tmp_path / "run"
    d.mkdir()
    (d / "transcript.json").write_text(json.dumps({
        "video": "intervista.mp4", "model": "small", "duration": 12.0, "speakers": 2,
        "segments": [
            {"t0": 0.0, "t1": 3.0, "speaker": "PARLANTE 1", "text": "Buonasera."},
            {"t0": 3.0, "t1": 8.0, "speaker": "PARLANTE 2", "text": "Buonasera a lei."},
            {"t0": 8.0, "t1": 12.0, "speaker": "PARLANTE 1", "text": "Cominciamo."},
        ]}, ensure_ascii=False), encoding="utf-8")
    return d


def test_i_nomi_sostituiscono_le_etichette(tmp_path):
    d = _run(tmp_path)

    out = write_named_transcript(d, {"PARLANTE 1": "IVANA MILIČEVIĆ", "PARLANTE 2": "HOON LEE"})

    testo = (d / "transcript_nomi.txt").read_text(encoding="utf-8")
    assert out and out.endswith("transcript_nomi.txt")
    assert "IVANA MILIČEVIĆ  Buonasera." in testo and "HOON LEE  Buonasera a lei." in testo
    assert "PARLANTE" not in testo.split("corrispondenze")[1].split("\n\n")[1]
    assert "corrispondenze (stabilite dall'analista)" in testo   # da dove viene il nome


def test_un_parlante_senza_nome_resta_com_era(tmp_path):
    d = _run(tmp_path)

    write_named_transcript(d, {"PARLANTE 1": "IVANA MILIČEVIĆ"})

    testo = (d / "transcript_nomi.txt").read_text(encoding="utf-8")
    assert "IVANA MILIČEVIĆ  Buonasera." in testo
    assert "PARLANTE 2  Buonasera a lei." in testo


def test_il_trascritto_originale_non_si_tocca(tmp_path):
    d = _run(tmp_path)
    prima = (d / "transcript.json").read_bytes()

    write_named_transcript(d, {"PARLANTE 1": "ANNA NERI"})

    assert (d / "transcript.json").read_bytes() == prima


def test_niente_da_scrivere(tmp_path):
    d = _run(tmp_path)
    assert write_named_transcript(d, {}) is None
    assert write_named_transcript(tmp_path / "vuota", {"PARLANTE 1": "X"}) is None


class _Seg:
    def __init__(self, a, b, testo):
        self.start, self.end, self.text = a, b, testo


class _Info:
    duration, language, language_probability = 12.0, "it", 0.9


class _ModelloFinto:
    """Restituisce segmenti con la stessa forma di faster-whisper."""
    def transcribe(self, path, **kw):
        return iter([_Seg(0.0, 3.0, "Buonasera."), _Seg(3.0, 8.0, "Buonasera a lei.")]), _Info()


def test_legge_i_segmenti_che_scrive_transcribe_video(tmp_path):
    """Il 2026-09-02 il trascritto con i nomi leggeva start/end su segmenti scritti
    con t0/t1: KeyError, e il test passava perche' costruiva i segmenti a mano."""
    from audio.transcribe import transcribe_video
    d = tmp_path / "run"
    transcribe_video("intervista.mp4", d, model=_ModelloFinto())

    out = write_named_transcript(d, {"PARLANTE 1": "ANNA NERI"})

    assert out and "[00:00:03 → 00:00:08]" in (d / "transcript_nomi.txt").read_text(encoding="utf-8")
