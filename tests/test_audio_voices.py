"""Copied from Cognitor (tests/test_voci.py, commit fb93e01) with the modules in audio/."""
import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

"""`voices.py`: catalogue, voiceprints per speaker, comparison and groups, with no models or audio.

The embeddings are synthetic (`_fake_embeddings` of test_diarize): what is checked here is
the logic, not the model. The model is tested by hand on the sample (ROADMAP).
"""
import numpy as np
import pytest

from quaesitor.audio import voices as V
import re
_FAM_VALIDA = re.compile(r"^[A-Za-z0-9_-]{1,32}$")   # as in Cognitor's catalogo.py
from test_audio_diarize import _fake_embeddings


def test_il_catalogo_e_coerente():
    assert V.DEFAULT_VOICE in V.VOICE_MODELS
    for fam, v in V.VOICE_MODELS.items():
        assert _FAM_VALIDA.match(fam), f"{fam} non e' un nome di famiglia valido per i file .npy"
        assert v["file"].endswith(".onnx") and v["dim"] > 0 and v["size_mb"] > 0
        assert v["note_key"].startswith("srv.note_voce_")
    with pytest.raises(ValueError):
        V.model_file("inesistente")


def test_l_url_di_cam_plus_plus_e_codificato():
    """GitHub answers 404 to a bare `+` in the asset name."""
    assert V.model_url("wcam").endswith("wespeaker_en_voxceleb_CAM%2B%2B_LM.onnx")
    assert "+" not in V.model_url("wcam").rsplit("/", 1)[1]
    assert V.model_url("wr34").endswith("/wespeaker_en_voxceleb_resnet34_LM.onnx")


def test_i_percorsi_seguono_la_variabile_d_ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("QUAESITOR_MODELS_DIR", str(tmp_path))
    assert V.model_path("wr34") == tmp_path / "diarize" / V.model_file("wr34")
    assert not V.model_cached("wr34")
    V.model_path("wr34").parent.mkdir(parents=True)
    V.model_path("wr34").write_bytes(b"x")
    assert V.model_cached("wr34")


def test_affidabilita_per_durata():
    assert V.affidabilita(5) == "bassa"
    assert V.affidabilita(15) == "media"
    assert V.affidabilita(29.9) == "media"
    assert V.affidabilita(30) == "alta"


def test_i_secondi_netti_non_contano_due_volte_le_sovrapposizioni():
    assert V.secondi_netti([(0.0, 3.0), (1.5, 4.5), (3.0, 6.0)]) == 6.0
    assert V.secondi_netti([(10.0, 13.0), (0.0, 3.0)]) == 6.0
    assert V.secondi_netti([]) == 0.0


def test_centroidi_per_parlante_con_il_minimo_di_parlato():
    embs, truth = _fake_embeddings(n_per=6, k=2)
    wins = [(i * 1.5, i * 1.5 + 3.0) for i in range(12)]
    labels = list(truth)
    labels[11] = 2                                   # a third speaker with a single window
    out = V.centroidi_per_parlante(embs, labels, wins)
    assert set(out) == {"PARLANTE 1", "PARLANTE 2", "PARLANTE 3"}
    p1 = out["PARLANTE 1"]
    assert p1["ok"] and p1["n_windows"] == 6 and p1["speech_seconds"] == 10.5
    assert abs(np.linalg.norm(p1["centroid"]) - 1.0) < 1e-5
    p3 = out["PARLANTE 3"]
    assert not p3["ok"] and p3["centroid"] is None and "insufficiente" in p3["why"]
    assert p3["affidabilita"] == "bassa"
    # the centroid resembles its own windows more than those of the other one
    mie = embs[np.array(labels) == 0] @ p1["centroid"]
    altre = embs[np.array(labels) == 1] @ p1["centroid"]
    assert mie.min() > altre.max()


def test_riepilogo_impronte_tiene_solo_i_metadati():
    embs, truth = _fake_embeddings(n_per=6, k=1)
    wins = [(i * 1.5, i * 1.5 + 3.0) for i in range(6)]
    impronte = V.centroidi_per_parlante(embs, truth, wins)
    r = V.riepilogo_impronte(impronte, "wr34", "file.onnx", "leggera")
    assert r["family"] == "wr34" and r["file"] == V.NPZ and r["min_speech"] == V.MIN_SPEECH_S
    assert set(r["speakers"]["PARLANTE 1"]) == {"ok", "n_windows", "speech_seconds", "affidabilita"}
    assert "centroid" not in r["speakers"]["PARLANTE 1"]


def test_npz_va_e_torna(tmp_path):
    embs, truth = _fake_embeddings(n_per=4, k=2)
    wins = [(i * 1.5, i * 1.5 + 3.0) for i in range(8)]
    impronte = V.centroidi_per_parlante(embs, truth, wins)
    speakers = ["PARLANTE 1", "PARLANTE 2"]
    V.scrivi_npz(tmp_path, embs, wins, truth, speakers, impronte, "wr34", "m.onnx", "leggera")
    z = V.leggi_npz(tmp_path)
    assert z["family"] == "wr34" and z["model"] == "m.onnx" and z["diarizer"] == "leggera"
    assert z["embeddings"].shape == (8, 256) and z["windows"].shape == (8, 2)
    assert z["speakers"] == speakers
    assert np.allclose(z["centroids"][0], impronte["PARLANTE 1"]["centroid"])
    assert V.leggi_npz(tmp_path / "altrove") is None


def test_il_punteggio_e_un_coseno_e_la_coorte_lo_normalizza():
    rng = np.random.default_rng(1)
    a = rng.normal(size=256); a /= np.linalg.norm(a)
    b = a + 0.2 * rng.normal(size=256); b /= np.linalg.norm(b)
    assert abs(V.punteggio(a, a) - 1.0) < 1e-5
    assert V.punteggio(a, b) == pytest.approx(float(a @ b), abs=1e-5)
    coorte = rng.normal(size=(40, 256)); coorte /= np.linalg.norm(coorte, axis=1, keepdims=True)
    normalizzato = V.punteggio(a, b, coorte=coorte)
    assert normalizzato > 3          # a similar voice stands out above the unrelated voices
    assert V.punteggio(a, b, coorte=coorte[:1]) == pytest.approx(float(a @ b), abs=1e-5)


def test_livelli_delle_proposte():
    assert V.livello(0.9) == "probabile"
    assert V.livello(V.T_VOICE_PROBABILE) == "probabile"
    assert V.livello(0.55) == "da_verificare"
    assert V.livello(0.3) is None


def _voce(eid, name, vettore, family="wr34", secondi=40.0):
    return {"eid": eid, "name": name, "centroid": vettore, "family": family, "speech_seconds": secondi}


def test_i_candidati_sono_ordinati_e_isolati_per_famiglia():
    rng = np.random.default_rng(2)
    me = rng.normal(size=256); me /= np.linalg.norm(me)
    simile = me + 0.3 * rng.normal(size=256); simile /= np.linalg.norm(simile)
    lontano = rng.normal(size=256); lontano /= np.linalg.norm(lontano)
    note = [_voce("1", "IVANA", simile), _voce("2", "HOON", lontano, secondi=8.0),
            _voce("3", "GEMELLA", me.copy(), family="wcam"),            # identical, other family
            _voce("1", "IVANA", me.copy(), secondi=70.0)]                # second voiceprint, better
    c = V.candidati_parlante(me, "wr34", note)
    assert [x["eid"] for x in c] == ["1"]
    assert c[0]["score"] == pytest.approx(1.0, abs=1e-3) and c[0]["livello"] == "probabile"
    assert c[0]["speech_seconds"] == 70.0 and c[0]["affidabilita"] == "alta"
    assert V.candidati_parlante(None, "wr34", note) == []
    assert V.candidati_parlante(me, "wr293", note) == []


def test_raggruppa_per_similarita_senza_catene():
    embs, truth = _fake_embeddings(n_per=4, k=3)
    gruppi = V.raggruppa(embs, threshold=0.6)
    assert len(gruppi) == 3
    for g in gruppi:
        assert len({truth[i] for i in g}) == 1
    assert V.raggruppa(np.zeros((0, 256)), 0.6) == []
    assert V.raggruppa(embs[:1], 0.6) == [[0]]
    # two different voices do not merge even if a third half-resembles both
    a = embs[0]; b = embs[4]
    ponte = a + b; ponte /= np.linalg.norm(ponte)
    M = np.vstack([a, b, ponte])
    gruppi = V.raggruppa(M, threshold=float(min(a @ ponte, b @ ponte)) - 0.01)
    assert [0, 1] not in [sorted(g)[:2] for g in gruppi if len(g) == 3]


def test_coppie_sopra_soglia_a_blocchi_come_la_matrice_intera():
    """The pairs computed in blocks match, as a set and in order, those of the
    N x N matrix that `recluster` kept in memory until 2026-09-13."""
    embs, _ = _fake_embeddings(n_per=5, k=4)
    S = embs @ embs.T
    n = len(embs)
    attese = sorted(((-float(S[i, j]), i, j) for i in range(n) for j in range(i + 1, n)
                     if S[i, j] >= 0.3))
    for blocco in (1, 3, 7, 64):                    # block edges at different positions
        ii, jj, ss = V.coppie_sopra_soglia(embs, 0.3, blocco=blocco)
        assert [(i, j) for _, i, j in attese] == list(zip(ii.tolist(), jj.tolist()))
        assert np.allclose(ss, [-s for s, _, _ in attese], atol=1e-5)
        assert (ii < jj).all()
    ii, jj, ss = V.coppie_sopra_soglia(embs, 2.0)   # no pair above the threshold
    assert len(ii) == len(jj) == len(ss) == 0
    assert all(len(x) == 0 for x in V.coppie_sopra_soglia(np.zeros((0, 8)), 0.5))
