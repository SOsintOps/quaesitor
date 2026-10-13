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

"""Audio transcription of videos (ROADMAP Phase 1): transcription with faster-whisper.

The video goes in as it is: faster-whisper decodes its audio by itself (PyAV),
without a system ffmpeg. Fully offline; on the CPU the small models are used
(tiny/base/small), CUDA accelerates where available.

Output in the run folder:
- transcript.json   source of truth: language, duration, timed segments,
                    speaker (Phase 2) and translations (Phase 3);
- transcript.txt    readable version: [HH:MM:SS-HH:MM:SS] PARLANTE k (language) text.

Diarization (ROADMAP Phase 2, `diarize=True`): after the transcription the module
`diarize` counts the speakers (Silero VAD + WeSpeaker on onnxruntime) and labels
the segments `PARLANTE 1..N`. If something is missing (audio package, models, network)
the transcription is produced anyway, without speakers, with a message in the log.

Translation (ROADMAP Phase 3, `translate=("en","it")`): the `translate` module
adds English (Whisper, second pass) and/or Italian (Argos package
en_it via ctranslate2) and `transcript_en.txt` / `transcript_it.txt` are written;
here too, on problems, the transcription stays valid.

The audio dependencies are OPTIONAL (requirements-audio.txt): without them, the functions
raise RuntimeError with clear instructions and the rest of Cognitor does not change.
"""
# «You have a grand gift for silence, Watson.»
#   A. Conan Doyle, The Man with the Twisted Lip
from __future__ import annotations

import os
import json

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]


def _fmt_ts(sec: float) -> str:
    s = int(max(0, sec))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def load_model(model_size: str = "small", device: str = "cpu"):
    """Loads the faster-whisper model (downloaded on first use, then cached)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError(
            "supporto audio non installato: pip install -r requirements-audio.txt")
    if model_size not in WHISPER_MODELS:
        raise RuntimeError(f"modello Whisper sconosciuto: {model_size} "
                           f"(validi: {', '.join(WHISPER_MODELS)})")
    compute = "int8" if device == "cpu" else "float16"
    return WhisperModel(model_size, device=device, compute_type=compute)


def write_transcript(result: dict, output_dir, lang: str | None = None) -> str:
    """Writes transcript.txt (and transcript.json) from the `result` dict; returns the .txt path.
    With `lang` ("en"/"it") it writes transcript_<lang>.txt with the translated texts instead
    (segments[i]["tr"][lang]; if missing, the original text) and does not touch the .json."""
    os.makedirs(output_dir, exist_ok=True)
    if lang is None:
        out_json = os.path.join(str(output_dir), "transcript.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)

    base = os.path.basename(str(result.get("video", "")))
    total = float(result.get("duration") or 0.0)
    langs = result.get("languages") or []
    n_spk = result.get("speakers")
    name = "transcript.txt" if lang is None else f"transcript_{lang}.txt"
    out_txt = os.path.join(str(output_dir), name)
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("QUAESITOR — SBOBINAMENTO" + (f" — TRADUZIONE ({lang.upper()})" if lang else "")
                + f"\nvideo: {base}\nmodello: {result.get('model')}"
                f" | durata audio: {_fmt_ts(total)}"
                + (f" | lingua: {langs[0]}" if langs else "")
                + (f" | parlanti: {n_spk}" if n_spk else "")
                + ("\n[TRASCRIZIONE PARZIALE: interrotta dall'utente]" if result.get("partial") else "")
                + "\n\n")
        for s in result.get("segments", []):
            spk = f" {s['speaker']}" if s.get("speaker") else ""
            text = s["text"]
            if lang is not None:
                text = (s.get("tr") or {}).get(lang) or text
            f.write(f"[{_fmt_ts(s['t0'])}-{_fmt_ts(s['t1'])}]{spk}"
                    f" ({lang or s.get('lang') or '??'}) {text}\n")
    return out_txt


def transcribe_video(video_path, output_dir, model_size: str = "small",
                     device: str = "cpu", cancel=None, model=None,
                     diarize: bool = False, num_speakers: int = 0,
                     pyannote: bool = False, hf_token: str = "",
                     use_gpu: bool = False, translate=(), voice_model: str = "wr34",
                     log=print) -> dict:
    """Transcribes the audio of a video (or audio file) and saves transcript.json/.txt.

    cancel:       optional callable, checked between one segment and the next.
    model:        already loaded instance to reuse (or a stub in the tests); if None it is
                  loaded according to model_size/device.
    pyannote:     if True uses pyannote.audio (more accurate, needs PyTorch and a Hugging
                  Face token of the analyst); if it is not usable it falls back by itself
                  to the lightweight diarization, stating so in the log.
    diarize:      if True, after the transcription counts the speakers and labels the
                  segments (Phase 2); on problems it goes on without speakers.
    num_speakers: 0 = automatic, otherwise forces the number of speakers.
    use_gpu:      uses CUDA (if available in onnxruntime) for the voice embedding.
    voice_model:  family of the voice model (catalogue in voices.py): the voiceprints of
                  every speaker end up in voices.npz next to the transcript.
    translate:    target languages among "en" and "it" (Phase 3): writes
                  transcript_<lang>.txt; on problems it goes on without them.
    Returns the transcript dict (the same content as transcript.json).
    """
    os.makedirs(output_dir, exist_ok=True)
    if model is None:
        model = load_model(model_size, device)

    seg_iter, info = model.transcribe(str(video_path), vad_filter=True)
    total = float(getattr(info, "duration", 0.0) or 0.0)
    lang = getattr(info, "language", None)
    lang_p = getattr(info, "language_probability", None)
    base = os.path.basename(str(video_path))
    log(f"[transcribe] {base}: {total:.0f}s di audio, modello {model_size}"
          + (f", lingua rilevata: {lang}" + (f" ({lang_p:.0%})" if lang_p else "")
             if lang else ""))

    segments = []
    stopped = False
    for s in seg_iter:
        if cancel and cancel():
            log("[transcribe] interrotto dall'utente")
            stopped = True
            break
        text = (s.text or "").strip()
        if not text:
            continue
        segments.append({"t0": round(float(s.start), 2), "t1": round(float(s.end), 2),
                         "lang": lang, "speaker": None, "text": text})
        log(f"[transcribe] {int(min(float(s.end), total) if total else float(s.end))}"
              f"/{int(total)}")

    result = {
        "video": str(video_path), "model": model_size,
        "duration": round(total, 2), "languages": [lang] if lang else [],
        "speakers": None, "partial": stopped, "segments": segments,
    }
    out_txt = write_transcript(result, output_dir)   # first version: already useful
    log(f"[transcribe] completato: {len(segments)} segmenti -> {out_txt}")

    if diarize and segments and not stopped:
        try:
            from .diarize import add_speakers_auto
            add_speakers_auto(video_path, result, use_gpu=use_gpu, num_speakers=num_speakers,
                              cancel=cancel, log=log, token=hf_token,
                              prefer_pyannote=bool(pyannote), voice_model=voice_model)
            vettori = result.pop("_voices", None)      # private key: the vectors do not go into the JSON
            if vettori:
                try:
                    from .voices import scrivi_npz
                    scrivi_npz(output_dir, vettori["embeddings"], vettori["windows"], vettori["labels"],
                               vettori["speakers"], vettori["impronte"], vettori["family"],
                               vettori["model"], vettori["diarizer"])
                except Exception as e:  # noqa: BLE001 — without the npz the transcript is valid anyway
                    result.pop("voiceprints", None)
                    log(f"[diarize] impronte vocali non salvate: {e}")
            write_transcript(result, output_dir)
            n = result["speakers"]
            log(f"[diarize] completato: {n} parlant{'e' if n == 1 else 'i'} -> {out_txt}")
        except Exception as e:  # noqa: BLE001 — the transcription stays valid without speakers
            log(f"[diarize] saltato: {e}")

    targets = [t for t in (translate or ()) if t in ("en", "it")]
    if targets and segments and not stopped:
        try:
            from .translate import translate_transcript
            translate_transcript(result, targets, video_path=video_path, model=model,
                                 use_gpu=use_gpu, cancel=cancel, log=log)
            write_transcript(result, output_dir)
            for lang in result.get("translations") or []:
                log(f"[translate] -> {write_transcript(result, output_dir, lang=lang)}")
        except Exception as e:  # noqa: BLE001 — the transcription stays valid without translations
            log(f"[translate] saltato: {e}")
    return result


def write_named_transcript(output_dir, nomi: dict, lang=None) -> str | None:
    """Writes `transcript_nomi.txt`: the transcript with the **names of the people** in place
    of the diarization labels (PARLANTE 1, 2, …).

    The original transcript is not touched: it is the product of the processing, while the
    match between voice and person is a conclusion of the analyst, which can
    change. Returns the path written, or None if there is nothing to write.
    """
    import json as _json
    d = str(output_dir)
    src = os.path.join(d, "transcript.json")
    if not nomi or not os.path.isfile(src):
        return None
    with open(src, encoding="utf-8") as f:
        result = _json.load(f)
    segmenti = result.get("segments") or []
    if not segmenti:
        return None
    base = os.path.basename(str(result.get("video", "")))
    out = os.path.join(d, "transcript_nomi.txt" if lang is None else f"transcript_nomi_{lang}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("QUAESITOR — SBOBINAMENTO CON I NOMI"
                + (f" — TRADUZIONE ({lang.upper()})" if lang else "")
                + f"\nvideo: {base}\nmodello: {result.get('model')}"
                f" | durata audio: {_fmt_ts(float(result.get('duration') or 0.0))}\n"
                "corrispondenze (stabilite dall'analista): "
                + ", ".join(f"{k} = {v}" for k, v in sorted(nomi.items())) + "\n\n")
        for s in segmenti:
            spk = s.get("speaker")
            etichetta = f" {nomi.get(spk, spk)}" if spk else ""
            testo = s["text"]
            if lang is not None:
                testo = (s.get("tr") or {}).get(lang) or testo
            # the segment keys are t0/t1 (see transcribe_video), not start/end
            f.write(f"[{_fmt_ts(s['t0'])} → {_fmt_ts(s['t1'])}]{etichetta}  {testo.strip()}\n")
    print(f"[transcribe] trascritto con i nomi -> {out}")
    return out
