# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Video transcription on this computer (quaesitor/audio)."""
# "Audi alteram partem." (legal maxim)
# Hear the other side.
import logging
import os
import re
import threading
import threading as _threading

from flask import Blueprint, jsonify, request

from .. import audio as _audio
from .. import ontology as onto
from .. import transcripts as _transcripts
from .. import ftm, store
from ..core import _scan, _scan_lock, _truthy, DATA_DIR, NodeError
from ..labels import _cache
from ..archive import _run_scan, _sources_folder
from ..bulk_import import _ftm_mapping, commit_plan, ftm_reserved, plan_import

bp = Blueprint("transcription", __name__)


# ======================= VIDEO TRANSCRIPTION (1.6.0) =======================
# The modules of Cognitor in audio/ (GPL, optional packages of requirements-audio.txt):
# faster-whisper, diarization, translation. A transcribed video becomes the same
# Follow the Money entities as a Cognitor bundle (transcripts.py) and goes through the
# same import: a second transcription of the same file updates the same nodes.
# Everything runs on this computer; the models download once, on first use.

TRANSCRIPTS_DIRNAME = "transcripts"
WHISPER_MODELS = ("tiny", "base", "small", "medium", "large-v3")
_tr_job = {"running": False, "finished": False, "error": "", "stage": "", "done": 0, "total": 0,
           "log": [], "result": None, "file": ""}
_tr_lock = threading.Lock()
_tr_stop = threading.Event()


def _tr_log(msg):
    """Log of the transcription job: the last 200 lines, and the progress lines
    '[transcribe|diarize|translate] N/M' of the modules become the bar."""
    msg = str(msg)
    lines = _tr_job["log"]
    lines.append(msg)
    del lines[:-200]
    m = re.match(r"\[(transcribe|diarize|translate)\] (\d+)/(\d+)", msg)
    if m:
        _tr_job["stage"], _tr_job["done"], _tr_job["total"] = m.group(1), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"\[(diarize|translate)\]", msg)
        if m and _tr_job["stage"] != m.group(1):
            _tr_job.update(stage=m.group(1), done=0, total=0)
    logging.info(msg)


@bp.route("/api/transcribe/status")
def api_transcribe_status():
    ok, why = _audio.available()
    out = {"available": ok, "reason": why, "missing": _audio.missing_packages(),
           "models": list(WHISPER_MODELS), "running": _tr_job["running"],
           "install": "requirements-audio.txt"}
    if ok:
        try:
            from ..audio import diarize as _dia
            out["diarize_models_cached"] = _dia.models_cached()
            out["models_dir"] = str(_dia.models_dir())
        except Exception as e:                       # noqa: BLE001 - status only
            out["diarize_models_cached"] = False
            out["models_error"] = str(e)
    return jsonify(out)


@bp.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    """Starts the transcription of a video (or audio) file of this computer.
    Body: {path, model_size, diarize, speakers, translate: ["en", "it"]}.
    Progress: /api/transcribe/progress; stop: /api/transcribe/stop."""
    data = request.get_json(silent=True) or {}
    ok, why = _audio.available()
    if not ok:
        return jsonify({"error": "transcription not installed: pip install -r requirements-audio.txt",
                        "reason": why}), 503
    path = str(data.get("path") or "").strip().strip('"')
    path = os.path.abspath(os.path.expanduser(path)) if path else ""
    if not path or not os.path.isfile(path):
        return jsonify({"error": f"file not found: {path}"}), 400
    case_id = store.current_case()
    if not case_id:
        return jsonify({"error": "no case open"}), 400
    model = str(data.get("model_size") or "small")
    if model not in WHISPER_MODELS:
        return jsonify({"error": f"unknown model: {model}"}), 400
    try:
        speakers = max(0, min(20, int(data.get("speakers") or 0)))
    except (TypeError, ValueError):
        speakers = 0
    opts = {"model_size": model, "diarize": _truthy(data.get("diarize", True)), "speakers": speakers,
            "translate": [x for x in (data.get("translate") or []) if x in ("en", "it")]}
    with _tr_lock:
        if _tr_job["running"]:
            return jsonify({"error": "transcription already running", "running": True}), 409
        _tr_stop.clear()
        _tr_job.update({"running": True, "finished": False, "error": "", "stage": "hash", "done": 0,
                        "total": 0, "log": [], "result": None, "file": os.path.basename(path)})
    threading.Thread(target=_run_transcribe, args=(path, opts, case_id), daemon=True).start()
    return jsonify({"started": True})


@bp.route("/api/transcribe/progress")
def api_transcribe_progress():
    out = dict(_tr_job)
    out["log"] = list(_tr_job["log"][-60:])
    return jsonify(out)


@bp.route("/api/transcribe/stop", methods=["POST"])
def api_transcribe_stop():
    _tr_stop.set()
    return jsonify({"ok": True, "running": _tr_job["running"]})


def _run_transcribe(path, opts, case_id):
    try:
        from ..audio.transcribe import transcribe_video
        sha = _transcripts.sha256_file(path)
        out = os.path.join(DATA_DIR, TRANSCRIPTS_DIRNAME, case_id, sha[:16])
        _tr_job["stage"] = "transcribe"
        _tr_log(f"[transcribe] {os.path.basename(path)} -> {out}")
        res = transcribe_video(path, out, model_size=opts["model_size"], diarize=opts["diarize"],
                               num_speakers=opts["speakers"], translate=tuple(opts["translate"]),
                               cancel=_tr_stop.is_set, log=_tr_log)
        if store.current_case() != case_id:
            raise NodeError(f"the open case changed during the transcription: the transcript stays in {out}")
        _tr_job.update(stage="import", done=0, total=0)
        ents, names, body = _transcripts.entities(res, path, case_id, sha)
        table = ftm.rows_from_entities({e["id"]: e for e in ents}, native_types=onto.TYPES,
                                       reserved=ftm_reserved)
        plan, _ = plan_import(table, mapping=_ftm_mapping(table[0]), has_header=True)
        r = commit_plan(plan, update=True, ftm_dataset="quaesitor:transcribe")
        _cache["key"] = None
        # the transcript in the sources folder, where the search finds it
        folder = os.path.join(_sources_folder(), TRANSCRIPTS_DIRNAME, re.sub(r"[^A-Za-z0-9_-]+", "_", case_id))
        os.makedirs(folder, exist_ok=True)
        stem = re.sub(r"[^\w.-]+", "_", os.path.splitext(os.path.basename(path))[0])[:60] + "_" + sha[:8]
        files = []
        if body:
            fp = os.path.join(folder, stem + ".txt")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(f"{os.path.basename(path)}\n\n{body}\n")
            files.append(fp)
        for lg in res.get("translations") or []:
            fp = os.path.join(folder, f"{stem}.{lg}.txt")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(f"{os.path.basename(path)} ({lg})\n\n{_transcripts.text_of(res.get('segments') or [], names, lang=lg)}\n")
            files.append(fp)
        scan = False
        if files:
            sfolder = _sources_folder()
            with _scan_lock:
                if not _scan["running"] and os.path.isdir(sfolder):
                    _scan.update({"running": True, "done": 0, "total": 0, "name": "",
                                  "finished": False, "error": "", "summary": None})
                    _threading.Thread(target=_run_scan, args=(sfolder,), daemon=True).start()
                    scan = True
        node = next((i for i in r.get("ids") or [] if i.split(":", 1)[0] in ("video", "audio")), "")
        _tr_job["result"] = {"node": node, "output": out, "segments": len(res.get("segments") or []),
                             "speakers": len(names), "languages": res.get("languages") or [],
                             "translations": res.get("translations") or [], "partial": bool(res.get("partial")),
                             "nodes": r.get("nodes", 0), "links": r.get("links", 0),
                             "updated": r.get("updated", 0), "sources": files, "sources_scan": scan}
        _tr_log(f"[import] {r.get('nodes', 0)} nodes, {r.get('links', 0)} links, {r.get('updated', 0)} updated")
    except Exception as e:
        logging.error(f"Transcription failed: {e}", exc_info=not isinstance(e, NodeError))
        _tr_job["error"] = str(e)
    finally:
        _tr_job["running"] = False
        _tr_job["finished"] = True
