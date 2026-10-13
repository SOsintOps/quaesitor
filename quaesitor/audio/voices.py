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

"""Impronte vocali: di chi è una voce, dentro e fra i video.

La diarizzazione (`diarize.py`) risponde a «quante voci e quando»: per ogni finestra di
3 s calcola un embedding WeSpeaker, li raggruppa e numera i parlanti per ordine di prima
comparsa. Fino alla 0.16.0 gli embedding venivano scartati subito dopo: «PARLANTE 1» di
due video diversi non aveva nulla in comune se non l'etichetta. Questo modulo conserva
l'impronta di ogni parlante (il centroide delle sue finestre) e la rende confrontabile
fra run, fra video e con le persone del caso.

Tre regole, prese dai volti:
- **la famiglia**: modelli diversi producono vettori non confrontabili. La famiglia è l'id
  del modello (`wr34`, `wcam`, `wr293`) e accompagna ogni impronta, nel file, nel
  database e nel faldone. Il confronto avviene solo dentro la stessa famiglia.
- **il minimo di parlato**: sotto `MIN_SPEECH_S` secondi netti il centroide è una finestra
  rumorosa, non una voce. Il parlante mantiene la sua etichetta nel trascritto, ma non
  entra nei confronti, e il motivo è scritto (`why`).
- **nessuna fusione automatica**: il modulo produce punteggi e proposte. Collegare una voce
  a una persona è un atto dell'analista, registrato e annullabile.

Le soglie sono coseni fra centroidi L2-normalizzati (`T_VOICE_*`). Non vanno confuse con
`diarize.CLUSTER_THRESHOLD`, che è una **distanza** (0,70 = similarità 0,30) fra finestre
singole con average linkage: un'altra operazione. Un centroide di molte finestre è più
stabile di una finestra sola, quindi le stesse voci risultano più simili e le soglie
stanno più in alto.

Che cosa non è: un confronto vocale forense. Quello richiede una coorte di riferimento,
una calibrazione a rapporto di verosimiglianza e un perito. Qui il punteggio è un indizio
investigativo, accompagnato dai secondi di parlato e da un livello di affidabilità legato
alla durata (`affidabilita`). La normalizzazione su coorte (`punteggio(..., coorte=...)`)
è predisposta per ridurre l'effetto del canale, e si attiva dopo una misura sul campione.
"""
# «You know my method. It is founded upon the observation of trifles.»
#   A. Conan Doyle, The Boscombe Valley Mystery
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

import numpy as np

# ---------------------------------------------------------------------------
# catalogo dei modelli voce (WeSpeaker, export ONNX di sherpa-onnx)
# ---------------------------------------------------------------------------
BASE_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/"

# Tutti gli export WeSpeaker hanno un solo input [B, T, 80] (fbank di diarize.fbank, scala
# int16, CMN) e un solo output [B, dim]. Il numero di parametri e l'errore (EER su
# VoxCeleb1-O, dal model zoo di WeSpeaker) sono nelle note. `dim` si verifica sui metadati
# del file al primo uso (`verifica_dim`): se il catalogo sbaglia, l'errore lo dice.
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
# soglie (coseno fra centroidi L2-normalizzati della stessa famiglia)
# ---------------------------------------------------------------------------
MIN_SPEECH_S = 6.0        # parlato netto minimo per un'impronta: ≥ 3 finestre da 3 s a passo 1,5
MIN_WINDOWS = 2           # seconda guardia, per i turni corti di pyannote
T_VOICE_CLUSTER = 0.60    # due voci sconosciute di run diverse si uniscono da qui in su
T_VOICE_PROBABILE = 0.65  # proposta «voce compatibile»: più severa della fusione fra sconosciuti
T_VOICE_VERIFICA = 0.50   # proposta «da verificare»; sotto non si propone nulla

# affidabilità legata alla durata netta di parlato: i sistemi forensi validano per durata,
# e sotto la mezza minuto il punteggio di una voce sola vale poco
AFFIDABILITA_MEDIA_S = 15.0
AFFIDABILITA_ALTA_S = 30.0

NPZ = "voices.npz"


# ---------------------------------------------------------------------------
# modelli: percorsi, download, verifica
# ---------------------------------------------------------------------------
def cartella_modelli() -> Path:
    """La stessa cartella di Silero VAD: ~/.quaesitor/models/diarize (o QUAESITOR_MODELS_DIR)."""
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
    """L'URL dell'asset: `CAM++` diventa `CAM%2B%2B`, altrimenti GitHub risponde 404."""
    return BASE_URL + quote(model_file(fam), safe="")


def model_cached(fam: str) -> bool:
    return model_path(fam).is_file()


def scarica_file(url: str, dest: Path, progress=None, cancel=None) -> Path:
    """Scarica `url` in `dest` passando da un `.part`; progress(fatti, totale), cancel() -> bool."""
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
    """La dimensione dichiarata dal file (metadato `output_dim` degli export sherpa-onnx)
    deve coincidere con il catalogo: due dimensioni diverse sotto la stessa famiglia
    produrrebbero confronti sbagliati senza alcun errore."""
    attesa = VOICE_MODELS[fam]["dim"]
    dim = None
    try:
        meta = session.get_modelmeta().custom_metadata_map or {}
        if meta.get("output_dim"):
            dim = int(meta["output_dim"])
    except Exception:  # noqa: BLE001 — metadati assenti: si guarda la forma dell'uscita
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
# impronte per parlante
# ---------------------------------------------------------------------------
def affidabilita(speech_seconds: float) -> str:
    """`bassa` sotto 15 s netti, `media` sotto 30 s, `alta` da 30 s in su."""
    s = float(speech_seconds or 0.0)
    if s >= AFFIDABILITA_ALTA_S:
        return "alta"
    if s >= AFFIDABILITA_MEDIA_S:
        return "media"
    return "bassa"


def secondi_netti(intervalli) -> float:
    """Lunghezza dell'unione di intervalli [(t0, t1)]: le finestre si sovrappongono a metà."""
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
    """Per ogni parlante: centroide L2 delle sue finestre, o None con il motivo.

    Ritorna {"PARLANTE k": {"centroid", "n_windows", "speech_seconds", "ok", "why",
    "affidabilita"}}. Il centroide è la media delle finestre normalizzata: lo stesso
    calcolo di `diarize._centroids`, che finora viveva e moriva dentro il clustering."""
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
    """Embedding per i turni di un altro diarizzatore (pyannote), con le stesse finestre
    della pipeline leggera. Ritorna (embs, windows, labels, speakers)."""
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
    """La chiave `voiceprints` di transcript.json: solo metadati, i vettori stanno nel npz."""
    return {"family": family, "model": model, "diarizer": diarizer, "file": NPZ,
            "min_speech": MIN_SPEECH_S,
            "speakers": {k: {"ok": v["ok"], "n_windows": v["n_windows"],
                             "speech_seconds": v["speech_seconds"], "affidabilita": v["affidabilita"],
                             **({"why": v["why"]} if v["why"] else {})}
                         for k, v in impronte.items()}}


# ---------------------------------------------------------------------------
# il file accanto al trascritto
# ---------------------------------------------------------------------------
def scrivi_npz(output_dir, embs, windows, labels, speakers, impronte: dict,
               family: str, model: str, diarizer: str) -> Path:
    """`voices.npz`: le finestre e i centroidi di una run, per ricalcoli senza ridecodificare."""
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
# confronto
# ---------------------------------------------------------------------------
def punteggio(a: np.ndarray, b: np.ndarray, coorte: np.ndarray | None = None, top: int = 50) -> float:
    """Coseno fra due centroidi. Con `coorte` [M, d] (altre voci della stessa famiglia,
    escluse le due) applica AS-norm: il coseno grezzo meno la media dei migliori `top`
    coseni di ciascuna voce contro la coorte, diviso per la loro deviazione. Riduce
    l'effetto del canale; si attiva dopo una misura sul campione."""
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
    """Le persone la cui voce assomiglia a `centroid`, dalla più simile in giù.

    `voci_note`: [{"eid", "name", "centroid", "family", "speech_seconds"}], una riga per
    impronta archiviata. Per ogni persona conta l'impronta migliore. Famiglie diverse non
    si confrontano: un vettore identico sotto un'altra famiglia non è un candidato."""
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
# gruppi di voci fra run
# ---------------------------------------------------------------------------
BLOCCO_COPPIE = 512     # righe di M per ogni blocco di similarita' (512 x N float32)


def coppie_sopra_soglia(M: np.ndarray, threshold: float, blocco: int = BLOCCO_COPPIE):
    """Le coppie (i, j), i < j, con similarita' coseno >= `threshold`, dalla piu' simile.

    Ritorna tre array allineati: gli indici i, gli indici j e la similarita'. A parita'
    di similarita' vale l'ordine (i, j). La matrice N x N non viene costruita: il
    prodotto si calcola per blocchi di `blocco` righe, e di ogni blocco restano le sole
    coppie sopra soglia. La memoria segue le coppie utili, non N al quadrato. Fino al
    2026-09-13 `recluster` teneva la matrice intera con gli indici di tutte le coppie:
    circa 450 MB per un caso da 5.000 sconosciuti, a ogni scarto o promozione."""
    M = np.asarray(M, dtype=np.float32)
    n = len(M)
    ii, jj, ss = [], [], []
    for a in range(0, n, max(1, int(blocco))):
        b = min(a + max(1, int(blocco)), n)
        S = M[a:b] @ M[a:].T                      # righe a..b contro le colonne da a in poi
        tieni = S >= threshold
        tieni[:, :b - a] &= np.triu(np.ones((b - a, b - a), dtype=bool), k=1)   # solo j > i
        r, c = np.nonzero(tieni)
        ii.append(r + a)
        jj.append(c + a)
        ss.append(S[r, c])
    if not ii:
        vuoto = np.zeros(0, dtype=np.int64)
        return vuoto, vuoto.copy(), np.zeros(0, dtype=np.float32)
    ii, jj, ss = np.concatenate(ii), np.concatenate(jj), np.concatenate(ss)
    ordine = np.lexsort((jj, ii, -ss))            # ultima chiave = principale
    return ii[ordine], jj[ordine], ss[ordine]


def raggruppa(M: np.ndarray, threshold: float = T_VOICE_CLUSTER) -> list[list[int]]:
    """Gruppi di righe di `M` [n, d] (L2) per similarità coseno ≥ `threshold`.

    Greedy sulle coppie più simili, con union-find e una verifica in più: due gruppi si
    fondono solo se anche i loro centroidi correnti superano la soglia. Senza questa
    verifica una catena A~B, B~C unirebbe A e C anche quando A e C non si somigliano.
    È il criterio dei volti: dal 2026-09-13 `graphstore.recluster` chiama questa funzione
    e non tiene piu' una copia propria. Le coppie arrivano da `coppie_sopra_soglia`."""
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
