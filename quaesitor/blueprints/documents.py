# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Document sources: the folder, the index, search, files, OCR and the Tesseract download."""
# "Verba volant, scripta manent." (proverb)
# Spoken words fly away, written ones remain.
import logging
import os
import threading
import threading as _threading

from flask import abort, Blueprint, jsonify, request, send_from_directory

from .. import archive
from .. import setup_tesseract as _tess
from .. import sources as _src
from ..paths import BASE_DIR
from ..core import _scan, _scan_lock
from ..archive import _run_scan, sources_index

bp = Blueprint("documents", __name__)


# -------- Tesseract downloadable from the interface (Windows only) ----------
# Same procedure as setup_tesseract.py, run in a thread: the state is read from
# /api/ocr/install/status while the panel shows the progress.
_OCR_JOB = {"state": "idle", "stage": "", "percent": 0, "error": ""}
_OCR_LOCK = threading.Lock()


def _ocr_install_worker():
    def progress(done, total):
        _OCR_JOB["percent"] = int(done * 100 / total) if total else 0

    def stage(name):
        _OCR_JOB["stage"] = name

    try:
        dest = os.path.join(BASE_DIR, "tools", "tesseract")
        exe = _tess.setup_windows(_tess.DEFAULT_URL, dest, progress=progress, stage=stage)
        ok = _src.configure_ocr(BASE_DIR)          # enables OCR without restarting
        _OCR_JOB.update(state="done" if ok else "error", percent=100,
                        error="" if ok else "tesseract.exe downloaded but not usable")
        logging.info(f"Tesseract in {exe}: OCR {'on' if ok else 'NOT on'}")
    except Exception as e:
        logging.error("Installing Tesseract failed", exc_info=True)
        _OCR_JOB.update(state="error", error=str(e))


@bp.route("/api/ocr/install", methods=["POST"])
def api_ocr_install():
    """Starts the download of Tesseract into the tools/tesseract folder."""
    if os.name != "nt":
        return jsonify({"error": "automatic download available on Windows only"}), 400
    if _src.OCR_AVAILABLE:
        return jsonify({"ok": True, "state": "done", "already": True})
    if _src.OCR_REASON == "module":
        return jsonify({"error": "the Python module pytesseract is missing: pip install pytesseract"}), 400
    with _OCR_LOCK:
        if _OCR_JOB["state"] != "running":
            _OCR_JOB.update(state="running", stage="download", percent=0, error="")
            threading.Thread(target=_ocr_install_worker, daemon=True).start()
            logging.info(f"Downloading Tesseract from {_tess.DEFAULT_URL}")
    return jsonify({"ok": True, "state": "running", "url": _tess.DEFAULT_URL})


@bp.route("/api/ocr/install/status")
def api_ocr_install_status():
    return jsonify(dict(_OCR_JOB, ocr_available=_src.OCR_AVAILABLE))


@bp.route("/api/sources/status")
def api_sources_status():
    """State of the sources index: folder, how many files, OCR available."""
    idx = sources_index()
    st = _src.index_summary(idx) if idx else {}
    if idx:
        # folder actually read from NOW (usually 'sources' next to the
        # executable): so the user sees where the documents are taken from
        cartella = _src.resolved_folder(idx, BASE_DIR, archive.SOURCES_DEFAULT)
        st["folder"] = cartella
        # if the resolved folder is next to the program, the whole is portable:
        # it is declared here, not from how the index was at scan time
        # (it could have been an absolute folder on another PC)
        rel = _src._rel_to_base(cartella, BASE_DIR)
        st["portable"] = bool(rel)
        st["folder_rel"] = rel
    st["ocr_available"] = _src.OCR_AVAILABLE
    st["ocr_langs"] = _src.OCR_LANG                 # e.g. "ita+eng" ("" = default)
    st["ocr_reason"] = _src.OCR_REASON             # "module" | "binary" | ""
    # automatic download only on Windows and only if the binary is missing (if the
    # pytesseract Python module is missing, downloading Tesseract would not help)
    st["ocr_can_install"] = os.name == "nt" and _src.OCR_REASON != "module"
    st["ocr_install"] = _OCR_JOB["state"]
    st["ocr_url"] = _tess.DEFAULT_URL
    st["indexed"] = bool(idx)
    st["default_folder"] = archive.SOURCES_DEFAULT
    return jsonify(st)


@bp.route("/api/sources/pick", methods=["POST"])
def api_sources_pick():
    """Opens the system's native folder picker (the app runs locally) and
    returns the chosen path. If there is no graphical environment, the client
    falls back to entering the path by hand."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        start = request.get_json(silent=True) or {}
        folder = filedialog.askdirectory(
            title="Choose the sources folder",
            initialdir=start.get("start") or os.path.expanduser("~"))
        root.destroy()
        return jsonify({"folder": folder or ""})
    except Exception as e:
        logging.warning(f"Folder dialog not available: {e}")
        return jsonify({"error": "folder dialog not available", "detail": str(e)}), 501


@bp.route("/api/sources/scan", methods=["POST"])
def api_sources_scan():
    """Starts indexing the folder in a worker thread and returns at once.
    The progress is read with /api/sources/progress. Body: {folder}."""
    data = request.get_json(silent=True) or {}
    folder = str(data.get("folder") or "").strip().strip('"')
    if not folder:
        folder = archive.SOURCES_DEFAULT          # 'sources' next to the executable
    if not os.path.isdir(folder):
        return jsonify({"error": f"folder not found: {folder}"}), 404
    with _scan_lock:
        if _scan["running"]:
            return jsonify({"error": "scan already running", "running": True}), 409
        _scan.update({"running": True, "done": 0, "total": 0, "name": "",
                      "finished": False, "error": "", "summary": None})
    _threading.Thread(target=_run_scan, args=(folder,), daemon=True).start()
    return jsonify({"started": True})


@bp.route("/api/sources/progress")
def api_sources_progress():
    """State of the indexing in progress (for the 'file n of n' bar)."""
    return jsonify(dict(_scan))


@bp.route("/api/sources/search", methods=["POST"])
def api_sources_search():
    """Searches a term in the indexed sources. Body: {q, mode:'partial'|'total'}."""
    data = request.get_json(silent=True) or {}
    q = str(data.get("q") or "").strip()
    mode = "total" if data.get("mode") == "total" else "partial"
    if len(q) < 2:
        return jsonify({"error": "search term too short"}), 400
    idx = sources_index()
    if not idx:
        return jsonify({"error": "no sources folder indexed"}), 400
    return jsonify(_src.search_index(idx, q, mode))


@bp.route("/api/sources/multi", methods=["POST"])
def api_sources_multi():
    """Searches several terms together (the words of the card key). Body:
    {terms:[...], mode}. Returns the terms found (with count) and the files,
    each with the terms that match it."""
    data = request.get_json(silent=True) or {}
    terms = data.get("terms") or []
    mode = "total" if data.get("mode") == "total" else "partial"
    idx = sources_index()
    if not idx:
        return jsonify({"error": "no sources folder indexed"}), 400
    return jsonify(_src.search_multi(idx, terms, mode))


@bp.route("/api/sources/file/<fid>")
def api_sources_file(fid):
    """Serves an indexed file (for the preview), checking that it belongs to
    the index and lies inside the scanned folder."""
    idx = sources_index()
    if not idx:
        abort(404)
    f = _src.find_file(idx, fid)
    if not f:
        abort(404)
    # resolves the path NOW, looking FIRST in the 'sources' folder next to the
    # executable: that is where the documents live, and the only location that
    # stays valid when the program is moved to another PC (the index keeps the
    # absolute path of the machine that did the scan).
    path, folder = _src.locate_file(idx, f.get("rel"), BASE_DIR, archive.SOURCES_DEFAULT)
    if not path:
        logging.warning(
            f"Source not found: {f.get('rel')!r}. Looked for in: "
            + " | ".join(_src.folder_candidates(idx, BASE_DIR, archive.SOURCES_DEFAULT)))
        abort(404)
    return send_from_directory(os.path.dirname(path), os.path.basename(path))
