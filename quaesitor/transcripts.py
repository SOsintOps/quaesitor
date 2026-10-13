# -*- coding: utf-8 -*-
# Quaesitor - case graph for OSINT investigations
# Copyright (C) 2026 Ramingo (SOsintOps)
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""A transcribed video as Follow the Money entities, the same vocabulary as a
Cognitor bundle (section 14 of Cognitor's development plan):

    the video                Video        q-<case>-v<sha16>       transcript in bodyText
    every speaker            Person       q-<case>-s<sha16>-<k>   "Speaker k (file)"
    speaker in the video     UnknownLink  q-<case>-l-spk-...      role "speaks in"

The entities go through the Follow the Money import, so a second transcription of the
same file (same sha256) updates the same nodes instead of adding new ones.
"""
# "Verba volant, scripta manent." (Latin proverb)
# Spoken words fly away, written ones remain.
import hashlib
import mimetypes
import os
import re


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ts(sec):
    s = int(max(0.0, float(sec or 0.0)))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def speaker_number(spk):
    """'PARLANTE 2' -> '2' (the last number of the label)."""
    m = re.search(r"(\d+)\s*$", str(spk or ""))
    return m.group(1) if m else str(spk or "?")


def text_of(segments, names, lang=None):
    """'[HH:MM:SS-HH:MM:SS] Speaker k: text' per segment (translated with lang)."""
    out = []
    for s in segments:
        text = str(((s.get("tr") or {}).get(lang) if lang else s.get("text")) or "").strip()
        if not text:
            continue
        who = names.get(s.get("speaker"), "") if s.get("speaker") else ""
        out.append(f"[{_ts(s.get('t0'))}-{_ts(s.get('t1'))}] " + (f"{who}: " if who else "") + text)
    return "\n".join(out)


def entities(result, video_path, case_id, sha):
    """(entities, {speaker label: display name}, transcript text) of a transcription."""
    case_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(case_id or "case"))
    prefix = f"q-{case_id}-"
    fname = os.path.basename(str(video_path)) or "video"
    vid = f"{prefix}v{sha[:16]}"
    segs = result.get("segments") or []
    speakers = sorted({s.get("speaker") for s in segs if s.get("speaker")}, key=lambda x: (len(x), x))
    names = {sp: f"Speaker {speaker_number(sp)} ({fname})" for sp in speakers}
    body = text_of(segs, names)
    mime = mimetypes.guess_type(fname)[0] or ""
    props = {"fileName": [fname], "title": [fname], "contentHash": [sha],
             "summary": [f"Transcribed by Quaesitor: Whisper {result.get('model') or '?'}"
                         + (f", diarizer {result['diarizer']}" if result.get("diarizer") else "")
                         + (" (partial: stopped by the user)" if result.get("partial") else "")]}
    if mime.startswith(("video/", "audio/")):
        props["mimeType"] = [mime]
    if result.get("duration") is not None:
        props["duration"] = [str(result["duration"])]
    if result.get("languages"):
        props["language"] = [str(result["languages"][0])]
    if body:
        props["bodyText"] = [body]
    langs = sorted({lg for s in segs for lg in (s.get("tr") or {})})
    if langs:
        lg = "en" if "en" in langs else langs[0]
        props["translatedText"] = [text_of(segs, names, lang=lg)]
        props["translatedLanguage"] = [lg]
    schema = "Audio" if mime.startswith("audio/") else "Video"
    out = [{"id": vid, "schema": schema, "properties": props}]
    vp = (result.get("voiceprints") or {}).get("speakers") or {}
    for sp in speakers:
        k = speaker_number(sp)
        pid = f"{prefix}s{sha[:16]}-{k}"
        secs = float((vp.get(sp) or {}).get("speech_seconds") or 0.0) or sum(
            max(0.0, float(s.get("t1") or 0) - float(s.get("t0") or 0)) for s in segs if s.get("speaker") == sp)
        out.append({"id": pid, "schema": "Person", "properties": {
            "name": [names[sp]], "summary": [f"Speaker {k} of {fname}, not identified"]}})
        out.append({"id": f"{prefix}l-spk-s{sha[:16]}-{k}", "schema": "UnknownLink", "properties": {
            "subject": [pid], "object": [vid], "role": ["speaks in"],
            "summary": [f"{sp}, {secs:.0f} seconds"]}})
    return out, names, body
