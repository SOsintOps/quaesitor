# -*- coding: utf-8 -*-
# Quaesitor - case graph for OSINT investigations
# Copyright (C) 2026 Ramingo (SOsintOps)
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Originally part of Cognitor (https://github.com/SOsintOps/cognitor), commit fb93e01,
# released by its holder under the GPL as part of Quaesitor (point 6 of the Cognitor
# licence, 2026-10-12). See audio/README.md for the changes made in the copy.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Voiceprints: whose voice it is, within and across videos.

Diarization (`diarize.py`) answers "how many voices and when": for every window of
3 s it computes a WeSpeaker embedding, clusters them and numbers the speakers by order of
first appearance. Up to 0.16.0 the embeddings were discarded right after: "PARLANTE 1" of
two different videos had nothing in common but the label. This module keeps
the voiceprint of every speaker (the centroid of their windows) and makes it comparable
across runs, across videos and with the people of the case.

Three rules, taken from the faces:
- **the family**: different models produce vectors that cannot be compared. The family is
  the model id (`wr34`, `wcam`, `wr293`) and goes with every voiceprint, in the file, in the
  database and in the case file. Comparison happens only within the same family.
- **the minimum of speech**: below `MIN_SPEECH_S` net seconds the centroid is a noisy
  window, not a voice. The speaker keeps their label in the transcript, but does not
  enter the comparisons, and the reason is written (`why`).
- **no automatic merge**: the module produces scores and proposals. Linking a voice
  to a person is an act of the analyst, recorded and reversible.

The thresholds are cosines between L2-normalised centroids (`T_VOICE_*`). They must not be
confused with `diarize.CLUSTER_THRESHOLD`, which is a **distance** (0.70 = similarity 0.30)
between single windows with average linkage: a different operation. A centroid of many
windows is more stable than a single window, so the same voices come out more similar and
the thresholds sit higher.

What it is not: a forensic voice comparison. That requires a reference cohort,
a likelihood-ratio calibration and an expert. Here the score is an investigative
lead, accompanied by the seconds of speech and by a reliability level tied to the
duration (`affidabilita`). Cohort normalisation (`punteggio(..., coorte=...)`)
is in place to reduce the channel effect, and is switched on after a measurement on the sample.
"""
# «You know my method. It is founded upon the observation of trifles.»
#   A. Conan Doyle, The Boscombe Valley Mystery
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

import numpy as np

# ---------------------------------------------------------------------------
# catalogue of the voice models (WeSpeaker, ONNX export by sherpa-onnx)
# ---------------------------------------------------------------------------
BASE_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/"

# All WeSpeaker exports have a single input [B, T, 80] (fbank from diarize.fbank, int16
# scale, CMN) and a single output [B, dim]. The number of parameters and the error (EER on
# VoxCeleb1-O, from the WeSpeaker model zoo) are in the notes. `dim` is checked against the
# file metadata on first use (`verifica_dim`): if the catalogue is wrong, the error says so.
VOICE_MODELS = {
    "wr34": {"file": "wespeaker_en_voxceleb_resnet34_LM.onnx", "size_mb": 26, "dim": 256,
             "label": "WeSpeaker ResNet34-LM", "eer": 0.72,
             "note": "predefinito: 6,6 M parametri, EER 0,72 %, il più rapido",
             "note_key": "srv.note_voce_wr34"},
    "wcam": {"file": "wespeaker_en_voxceleb_CAM++_LM.onnx", "size_mb": 28, "dim": 512,
             "label": "WeSpeaker CAM++-LM", "eer": 0.72,
             "note": "7,2 M parametri, EER 0,72 %, stesso peso del predefinito",
             "note_key": "srv.note_voce_wcam"},
    "wr293": {"file": "wespeaker_en_voxceleb_resnet293_LM.onnx", "size_mb": 109, "dim": 256,
              "label": "WeSpeaker ResNet293-LM", "eer": 0.43,
              "note": "28,6 M parametri, EER 0,43 %, circa quattro volte più lento su CPU",
              "note_key": "srv.note_voce_wr293"},
}
DEFAULT_VOICE = "wr34"
FAMILY_LABEL = {fam: v["label"] for fam, v in VOICE_MODELS.items()}

# ---------------------------------------------------------------------------
# thresholds (cosine between L2-normalised centroids of the same family)
# ---------------------------------------------------------------------------
MIN_SPEECH_S = 6.0        # minimum net speech for a voiceprint: ≥ 3 windows of 3 s at a 1.5 hop
MIN_WINDOWS = 2           # second guard, for pyannote's short turns
T_VOICE_CLUSTER = 0.60    # two unknown voices from different runs are merged from here up
T_VOICE_PROBABILE = 0.65  # "compatible voice" proposal: stricter than merging unknowns
T_VOICE_VERIFICA = 0.50   # "to be verified" proposal; below it nothing is proposed

# reliability tied to the net duration of speech: forensic systems validate by duration,
# and below half a minute the score of a single voice is worth little
AFFIDABILITA_MEDIA_S = 15.0
AFFIDABILITA_ALTA_S = 30.0

NPZ = "voices.npz"


# ---------------------------------------------------------------------------
# models: paths, download, check
# ---------------------------------------------------------------------------
def cartella_modelli() -> Path:
    """The same folder as Silero VAD: ~/.quaesitor/models/diarize (or QUAESITOR_MODELS_DIR)."""
    env = os.environ.get("QUAESITOR_MODELS_DIR")
    base = Path(env) if env else Path.home() / ".quaesitor" / "models"
    return base / "diarize"


def model_file(fam: str) -> str:
    if fam not in VOICE_MODELS:
        raise ValueError(f"modello voce sconosciuto: {fam} (validi: {', '.join(VOICE_MODELS)})")
    return VOICE_MODELS[fam]["file"]


def model_path(fam: str) -> Path:
    return cartella_modelli() / model_file(fam)


def model_url(fam: str) -> str:
    """The asset URL: `CAM++` becomes `CAM%2B%2B`, otherwise GitHub answers 404."""
    return BASE_URL + quote(model_file(fam), safe="")


def model_cached(fam: str) -> bool:
    return model_path(fam).is_file()


def scarica_file(url: str, dest: Path, progress=None, cancel=None) -> Path:
    """Downloads `url` to `dest` through a `.part`; progress(done, total), cancel() -> bool."""
    import urllib.request
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "cognitor"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            if cancel and cancel():
                f.close()
                tmp.unlink(missing_ok=True)
                raise RuntimeError("download annullato")
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if progress:
                progress(done, total)
    tmp.replace(dest)
    return dest


def download_model(fam: str, progress=None, cancel=None) -> Path:
    dest = model_path(fam)
    if dest.is_file():
        return dest
    return scarica_file(model_url(fam), dest, progress=progress, cancel=cancel)


def verifica_dim(session, fam: str) -> int:
    """The dimension declared by the file (`output_dim` metadata of the sherpa-onnx exports)
    must match the catalogue: two different dimensions under the same family
    would produce wrong comparisons without any error."""
    attesa = VOICE_MODELS[fam]["dim"]
    dim = None
    try:
        meta = session.get_modelmeta().custom_metadata_map or {}
        if meta.get("output_dim"):
            dim = int(meta["output_dim"])
    except Exception:  # noqa: BLE001 — no metadata: look at the shape of the output
        pass
    if dim is None:
        try:
            forma = session.get_outputs()[0].shape
            dim = int(forma[-1]) if forma and isinstance(forma[-1], int) else None
        except Exception:  # noqa: BLE001
            dim = None
    if dim is not None and dim != attesa:
        raise RuntimeError(f"il modello voce {fam} produce vettori di {dim} numeri, il catalogo "
                           f"ne dichiara {attesa}: correggere VOICE_MODELS prima di usarlo")
    return dim or attesa


# ---------------------------------------------------------------------------
# voiceprints per speaker
# ---------------------------------------------------------------------------
def affidabilita(speech_seconds: float) -> str:
    """`bassa` below 15 net seconds, `media` below 30 s, `alta` from 30 s up."""
    s = float(speech_seconds or 0.0)
    if s >= AFFIDABILITA_ALTA_S:
        return "alta"
    if s >= AFFIDABILITA_MEDIA_S:
        return "media"
    return "bassa"


def secondi_netti(intervalli) -> float:
    """Length of the union of intervals [(t0, t1)]: the windows overlap by half."""
    tot, fine = 0.0, None
    for a, b in sorted((float(a), float(b)) for a, b in intervalli):
        if fine is None or a > fine:
            tot += b - a
            fine = b
        elif b > fine:
            tot += b - fine
            fine = b
    return round(tot, 2)


def etichetta(label: int) -> str:
    return f"PARLANTE {int(label) + 1}"


def centroidi_per_parlante(embs: np.ndarray, labels, windows, min_speech: float = MIN_SPEECH_S,
                           min_windows: int = MIN_WINDOWS) -> dict:
    """For every speaker: L2 centroid of their windows, or None with the reason.

    Returns {"PARLANTE k": {"centroid", "n_windows", "speech_seconds", "ok", "why",
    "affidabilita"}}. The centroid is the normalised mean of the windows: the same
    computation as `diarize._centroids`, which until now lived and died inside the clustering."""
    labels = np.asarray(labels)
    out = {}
    for lab in sorted(set(int(x) for x in labels.tolist())):
        idx = np.nonzero(labels == lab)[0]
        secondi = secondi_netti([windows[i] for i in idx])
        voce = {"centroid": None, "n_windows": int(len(idx)), "speech_seconds": secondi,
                "ok": False, "why": "", "affidabilita": affidabilita(secondi)}
        if secondi < min_speech:
            voce["why"] = f"parlato insufficiente ({secondi:.1f} s, minimo {min_speech:.0f} s)"
        elif len(idx) < min_windows:
            voce["why"] = f"finestre insufficienti ({len(idx)}, minimo {min_windows})"
        else:
            c = np.asarray(embs[idx], dtype=np.float32).mean(axis=0)
            norma = float(np.linalg.norm(c))
            if norma < 1e-8:
                voce["why"] = "impronta nulla"
            else:
                voce["centroid"] = (c / norma).astype(np.float32)
                voce["ok"] = True
        out[etichetta(lab)] = voce
    return out


def impronte_da_turni(audio: np.ndarray, turni: list, session, cancel=None, log=print):
    """Embeddings for the turns of another diarizer (pyannote), with the same windows
    as the lightweight pipeline. Returns (embs, windows, labels, speakers)."""
    from .diarize import embed_windows, window_plan
    speakers = sorted({t["speaker"] for t in turni})
    indice = {s: i for i, s in enumerate(speakers)}
    windows, labels = [], []
    for t in sorted(turni, key=lambda t: t["t0"]):
        for w in window_plan([(float(t["t0"]), float(t["t1"]))]):
            windows.append(w)
            labels.append(indice[t["speaker"]])
    if not windows:
        return np.zeros((0, 1), dtype=np.float32), [], [], speakers
    embs = embed_windows(audio, windows, session, cancel=cancel, log=log)
    return embs, windows, labels, speakers


def riepilogo_impronte(impronte: dict, family: str, model: str, diarizer: str) -> dict:
    """The `voiceprints` key of transcript.json: metadata only, the vectors are in the npz."""
    return {"family": family, "model": model, "diarizer": diarizer, "file": NPZ,
            "min_speech": MIN_SPEECH_S,
            "speakers": {k: {"ok": v["ok"], "n_windows": v["n_windows"],
                             "speech_seconds": v["speech_seconds"], "affidabilita": v["affidabilita"],
                             **({"why": v["why"]} if v["why"] else {})}
                         for k, v in impronte.items()}}


# ---------------------------------------------------------------------------
# the file next to the transcript
# ---------------------------------------------------------------------------
def scrivi_npz(output_dir, embs, windows, labels, speakers, impronte: dict,
               family: str, model: str, diarizer: str) -> Path:
    """`voices.npz`: the windows and centroids of a run, for recomputation without re-decoding."""
    dim = int(np.asarray(embs).shape[1]) if len(embs) else VOICE_MODELS.get(family, {}).get("dim", 1)
    cents = np.full((len(speakers), dim), np.nan, dtype=np.float32)
    for i, s in enumerate(speakers):
        c = (impronte.get(s) or {}).get("centroid")
        if c is not None:
            cents[i] = c
    dest = Path(output_dir) / NPZ
    np.savez_compressed(
        dest,
        embeddings=np.asarray(embs, dtype=np.float32).reshape(len(embs), -1) if len(embs) else np.zeros((0, dim), np.float32),
        windows=np.asarray(windows, dtype=np.float32).reshape(-1, 2),
        labels=np.asarray(labels, dtype=np.int32),
        speakers=np.asarray(list(speakers)),
        centroids=cents,
        family=np.asarray(family), model=np.asarray(model), diarizer=np.asarray(diarizer))
    return dest


def leggi_npz(output_dir) -> dict | None:
    p = Path(output_dir) / NPZ
    if not p.is_file():
        return None
    with np.load(p, allow_pickle=False) as z:
        return {"embeddings": z["embeddings"], "windows": z["windows"], "labels": z["labels"],
                "speakers": [str(s) for s in z["speakers"].tolist()], "centroids": z["centroids"],
                "family": str(z["family"]), "model": str(z["model"]), "diarizer": str(z["diarizer"])}


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------
def punteggio(a: np.ndarray, b: np.ndarray, coorte: np.ndarray | None = None, top: int = 50) -> float:
    """Cosine between two centroids. With `coorte` [M, d] (other voices of the same family,
    the two excluded) it applies AS-norm: the raw cosine minus the mean of the best `top`
    cosines of each voice against the cohort, divided by their deviation. It reduces
    the channel effect; it is switched on after a measurement on the sample."""
    a = np.asarray(a, dtype=np.float32).ravel()
    b = np.asarray(b, dtype=np.float32).ravel()
    grezzo = float(a @ b)
    if coorte is None or len(coorte) < 2:
        return grezzo
    C = np.asarray(coorte, dtype=np.float32)
    k = min(top, len(C))
    sa = np.sort(C @ a)[-k:]
    sb = np.sort(C @ b)[-k:]
    za = (grezzo - sa.mean()) / max(float(sa.std()), 1e-6)
    zb = (grezzo - sb.mean()) / max(float(sb.std()), 1e-6)
    return float((za + zb) / 2)


def livello(score: float, t_probabile: float = T_VOICE_PROBABILE,
            t_verifica: float = T_VOICE_VERIFICA) -> str | None:
    if score >= t_probabile:
        return "probabile"
    if score >= t_verifica:
        return "da_verificare"
    return None


def candidati_parlante(centroid, family: str, voci_note: list, t_probabile: float = T_VOICE_PROBABILE,
                       t_verifica: float = T_VOICE_VERIFICA) -> list:
    """The people whose voice resembles `centroid`, from the most similar down.

    `voci_note`: [{"eid", "name", "centroid", "family", "speech_seconds"}], one row per
    stored voiceprint. For every person the best voiceprint counts. Different families are
    not compared: an identical vector under another family is not a candidate."""
    if centroid is None:
        return []
    migliori = {}
    for v in voci_note:
        if v.get("family") != family or v.get("centroid") is None:
            continue
        s = punteggio(centroid, v["centroid"])
        eid = str(v["eid"])
        if eid not in migliori or s > migliori[eid]["score"]:
            migliori[eid] = {"eid": eid, "name": v.get("name") or f"ENTITÀ {eid}", "score": round(s, 3),
                             "speech_seconds": float(v.get("speech_seconds") or 0.0),
                             "affidabilita": affidabilita(v.get("speech_seconds") or 0.0)}
    out = []
    for c in migliori.values():
        liv = livello(c["score"], t_probabile, t_verifica)
        if liv:
            out.append({**c, "livello": liv})
    return sorted(out, key=lambda c: -c["score"])


# ---------------------------------------------------------------------------
# groups of voices across runs
# ---------------------------------------------------------------------------
BLOCCO_COPPIE = 512     # rows of M per similarity block (512 x N float32)


def coppie_sopra_soglia(M: np.ndarray, threshold: float, blocco: int = BLOCCO_COPPIE):
    """The pairs (i, j), i < j, with cosine similarity >= `threshold`, most similar first.

    Returns three aligned arrays: the indices i, the indices j and the similarity. With equal
    similarity the order (i, j) applies. The N x N matrix is not built: the
    product is computed in blocks of `blocco` rows, and of every block only the
    pairs above the threshold are kept. Memory follows the useful pairs, not N squared. Until
    2026-09-13 `recluster` kept the whole matrix with the indices of all the pairs:
    about 450 MB for a case with 5,000 unknowns, at every rejection or promotion."""
    M = np.asarray(M, dtype=np.float32)
    n = len(M)
    ii, jj, ss = [], [], []
    for a in range(0, n, max(1, int(blocco))):
        b = min(a + max(1, int(blocco)), n)
        S = M[a:b] @ M[a:].T                      # rows a..b against the columns from a on
        tieni = S >= threshold
        tieni[:, :b - a] &= np.triu(np.ones((b - a, b - a), dtype=bool), k=1)   # only j > i
        r, c = np.nonzero(tieni)
        ii.append(r + a)
        jj.append(c + a)
        ss.append(S[r, c])
    if not ii:
        vuoto = np.zeros(0, dtype=np.int64)
        return vuoto, vuoto.copy(), np.zeros(0, dtype=np.float32)
    ii, jj, ss = np.concatenate(ii), np.concatenate(jj), np.concatenate(ss)
    ordine = np.lexsort((jj, ii, -ss))            # last key = primary
    return ii[ordine], jj[ordine], ss[ordine]


def raggruppa(M: np.ndarray, threshold: float = T_VOICE_CLUSTER) -> list[list[int]]:
    """Groups of rows of `M` [n, d] (L2) by cosine similarity ≥ `threshold`.

    Greedy on the most similar pairs, with union-find and one extra check: two groups
    merge only if their current centroids also exceed the threshold. Without this
    check a chain A~B, B~C would join A and C even when A and C do not resemble each other.
    It is the criterion of the faces: since 2026-09-13 `graphstore.recluster` calls this function
    and no longer keeps a copy of its own. The pairs come from `coppie_sopra_soglia`."""
    n = len(M)
    if n == 0:
        return []
    M = np.asarray(M, dtype=np.float32)
    padre = list(range(n))

    def trova(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    ii, jj, _ = coppie_sopra_soglia(M, threshold)
    somme = {i: M[i].copy() for i in range(n)}
    conteggi = {i: 1 for i in range(n)}
    for i, j in zip(ii.tolist(), jj.tolist()):
        ri, rj = trova(i), trova(j)
        if ri == rj:
            continue
        ci = somme[ri] / max(float(np.linalg.norm(somme[ri])), 1e-8)
        cj = somme[rj] / max(float(np.linalg.norm(somme[rj])), 1e-8)
        if float(ci @ cj) < threshold:
            continue
        padre[rj] = ri
        somme[ri] = somme[ri] + somme[rj]
        conteggi[ri] += conteggi[rj]
        del somme[rj], conteggi[rj]
    gruppi: dict[int, list[int]] = {}
    for i in range(n):
        gruppi.setdefault(trova(i), []).append(i)
    return sorted(gruppi.values(), key=lambda g: (-len(g), g[0]))
