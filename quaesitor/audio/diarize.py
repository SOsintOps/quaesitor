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

"""Diarizzazione leggera (ROADMAP Fase 2): quante persone parlano nel video.

Pipeline interamente su onnxruntime (niente PyTorch), tutta offline:
  1. Silero VAD (ONNX)            -> regioni di parlato;
  2. finestre di 3 s (passo 1,5 s) dentro le regioni -> fbank 80 bande
     (stile Kaldi, calcolato in numpy) -> embedding voce con un modello WeSpeaker
     del catalogo di `voices.py` (ONNX, addestrato su VoxCeleb; ResNet34-LM predefinito);
  3. clustering agglomerativo (distanza coseno, average linkage) -> PARLANTE 1..N;
  4. ogni segmento del transcript riceve il parlante che lo copre di più;
  5. per ogni parlante il centroide delle sue finestre diventa l'impronta vocale
     (`voices.centroidi_per_parlante`), scritta in `voices.npz` accanto al trascritto.

Silero VAD (~2 MB) e il modello voce scelto vengono scaricati al primo uso in
~/.quaesitor/models/diarize/ (override con la variabile QUAESITOR_MODELS_DIR).
Senza il pacchetto audio (requirements-audio.txt) o senza modelli la funzione
solleva RuntimeError con un messaggio chiaro: la trascrizione esce comunque,
solo senza parlanti.
"""
# «Nothing clears up a case so much as stating it to another person.»
#   A. Conan Doyle, Silver Blaze
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from . import voices
from .voices import DEFAULT_VOICE

SAMPLE_RATE = 16000
VAD_FILE = "silero_vad.onnx"
VAD_URL = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
VAD_SIZE_MB = 2

# parametri della pipeline (valori di default, tarati su voci sintetiche e reali)
WINDOW_SEC = 3.0          # finestra di embedding (più lunga = embedding più stabile su audio reale)
HOP_SEC = 1.5             # passo tra finestre
MIN_WINDOW_SEC = 0.6      # regioni più corte vengono ignorate
CLUSTER_THRESHOLD = 0.70  # distanza coseno oltre la quale due gruppi restano separati
MIN_CLUSTER_FRAC = 0.04   # gruppi sotto questa quota di finestre (min 2) vengono assorbiti dal più vicino


# ---------------------------------------------------------------------------
# modelli: cache e download
# ---------------------------------------------------------------------------
def models_dir() -> Path:
    """La cartella dei modelli di diarizzazione: Silero VAD e i modelli voce del catalogo."""
    return voices.cartella_modelli()


def vad_cached() -> bool:
    return (models_dir() / VAD_FILE).is_file()


def models_cached(voice: str = DEFAULT_VOICE) -> bool:
    """VAD e il modello voce indicato sono entrambi in cache."""
    return vad_cached() and voices.model_cached(voice)


def download_models(progress=None, cancel=None, voice: str = DEFAULT_VOICE) -> Path:
    """Scarica ciò che manca fra VAD e modello voce; progress(fatti, totale), cancel() -> bool."""
    d = models_dir()
    if not vad_cached():
        voices.scarica_file(VAD_URL, d / VAD_FILE, progress=progress, cancel=cancel)
    voices.download_model(voice, progress=progress, cancel=cancel)
    return d


def _session(path: Path, use_gpu: bool = False):
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.log_severity_level = 3
    from .accelerator import precarica_cuda, scegli_provider
    precarica_cuda(ort, use_gpu)
    providers, _ = scegli_provider(use_gpu, ort.get_available_providers())
    return ort.InferenceSession(str(path), sess_options=opts, providers=providers)


# ---------------------------------------------------------------------------
# audio
# ---------------------------------------------------------------------------
def decode_audio(path) -> np.ndarray:
    """Audio mono float32 a 16 kHz, decodificato dal video con PyAV (via faster-whisper)."""
    try:
        from faster_whisper.audio import decode_audio as _dec
    except ImportError:
        raise RuntimeError(
            "supporto audio non installato: pip install -r requirements-audio.txt")
    audio = _dec(str(path), sampling_rate=SAMPLE_RATE)
    return np.asarray(audio, dtype=np.float32).reshape(-1)


# ---------------------------------------------------------------------------
# 1) Silero VAD
# ---------------------------------------------------------------------------
def vad_regions(audio: np.ndarray, session, threshold: float = 0.5,
                min_speech: float = 0.25, min_silence: float = 0.10,
                pad: float = 0.03, cancel=None) -> list[tuple[float, float]]:
    """Regioni di parlato [(t0, t1), ...] in secondi (logica di get_speech_timestamps)."""
    chunk, ctx = 512, 64
    n = len(audio)
    if n % chunk:
        audio = np.concatenate([audio, np.zeros(chunk - n % chunk, dtype=np.float32)])
    state = np.zeros((2, 1, 128), dtype=np.float32)
    context = np.zeros((1, ctx), dtype=np.float32)
    sr = np.array(SAMPLE_RATE, dtype=np.int64)
    probs = []
    for i in range(0, len(audio), chunk):
        if cancel and (i // chunk) % 200 == 0 and cancel():
            raise RuntimeError("interrotto dall'utente")
        x = np.concatenate([context, audio[i:i + chunk][None, :]], axis=1)
        out, state = session.run(None, {"input": x, "state": state, "sr": sr})
        context = x[:, -ctx:]
        probs.append(float(out[0, 0]))

    neg = max(threshold - 0.15, 0.01)
    step = chunk / SAMPLE_RATE
    regions, start, silence_from = [], None, None
    for k, p in enumerate(probs):
        t = k * step
        if p >= threshold:
            if start is None:
                start = t
            silence_from = None
        elif start is not None and p < neg:
            if silence_from is None:
                silence_from = t
            elif t - silence_from >= min_silence:
                if silence_from - start >= min_speech:
                    regions.append((start, silence_from))
                start, silence_from = None, None
    if start is not None:
        end = len(probs) * step
        if end - start >= min_speech:
            regions.append((start, end))
    total = n / SAMPLE_RATE
    return [(max(0.0, a - pad), min(total, b + pad)) for a, b in regions]


# ---------------------------------------------------------------------------
# 2) fbank stile Kaldi (80 bande, 25/10 ms, hamming, pre-enfasi, log, CMN)
# ---------------------------------------------------------------------------
_MEL_CACHE: dict = {}


def _mel_banks(num_bins=80, n_fft=512, sr=SAMPLE_RATE, low=20.0, high=0.0):
    key = (num_bins, n_fft, sr, low, high)
    if key in _MEL_CACHE:
        return _MEL_CACHE[key]
    nyq = sr / 2.0
    high = nyq + high if high <= 0 else high
    mel = lambda f: 1127.0 * math.log(1.0 + f / 700.0)  # noqa: E731
    m_low, m_high = mel(low), mel(high)
    delta = (m_high - m_low) / (num_bins + 1)
    n_bins = n_fft // 2
    freqs = np.arange(n_bins) * (sr / n_fft)
    m_freqs = 1127.0 * np.log(1.0 + freqs / 700.0)
    banks = np.zeros((num_bins, n_bins), dtype=np.float32)
    for i in range(num_bins):
        left, center, right = m_low + i * delta, m_low + (i + 1) * delta, m_low + (i + 2) * delta
        up = (m_freqs - left) / (center - left)
        down = (right - m_freqs) / (right - center)
        banks[i] = np.maximum(0.0, np.minimum(up, down))
    _MEL_CACHE[key] = banks
    return banks


def fbank(wave: np.ndarray, num_bins: int = 80) -> np.ndarray:
    """Log-mel filterbank [T, num_bins] di un'onda float32 (-1..1) a 16 kHz,
    compatibile con kaldi.fbank(dither=0, window='hamming') usato da WeSpeaker."""
    x = np.asarray(wave, dtype=np.float32) * 32768.0      # scala int16 come Kaldi
    win, hop, n_fft = 400, 160, 512
    if len(x) < win:
        x = np.concatenate([x, np.zeros(win - len(x), dtype=np.float32)])
    n_frames = 1 + (len(x) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n_frames)[:, None]
    frames = x[idx]
    frames = frames - frames.mean(axis=1, keepdims=True)          # remove_dc_offset
    pre = np.empty_like(frames)                                    # pre-enfasi 0.97
    pre[:, 1:] = frames[:, 1:] - 0.97 * frames[:, :-1]
    pre[:, 0] = frames[:, 0] - 0.97 * frames[:, 0]
    window = (0.54 - 0.46 * np.cos(2 * np.pi * np.arange(win) / (win - 1))).astype(np.float32)
    spec = np.fft.rfft(pre * window, n=n_fft, axis=1)[:, :n_fft // 2]
    power = (spec.real ** 2 + spec.imag ** 2).astype(np.float32)
    mel = power @ _mel_banks(num_bins, n_fft).T
    feats = np.log(np.maximum(mel, np.finfo(np.float32).eps))
    return (feats - feats.mean(axis=0, keepdims=True)).astype(np.float32)  # CMN


# ---------------------------------------------------------------------------
# 3) embedding per finestra + clustering
# ---------------------------------------------------------------------------
def window_plan(regions, window=WINDOW_SEC, hop=HOP_SEC, min_len=MIN_WINDOW_SEC):
    """Finestre [(t0, t1)] che coprono le regioni di parlato."""
    wins = []
    for a, b in regions:
        if b - a < min_len:
            continue
        if b - a <= window:
            wins.append((a, b))
            continue
        t = a
        while t + window <= b + 1e-6:
            wins.append((t, t + window))
            t += hop
        if wins[-1][1] < b - hop / 2:       # coda residua
            wins.append((b - window, b))
    return wins


def embed_windows(audio: np.ndarray, wins, session, cancel=None, log=print,
                  batch: int = 16) -> np.ndarray:
    """Embedding L2-normalizzati [N, 256] delle finestre (batch a lunghezza uguale)."""
    name = session.get_inputs()[0].name
    embs = None                                       # allocato alla prima uscita (dim del modello)
    feats = []
    for (a, b) in wins:
        seg = audio[int(a * SAMPLE_RATE):int(b * SAMPLE_RATE)]
        feats.append(fbank(seg))
    order = sorted(range(len(wins)), key=lambda i: feats[i].shape[0])
    done = 0
    i = 0
    last_log, every = 0, max(1, len(wins) // 20)     # al massimo ~20 righe di progresso
    while i < len(order):
        T = feats[order[i]].shape[0]
        grp = [order[i]]
        while len(grp) < batch and i + len(grp) < len(order) and feats[order[i + len(grp)]].shape[0] == T:
            grp.append(order[i + len(grp)])
        if cancel and cancel():
            raise RuntimeError("interrotto dall'utente")
        x = np.stack([feats[j] for j in grp]).astype(np.float32)
        out = session.run(None, {name: x})[0]
        if embs is None:
            embs = np.zeros((len(wins), out.shape[-1]), dtype=np.float32)
        for j, e in zip(grp, out):
            embs[j] = e
        i += len(grp)
        done += len(grp)
        if done - last_log >= every or done == len(wins):
            last_log = done
            log(f"[diarize] {done}/{len(wins)}")
    if embs is None:
        return np.zeros((0, 1), dtype=np.float32)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    return embs / np.maximum(norms, 1e-8)


def _centroids(embs: np.ndarray, labels: np.ndarray, ids) -> np.ndarray:
    cents = np.stack([embs[labels == i].mean(axis=0) for i in ids])
    return cents / np.maximum(np.linalg.norm(cents, axis=1, keepdims=True), 1e-8)


def cluster_embeddings(embs: np.ndarray, threshold: float = CLUSTER_THRESHOLD,
                       num_speakers: int = 0, min_size: int = 0) -> np.ndarray:
    """Etichette intere (0..K-1) per finestra: clustering agglomerativo a distanza coseno
    (average linkage), poi i gruppi minuscoli vengono assorbiti e ogni finestra viene
    ri-assegnata al centroide più vicino (pulisce i bordi dei turni).
    num_speakers > 0 forza il numero di gruppi; 0 = automatico (soglia).
    min_size: finestre minime perché un gruppo sia un parlante (0 = MIN_CLUSTER_FRAC)."""
    n = len(embs)
    if n == 0:
        return np.zeros(0, dtype=int)
    if n == 1:
        return np.zeros(1, dtype=int)
    from scipy.cluster.hierarchy import linkage, fcluster
    Z = linkage(embs, method="average", metric="cosine")
    if num_speakers and num_speakers > 0:
        labels = fcluster(Z, t=min(num_speakers, n), criterion="maxclust")
    else:
        labels = fcluster(Z, t=threshold, criterion="distance")
    labels = labels - 1
    if not num_speakers:
        # gruppi minuscoli -> assorbiti dal centroide più vicino tra quelli "veri"
        min_size = min_size or max(2, int(round(MIN_CLUSTER_FRAC * n)))
        ids, counts = np.unique(labels, return_counts=True)
        big = [i for i, c in zip(ids, counts) if c >= min_size]
        if big and len(big) < len(ids):
            cents = _centroids(embs, labels, big)
            for i in ids:
                if i not in big:
                    sims = embs[labels == i] @ cents.T
                    labels[labels == i] = np.array(big)[sims.argmax(axis=1)]
    # ri-assegnazione finale al centroide più vicino (un passo di k-means)
    ids = np.unique(labels)
    if len(ids) > 1:
        cents = _centroids(embs, labels, ids)
        labels = ids[(embs @ cents.T).argmax(axis=1)]
    # rinumera per ordine di prima comparsa
    remap, out = {}, np.zeros_like(labels)
    for k, lab in enumerate(labels):
        remap.setdefault(lab, len(remap))
        out[k] = remap[lab]
    return out


# ---------------------------------------------------------------------------
# 4) pipeline completa e assegnazione ai segmenti
# ---------------------------------------------------------------------------
def speaker_turns(wins, labels) -> list[dict]:
    """Fonde finestre consecutive con la stessa etichetta in turni di parola."""
    turns = []
    for (a, b), lab in sorted(zip(wins, labels), key=lambda w: w[0][0]):
        name = f"PARLANTE {int(lab) + 1}"
        if turns and turns[-1]["speaker"] == name and a <= turns[-1]["t1"] + 1e-6:
            turns[-1]["t1"] = max(turns[-1]["t1"], b)
        else:
            turns.append({"t0": round(float(a), 2), "t1": round(float(b), 2), "speaker": name})
    for t in turns:
        t["t0"], t["t1"] = round(t["t0"], 2), round(t["t1"], 2)
    return turns


def assign_speakers(segments: list[dict], wins, labels) -> None:
    """Scrive segment["speaker"] = "PARLANTE k" per copertura prevalente (in place)."""
    if not wins:
        return
    w0 = np.array([w[0] for w in wins]); w1 = np.array([w[1] for w in wins])
    labels = np.asarray(labels)
    for s in segments:
        a, b = float(s["t0"]), float(s["t1"])
        ov = np.minimum(w1, b) - np.maximum(w0, a)
        if (ov > 0).any():
            cover = {}
            for lab, o in zip(labels[ov > 0], ov[ov > 0]):
                cover[int(lab)] = cover.get(int(lab), 0.0) + float(o)
            best = max(cover.items(), key=lambda kv: kv[1])[0]
        else:                                     # nessuna finestra: la più vicina nel tempo
            mid = (a + b) / 2
            best = int(labels[np.argmin(np.abs((w0 + w1) / 2 - mid))])
        s["speaker"] = f"PARLANTE {best + 1}"


def diarize_audio(audio: np.ndarray, use_gpu: bool = False, num_speakers: int = 0,
                  threshold: float = CLUSTER_THRESHOLD, cancel=None, log=print,
                  voice_model: str = DEFAULT_VOICE) -> dict:
    """Diarizza un'onda 16 kHz. Ritorna {"speakers": N, "windows": [...], "labels": [...],
    "turns": [...], "speech": secondi di parlato, "embeddings": [N, d], "family", "model"}."""
    if not models_cached(voice_model):
        peso = VAD_SIZE_MB + voices.VOICE_MODELS[voice_model]["size_mb"]
        log(f"[diarize] scarico i modelli (~{peso} MB) in {models_dir()}")
        download_models(cancel=cancel, voice=voice_model)
    d = models_dir()
    vad = _session(d / VAD_FILE, use_gpu=False)      # piccolo: CPU basta
    regions = vad_regions(audio, vad, cancel=cancel)
    speech = sum(b - a for a, b in regions)
    log(f"[diarize] parlato: {speech:.0f}s in {len(regions)} regioni")
    wins = window_plan(regions)
    base = {"family": voice_model, "model": voices.model_file(voice_model)}
    if not wins:
        return {"speakers": 0, "windows": [], "labels": [], "turns": [], "speech": round(speech, 2),
                "embeddings": np.zeros((0, voices.VOICE_MODELS[voice_model]["dim"]), np.float32), **base}
    emb_sess = _session(voices.model_path(voice_model), use_gpu=use_gpu)
    voices.verifica_dim(emb_sess, voice_model)
    embs = embed_windows(audio, wins, emb_sess, cancel=cancel, log=log)
    labels = cluster_embeddings(embs, threshold=threshold, num_speakers=num_speakers)
    n = int(labels.max()) + 1 if len(labels) else 0
    log(f"[diarize] parlanti stimati: {n}" if n != 1 else "[diarize] un solo parlante")
    return {"speakers": n, "windows": wins, "labels": labels.tolist(),
            "turns": speaker_turns(wins, labels), "speech": round(speech, 2),
            "embeddings": embs, **base}


def _annota_impronte(transcript: dict, embs, wins, labels, speakers, family, model, diarizer, log=print):
    """Scrive in `transcript` la chiave `voiceprints` (metadati) e `_voices` (i vettori,
    chiave privata che transcribe.py toglie prima di scrivere il JSON)."""
    impronte = voices.centroidi_per_parlante(embs, labels, wins)
    for s in speakers:                       # parlanti senza finestre (pyannote): assenti, con motivo
        impronte.setdefault(s, {"centroid": None, "n_windows": 0, "speech_seconds": 0.0, "ok": False,
                                "why": "nessuna finestra di parlato", "affidabilita": "bassa"})
    transcript["voiceprints"] = voices.riepilogo_impronte(impronte, family, model, diarizer)
    transcript["_voices"] = {"embeddings": embs, "windows": wins, "labels": labels, "speakers": speakers,
                             "impronte": impronte, "family": family, "model": model, "diarizer": diarizer}
    ok = [k for k, v in impronte.items() if v["ok"]]
    senza = [f"{k}: {v['why']}" for k, v in impronte.items() if not v["ok"]]
    log(f"[diarize] impronte vocali ({family}): {len(ok)} parlanti su {len(impronte)}"
        + (" (" + "; ".join(senza) + ")" if senza else ""))


def add_speakers(video_path, transcript: dict, use_gpu: bool = False, num_speakers: int = 0,
                 cancel=None, log=print, audio: np.ndarray | None = None,
                 voice_model: str = DEFAULT_VOICE) -> dict:
    """Arricchisce un transcript (dict di transcribe_video) con i parlanti e le impronte, in place.
    Ritorna il dict; in caso di problemi solleva RuntimeError (chiamante decide il fallback)."""
    if audio is None:
        audio = decode_audio(video_path)
    res = diarize_audio(audio, use_gpu=use_gpu, num_speakers=num_speakers, cancel=cancel, log=log,
                        voice_model=voice_model)
    assign_speakers(transcript.get("segments", []), res["windows"], res["labels"])
    transcript["speakers"] = res["speakers"]
    transcript["speaker_turns"] = res["turns"]
    transcript["speech_seconds"] = res["speech"]
    if res.get("embeddings") is not None and len(res["windows"]):
        speakers = [voices.etichetta(k) for k in range(res["speakers"])]
        _annota_impronte(transcript, res["embeddings"], res["windows"], res["labels"], speakers,
                         res.get("family", voice_model), res.get("model", ""), "leggera", log=log)
    return transcript


# ---------------------------------------------------------------------------
# pyannote.audio: diarizzazione avanzata, facoltativa (ROADMAP Fase 4)
# ---------------------------------------------------------------------------
PYANNOTE_PIPELINE = "pyannote/speaker-diarization-3.1"


def pyannote_status(token: str = "") -> dict:
    """Che cosa manca per usare pyannote: {ready, torch, pyannote, token, why}.

    Serve un ambiente più pesante (PyTorch) e un **token di Hugging Face personale**,
    perché il modello va accettato sul sito prima di poterlo scaricare. Il token è
    dell'analista: il programma non ne ha uno proprio e non lo chiede a nessuno.
    """
    stato = {"ready": False, "torch": False, "pyannote": False,
             "token": bool((token or "").strip()), "why": ""}
    try:
        import torch  # noqa: F401
        stato["torch"] = True
    except Exception:  # noqa: BLE001
        stato["why"] = "PyTorch non è installato (pip install torch, ~2,5 GB)"
    try:
        import pyannote.audio  # noqa: F401
        stato["pyannote"] = True
    except Exception:  # noqa: BLE001
        stato["why"] = stato["why"] or "pyannote.audio non è installato (pip install pyannote.audio)"
    if not stato["token"]:
        stato["why"] = stato["why"] or ("manca il token di Hugging Face: si ottiene sul sito, "
                                        "dopo aver accettato le condizioni del modello "
                                        + PYANNOTE_PIPELINE)
    stato["ready"] = stato["torch"] and stato["pyannote"] and stato["token"]
    return stato


def diarize_pyannote(video_path, transcript: dict, token: str, num_speakers: int = 0,
                     use_gpu: bool = False, log=print, voice_model: str | None = None,
                     audio: np.ndarray | None = None, cancel=None) -> dict:
    """Diarizzazione con pyannote.audio. Solleva RuntimeError se non è utilizzabile:
    il chiamante ripiega sulla diarizzazione leggera.

    pyannote consegna turni, non impronte: con `voice_model` le impronte si calcolano sui
    suoi turni con il modello WeSpeaker del catalogo, così una run pyannote entra negli
    stessi confronti di una run leggera. Se il modello manca o fallisce, i parlanti restano
    validi e il log lo dichiara."""
    stato = pyannote_status(token)
    if not stato["ready"]:
        raise RuntimeError(stato["why"] or "pyannote non disponibile")
    from pyannote.audio import Pipeline
    log(f"[diarize] pyannote: carico {PYANNOTE_PIPELINE}")
    pipeline = Pipeline.from_pretrained(PYANNOTE_PIPELINE, use_auth_token=token.strip())
    if use_gpu:
        try:
            import torch
            if torch.cuda.is_available():
                pipeline.to(torch.device("cuda"))
        except Exception:  # noqa: BLE001 — resta su CPU
            pass
    kwargs = {"num_speakers": int(num_speakers)} if num_speakers else {}
    annotazione = pipeline(str(video_path), **kwargs)

    # stesse chiavi t0/t1 dei turni della diarizzazione leggera (speaker_turns) e dei
    # segmenti di transcribe_video: un lettore solo per i due diarizzatori
    turni = [{"speaker": f"PARLANTE {int(str(spk).split('_')[-1]) + 1}"
              if str(spk).upper().startswith("SPEAKER") else str(spk),
              "t0": round(float(seg.start), 2), "t1": round(float(seg.end), 2)}
             for seg, _track, spk in annotazione.itertracks(yield_label=True)]
    turni.sort(key=lambda t: t["t0"])
    for s in transcript.get("segments", []):          # a ogni segmento il parlante che
        centro = (float(s["t0"]) + float(s["t1"])) / 2          # copre il suo centro
        scelto = next((t["speaker"] for t in turni if t["t0"] <= centro <= t["t1"]), None)
        if scelto is None and turni:                  # nessuna sovrapposizione: il più vicino
            scelto = min(turni, key=lambda t: min(abs(t["t0"] - centro),
                                                  abs(t["t1"] - centro)))["speaker"]
        if scelto:
            s["speaker"] = scelto
    parlanti = sorted({t["speaker"] for t in turni})
    transcript["speakers"] = len(parlanti)
    transcript["speaker_turns"] = turni
    transcript["diarizer"] = "pyannote"
    log(f"[diarize] pyannote: {len(parlanti)} parlanti in {len(turni)} turni")
    if voice_model and turni:
        try:
            if audio is None:
                audio = decode_audio(video_path)
            if not models_cached(voice_model):
                download_models(cancel=cancel, voice=voice_model)
            sess = _session(voices.model_path(voice_model), use_gpu=use_gpu)
            voices.verifica_dim(sess, voice_model)
            embs, wins, labels, speakers = voices.impronte_da_turni(audio, turni, sess, cancel=cancel, log=log)
            _annota_impronte(transcript, embs, wins, labels, speakers, voice_model,
                             voices.model_file(voice_model), "pyannote", log=log)
        except Exception as e:  # noqa: BLE001 — i turni di pyannote valgono anche senza impronte
            log(f"[diarize] impronte vocali non calcolate ({e})")
    return transcript


def add_speakers_auto(video_path, transcript: dict, use_gpu: bool = False,
                      num_speakers: int = 0, cancel=None, log=print,
                      audio=None, token: str = "", prefer_pyannote: bool = False,
                      voice_model: str = DEFAULT_VOICE) -> dict:
    """Diarizzazione: pyannote se richiesto e utilizzabile, altrimenti quella leggera.

    Il ripiego è automatico e dichiarato nel log: chi lavora deve sapere quale dei due
    ha prodotto le etichette, perché la qualità è diversa."""
    if prefer_pyannote:
        try:
            return diarize_pyannote(video_path, transcript, token, num_speakers=num_speakers,
                                    use_gpu=use_gpu, log=log, voice_model=voice_model,
                                    audio=audio, cancel=cancel)
        except Exception as e:  # noqa: BLE001
            log(f"[diarize] pyannote non utilizzabile ({e}): uso la diarizzazione leggera")
    out = add_speakers(video_path, transcript, use_gpu=use_gpu, num_speakers=num_speakers,
                       cancel=cancel, log=log, audio=audio, voice_model=voice_model)
    out["diarizer"] = "leggera"
    return out
