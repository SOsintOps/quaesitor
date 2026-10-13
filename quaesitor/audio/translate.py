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

"""Traduzione del trascritto (ROADMAP Fase 3): inglese e italiano, tutto offline.

- Verso l'**inglese**: traduzione nativa di Whisper (seconda passata del modello
  con `task="translate"`), riallineata ai segmenti della trascrizione per
  sovrapposizione temporale. Se l'audio è già in inglese non serve nulla.
- Verso l'**italiano**: pacchetto lingua di **Argos Translate** `en_it`
  (modello CTranslate2 + SentencePiece) caricato direttamente con ctranslate2
  — niente pacchetto `argostranslate` (che richiederebbe stanza/PyTorch).
  Sorgenti diverse dall'inglese passano per l'inglese (pivot = la traduzione
  Whisper del punto sopra). Se l'audio è già in italiano non serve nulla.

Il pacchetto `.argosmodel` (~88 MB) viene scaricato al primo uso in
~/.quaesitor/models/translate/ (override con QUAESITOR_MODELS_DIR); i modelli
arrivano dall'indice ufficiale argospm. Nessun dato lascia la macchina.

Output: per ogni lingua richiesta `transcript_<lang>.txt` (stesso formato di
transcript.txt, con parlanti) e, in transcript.json, `segments[i].tr[lang]` e
la lista `translations`.
"""
# «Education never ends, Watson. It is a series of lessons, with the greatest for the last.»
#   A. Conan Doyle, The Adventure of the Red Circle
from __future__ import annotations

import os
import re
import json
import zipfile
from pathlib import Path

TARGETS = {"en": "inglese", "it": "italiano"}
ARGOS_INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
ARGOS_FALLBACK_URL = "https://argos-net.com/v1/translate-{src}_{dst}-1_0.argosmodel"
ARGOS_SIZE_MB = 90


# ---------------------------------------------------------------------------
# pacchetti Argos: cache e download
# ---------------------------------------------------------------------------
def models_dir() -> Path:
    env = os.environ.get("QUAESITOR_MODELS_DIR")
    base = Path(env) if env else Path.home() / ".quaesitor" / "models"
    return base / "translate"


def pair_dir(src: str, dst: str) -> Path:
    return models_dir() / f"{src}_{dst}"


def pair_cached(src: str, dst: str) -> bool:
    d = pair_dir(src, dst)
    return (d / "model" / "model.bin").is_file() and (d / "sentencepiece.model").is_file()


def _package_url(src: str, dst: str) -> str:
    """URL del pacchetto dall'indice argospm; in mancanza, lo schema classico v1."""
    import urllib.request
    try:
        req = urllib.request.Request(ARGOS_INDEX_URL, headers={"User-Agent": "cognitor"})
        with urllib.request.urlopen(req, timeout=30) as r:
            index = json.loads(r.read().decode("utf-8"))
        for p in index:
            if p.get("from_code") == src and p.get("to_code") == dst and p.get("links"):
                return p["links"][0]
    except Exception:  # noqa: BLE001 — indice irraggiungibile: si prova l'URL storico
        pass
    return ARGOS_FALLBACK_URL.format(src=src, dst=dst)


def download_pair(src: str, dst: str, progress=None, cancel=None) -> Path:
    """Scarica ed estrae il pacchetto <src>_<dst>; progress(done, total), cancel() -> bool."""
    import urllib.request
    dest = pair_dir(src, dst)
    if pair_cached(src, dst):
        return dest
    models_dir().mkdir(parents=True, exist_ok=True)
    url = _package_url(src, dst)
    zip_path = models_dir() / f"translate-{src}_{dst}.argosmodel"
    tmp = Path(str(zip_path) + ".part")
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
    tmp.replace(zip_path)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            # dentro lo zip: <cartella>/model/*, <cartella>/sentencepiece.model, metadata.json
            parts = Path(name).parts
            if len(parts) < 2 or name.endswith("/"):
                continue
            rel = Path(*parts[1:])
            if rel.parts[0] not in ("model", "sentencepiece.model", "metadata.json"):
                continue            # stanza/ (tokenizer PyTorch) non serve
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as s, open(out, "wb") as o:
                o.write(s.read())
    zip_path.unlink(missing_ok=True)
    if not pair_cached(src, dst):
        raise RuntimeError(f"pacchetto {src}_{dst} incompleto dopo il download")
    return dest


# ---------------------------------------------------------------------------
# motore Argos (CTranslate2 + SentencePiece)
# ---------------------------------------------------------------------------
_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+(?=[^\s])")


class ArgosPair:
    """Traduttore <src>→<dst> su un pacchetto Argos già in cache."""

    def __init__(self, src: str, dst: str, use_gpu: bool = False):
        try:
            import ctranslate2
            import sentencepiece as spm
        except ImportError:
            raise RuntimeError(
                "supporto traduzione non installato: pip install -r requirements-audio.txt")
        if not pair_cached(src, dst):
            raise RuntimeError(f"pacchetto lingua {src}_{dst} non in cache")
        d = pair_dir(src, dst)
        self.src, self.dst = src, dst
        self.sp = spm.SentencePieceProcessor(model_file=str(d / "sentencepiece.model"))
        device = "cuda" if use_gpu else "cpu"
        try:
            self.tr = ctranslate2.Translator(str(d / "model"), device=device,
                                             compute_type="int8" if device == "cpu" else "default")
        except Exception:  # noqa: BLE001 — CUDA non pronta per ctranslate2: CPU
            self.tr = ctranslate2.Translator(str(d / "model"), device="cpu", compute_type="int8")

    def translate(self, texts: list[str], beam_size: int = 4) -> list[str]:
        """Traduce una lista di testi (frase per frase, in batch); mantiene l'ordine."""
        pieces, owner = [], []
        for i, t in enumerate(texts):
            t = (t or "").strip()
            for s in (_SENT_SPLIT.split(t) if t else []):
                if s.strip():
                    pieces.append(s.strip())
                    owner.append(i)
        out = [""] * len(texts)
        if not pieces:
            return out
        toks = [self.sp.encode(p, out_type=str) for p in pieces]
        res = self.tr.translate_batch(toks, beam_size=beam_size, max_batch_size=32,
                                      max_decoding_length=512)
        parts: dict[int, list[str]] = {}
        for i, r in zip(owner, res):
            parts.setdefault(i, []).append(self.sp.decode(r.hypotheses[0]).strip())
        for i, ps in parts.items():
            out[i] = " ".join(p for p in ps if p)
        return out


# ---------------------------------------------------------------------------
# allineamento dei segmenti tradotti da Whisper
# ---------------------------------------------------------------------------
def align_to_segments(segments: list[dict], translated: list[dict]) -> list[str]:
    """Per ogni segmento originale, il testo dei segmenti `translated` ({t0,t1,text})
    che lo coprono di più (per sovrapposizione; altrimenti il più vicino), nell'ordine.
    Ogni segmento tradotto finisce in uno e un solo segmento originale."""
    texts = [[] for _ in segments]
    if not segments:
        return []
    for tseg in translated:
        a, b = float(tseg["t0"]), float(tseg["t1"])
        best, best_ov = None, 0.0
        for i, s in enumerate(segments):
            ov = min(b, float(s["t1"])) - max(a, float(s["t0"]))
            if ov > best_ov:
                best, best_ov = i, ov
        if best is None:                      # nessuna sovrapposizione: il più vicino nel tempo
            mid = (a + b) / 2
            best = min(range(len(segments)),
                       key=lambda i: abs((float(segments[i]["t0"]) + float(segments[i]["t1"])) / 2 - mid))
        texts[best].append((a, (tseg.get("text") or "").strip()))
    return [" ".join(t for _, t in sorted(lst) if t) for lst in texts]


def whisper_translate(model, video_path, cancel=None, log=print) -> list[dict]:
    """Seconda passata di Whisper con task="translate": segmenti in inglese."""
    seg_iter, info = model.transcribe(str(video_path), task="translate", vad_filter=True)
    total = float(getattr(info, "duration", 0.0) or 0.0)
    out = []
    for s in seg_iter:
        if cancel and cancel():
            raise RuntimeError("interrotto dall'utente")
        text = (s.text or "").strip()
        if text:
            out.append({"t0": round(float(s.start), 2), "t1": round(float(s.end), 2), "text": text})
        log(f"[translate] {int(min(float(s.end), total) if total else float(s.end))}/{int(total)}")
    return out


# ---------------------------------------------------------------------------
# pipeline
# ---------------------------------------------------------------------------
def translate_transcript(transcript: dict, targets, video_path=None, model=None,
                         use_gpu: bool = False, cancel=None, log=print) -> dict:
    """Aggiunge a `transcript` (dict di transcribe_video, in place) le traduzioni verso
    `targets` ⊆ {"en","it"}: segments[i]["tr"][lang] e transcript["translations"].
    `model` è il modello faster-whisper già caricato (per la passata verso l'inglese);
    senza modello si usa il pacchetto Argos <src>_en se esiste.
    Solleva RuntimeError quando una lingua non è producibile (chiamante decide)."""
    targets = [t for t in targets if t in TARGETS]
    segs = transcript.get("segments", [])
    src = (transcript.get("languages") or [None])[0]
    done = list(transcript.get("translations") or [])
    if not segs or not targets:
        return transcript
    if not src:
        raise RuntimeError("lingua sorgente sconosciuta: traduzione saltata")

    def set_lang(lang, texts):
        for s, t in zip(segs, texts):
            s.setdefault("tr", {})[lang] = t
        if lang not in done:
            done.append(lang)

    # l'inglese serve se e' richiesto, o come pivot verso l'italiano da una terza
    # lingua: con audio italiano e solo «italiano» richiesto partiva una seconda
    # passata di Whisper che poi si scartava (2026-09-02)
    need_en = ("en" in targets or ("it" in targets and src != "it")) and src != "en"
    english = None
    if src == "en":
        english = [s["text"] for s in segs]
    elif need_en:
        if model is not None and video_path is not None:
            log("[translate] verso l'inglese con Whisper (seconda passata)")
            english = align_to_segments(segs, whisper_translate(model, video_path, cancel=cancel, log=log))
        else:
            if not pair_cached(src, "en"):
                log(f"[translate] scarico il pacchetto Argos {src}_en (~{ARGOS_SIZE_MB} MB)")
                download_pair(src, "en", cancel=cancel)
            english = ArgosPair(src, "en", use_gpu=use_gpu).translate([s["text"] for s in segs])
        if "en" in targets:
            set_lang("en", english)
            log("[translate] inglese: ok")
    elif "en" in targets:
        log("[translate] l'audio è già in inglese: transcript_en non necessario")

    if "it" in targets:
        if src == "it":
            log("[translate] l'audio è già in italiano: transcript_it non necessario")
        else:
            if not pair_cached("en", "it"):
                log(f"[translate] scarico il pacchetto Argos en_it (~{ARGOS_SIZE_MB} MB)")
                download_pair("en", "it", cancel=cancel)
            pair = ArgosPair("en", "it", use_gpu=use_gpu)
            out, batch = [], 32
            for i in range(0, len(english), batch):
                if cancel and cancel():
                    raise RuntimeError("interrotto dall'utente")
                out.extend(pair.translate(english[i:i + batch]))
                log(f"[translate] {min(i + batch, len(english))}/{len(english)}")
            set_lang("it", out)
            log("[translate] italiano: ok")
    transcript["translations"] = done
    return transcript
