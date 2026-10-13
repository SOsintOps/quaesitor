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


# -------- Tesseract scaricabile dall'interfaccia (solo Windows) ----------
# Stesso procedimento di setup_tesseract.py, eseguito in un thread: lo stato
# si legge da /api/ocr/install/status mentre il pannello mostra l'avanzamento.
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
        ok = _src.configure_ocr(BASE_DIR)          # attiva l'OCR senza riavviare
        _OCR_JOB.update(state="done" if ok else "error", percent=100,
                        error="" if ok else "tesseract.exe scaricato ma non utilizzabile")
        logging.info(f"Tesseract in {exe}: OCR {'attivo' if ok else 'NON attivo'}")
    except Exception as e:
        logging.error("Installazione di Tesseract fallita", exc_info=True)
        _OCR_JOB.update(state="error", error=str(e))


@bp.route("/api/ocr/install", methods=["POST"])
def api_ocr_install():
    """Avvia il download di Tesseract nella cartella tools/tesseract."""
    if os.name != "nt":
        return jsonify({"error": "download automatico disponibile solo su Windows"}), 400
    if _src.OCR_AVAILABLE:
        return jsonify({"ok": True, "state": "done", "already": True})
    if _src.OCR_REASON == "module":
        return jsonify({"error": "manca il modulo Python pytesseract: pip install pytesseract"}), 400
    with _OCR_LOCK:
        if _OCR_JOB["state"] != "running":
            _OCR_JOB.update(state="running", stage="download", percent=0, error="")
            threading.Thread(target=_ocr_install_worker, daemon=True).start()
            logging.info(f"Download di Tesseract da {_tess.DEFAULT_URL}")
    return jsonify({"ok": True, "state": "running", "url": _tess.DEFAULT_URL})


@bp.route("/api/ocr/install/status")
def api_ocr_install_status():
    return jsonify(dict(_OCR_JOB, ocr_available=_src.OCR_AVAILABLE))


@bp.route("/api/sources/status")
def api_sources_status():
    """Stato dell'indice delle fonti: cartella, quanti file, OCR disponibile."""
    idx = sources_index()
    st = _src.index_summary(idx) if idx else {}
    if idx:
        # cartella da cui si legge DAVVERO ora (di norma 'fonti' accanto
        # all'eseguibile): così l'utente vede dove sta pescando i documenti
        cartella = _src.resolved_folder(idx, BASE_DIR, archive.SOURCES_DEFAULT)
        st["folder"] = cartella
        # se la cartella risolta sta accanto al programma il tutto è portabile:
        # lo si dichiara qui, non in base a com'era l'indice al momento della
        # scansione (poteva essere una cartella assoluta di un altro PC)
        rel = _src._rel_to_base(cartella, BASE_DIR)
        st["portable"] = bool(rel)
        st["folder_rel"] = rel
    st["ocr_available"] = _src.OCR_AVAILABLE
    st["ocr_langs"] = _src.OCR_LANG                 # es. "ita+eng" ("" = predefinita)
    st["ocr_reason"] = _src.OCR_REASON             # "module" | "binary" | ""
    # download automatico solo su Windows e solo se manca il binario (se manca
    # il modulo Python pytesseract, scaricare Tesseract non servirebbe)
    st["ocr_can_install"] = os.name == "nt" and _src.OCR_REASON != "module"
    st["ocr_install"] = _OCR_JOB["state"]
    st["ocr_url"] = _tess.DEFAULT_URL
    st["indexed"] = bool(idx)
    st["default_folder"] = archive.SOURCES_DEFAULT
    return jsonify(st)


@bp.route("/api/sources/pick", methods=["POST"])
def api_sources_pick():
    """Apre il selezionatore cartelle nativo del sistema (l'app gira in locale)
    e ritorna il percorso scelto. Se non c'è un ambiente grafico, il client
    ripiega sull'inserimento manuale del percorso."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        start = request.get_json(silent=True) or {}
        folder = filedialog.askdirectory(
            title="Scegli la cartella delle fonti",
            initialdir=start.get("start") or os.path.expanduser("~"))
        root.destroy()
        return jsonify({"folder": folder or ""})
    except Exception as e:
        logging.warning(f"Dialog cartella non disponibile: {e}")
        return jsonify({"error": "dialog non disponibile", "detail": str(e)}), 501


@bp.route("/api/sources/scan", methods=["POST"])
def api_sources_scan():
    """Avvia l'indicizzazione della cartella in un thread di lavoro e ritorna
    subito. L'avanzamento si legge con /api/sources/progress. Corpo: {folder}."""
    data = request.get_json(silent=True) or {}
    folder = str(data.get("folder") or "").strip().strip('"')
    if not folder:
        folder = archive.SOURCES_DEFAULT          # 'sources' accanto all'eseguibile
    if not os.path.isdir(folder):
        return jsonify({"error": f"cartella non trovata: {folder}"}), 404
    with _scan_lock:
        if _scan["running"]:
            return jsonify({"error": "scansione già in corso", "running": True}), 409
        _scan.update({"running": True, "done": 0, "total": 0, "name": "",
                      "finished": False, "error": "", "summary": None})
    _threading.Thread(target=_run_scan, args=(folder,), daemon=True).start()
    return jsonify({"started": True})


@bp.route("/api/sources/progress")
def api_sources_progress():
    """Stato dell'indicizzazione in corso (per la barra 'file n di n')."""
    return jsonify(dict(_scan))


@bp.route("/api/sources/search", methods=["POST"])
def api_sources_search():
    """Cerca un termine nelle fonti indicizzate. Corpo: {q, mode:'partial'|'total'}."""
    data = request.get_json(silent=True) or {}
    q = str(data.get("q") or "").strip()
    mode = "total" if data.get("mode") == "total" else "partial"
    if len(q) < 2:
        return jsonify({"error": "termine troppo corto"}), 400
    idx = sources_index()
    if not idx:
        return jsonify({"error": "nessuna cartella fonti indicizzata"}), 400
    return jsonify(_src.search_index(idx, q, mode))


@bp.route("/api/sources/multi", methods=["POST"])
def api_sources_multi():
    """Cerca più termini insieme (le parole della chiave scheda). Corpo:
    {terms:[...], mode}. Ritorna i termini positivi (con conteggio) e i file,
    ciascuno con i termini che vi corrispondono."""
    data = request.get_json(silent=True) or {}
    terms = data.get("terms") or []
    mode = "total" if data.get("mode") == "total" else "partial"
    idx = sources_index()
    if not idx:
        return jsonify({"error": "nessuna cartella fonti indicizzata"}), 400
    return jsonify(_src.search_multi(idx, terms, mode))


@bp.route("/api/sources/file/<fid>")
def api_sources_file(fid):
    """Serve un file indicizzato (per l'anteprima), validando che appartenga
    all'indice e stia dentro la cartella scansionata."""
    idx = sources_index()
    if not idx:
        abort(404)
    f = _src.find_file(idx, fid)
    if not f:
        abort(404)
    # risolve il percorso ORA, cercando PRIMA nella cartella 'fonti' accanto
    # all'eseguibile: è quella la posizione dei documenti, e l'unica che resta
    # valida portando il programma su un altro PC (l'indice conserva il
    # percorso assoluto della macchina che ha fatto la scansione).
    path, folder = _src.locate_file(idx, f.get("rel"), BASE_DIR, archive.SOURCES_DEFAULT)
    if not path:
        logging.warning(
            f"Fonte non trovata: {f.get('rel')!r}. Cercata in: "
            + " | ".join(_src.folder_candidates(idx, BASE_DIR, archive.SOURCES_DEFAULT)))
        abort(404)
    return send_from_directory(os.path.dirname(path), os.path.basename(path))
