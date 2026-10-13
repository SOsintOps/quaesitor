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

"""Translation of the transcript (ROADMAP Phase 3): English and Italian, fully offline.

- Into **English**: Whisper's native translation (second pass of the model
  with `task="translate"`), realigned to the transcription segments by
  temporal overlap. If the audio is already in English nothing is needed.
- Into **Italian**: **Argos Translate** language package `en_it`
  (CTranslate2 + SentencePiece model) loaded directly with ctranslate2
  — no `argostranslate` package (which would require stanza/PyTorch).
  Sources other than English go through English (pivot = the Whisper
  translation of the point above). If the audio is already in Italian nothing is needed.

The `.argosmodel` package (~88 MB) is downloaded on first use to
~/.quaesitor/models/translate/ (override with QUAESITOR_MODELS_DIR); the models
come from the official argospm index. No data leaves the machine.

Output: for every requested language `transcript_<lang>.txt` (same format as
transcript.txt, with speakers) and, in transcript.json, `segments[i].tr[lang]` and
the `translations` list.
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
# Argos packages: cache and download
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
    """URL of the package from the argospm index; failing that, the classic v1 scheme."""
    import urllib.request
    try:
        req = urllib.request.Request(ARGOS_INDEX_URL, headers={"User-Agent": "cognitor"})
        with urllib.request.urlopen(req, timeout=30) as r:
            index = json.loads(r.read().decode("utf-8"))
        for p in index:
            if p.get("from_code") == src and p.get("to_code") == dst and p.get("links"):
                return p["links"][0]
    except Exception:  # noqa: BLE001 — index unreachable: try the historical URL
        pass
    return ARGOS_FALLBACK_URL.format(src=src, dst=dst)


def download_pair(src: str, dst: str, progress=None, cancel=None) -> Path:
    """Downloads and extracts the <src>_<dst> package; progress(done, total), cancel() -> bool."""
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
            # inside the zip: <folder>/model/*, <folder>/sentencepiece.model, metadata.json
            parts = Path(name).parts
            if len(parts) < 2 or name.endswith("/"):
                continue
            rel = Path(*parts[1:])
            if rel.parts[0] not in ("model", "sentencepiece.model", "metadata.json"):
                continue            # stanza/ (PyTorch tokenizer) is not needed
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as s, open(out, "wb") as o:
                o.write(s.read())
    zip_path.unlink(missing_ok=True)
    if not pair_cached(src, dst):
        raise RuntimeError(f"pacchetto {src}_{dst} incompleto dopo il download")
    return dest


# ---------------------------------------------------------------------------
# Argos engine (CTranslate2 + SentencePiece)
# ---------------------------------------------------------------------------
_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+(?=[^\s])")


class ArgosPair:
    """Translator <src>→<dst> on an Argos package already in the cache."""

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
        except Exception:  # noqa: BLE001 — CUDA not ready for ctranslate2: CPU
            self.tr = ctranslate2.Translator(str(d / "model"), device="cpu", compute_type="int8")

    def translate(self, texts: list[str], beam_size: int = 4) -> list[str]:
        """Translates a list of texts (sentence by sentence, in batches); keeps the order."""
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
# alignment of the segments translated by Whisper
# ---------------------------------------------------------------------------
def align_to_segments(segments: list[dict], translated: list[dict]) -> list[str]:
    """For every original segment, the text of the `translated` segments ({t0,t1,text})
    that cover it most (by overlap; otherwise the nearest), in order.
    Every translated segment ends up in one and only one original segment."""
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
        if best is None:                      # no overlap: the nearest in time
            mid = (a + b) / 2
            best = min(range(len(segments)),
                       key=lambda i: abs((float(segments[i]["t0"]) + float(segments[i]["t1"])) / 2 - mid))
        texts[best].append((a, (tseg.get("text") or "").strip()))
    return [" ".join(t for _, t in sorted(lst) if t) for lst in texts]


def whisper_translate(model, video_path, cancel=None, log=print) -> list[dict]:
    """Second Whisper pass with task="translate": segments in English."""
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
    """Adds to `transcript` (dict from transcribe_video, in place) the translations into
    `targets` ⊆ {"en","it"}: segments[i]["tr"][lang] and transcript["translations"].
    `model` is the faster-whisper model already loaded (for the pass into English);
    without a model the Argos package <src>_en is used if it exists.
    Raises RuntimeError when a language cannot be produced (the caller decides)."""
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

    # English is needed if requested, or as a pivot towards Italian from a third
    # language: with Italian audio and only "Italian" requested, a second Whisper
    # pass was started and then discarded (2026-09-02)
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
