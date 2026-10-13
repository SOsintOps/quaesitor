# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""The Flask application: the page, the API blueprints and the start of the server.

    blueprints/   the routes, one module per area (pages, cases, graph, translit,
                  imports, ftm_io, transcription, opensanctions, epieos_api, ai,
                  documents)
    the shared code, in layers: each module imports only from those before it
                  core, chatbot, transliteration, normalize, records, identifiers,
                  labels, dictionary, archive, bulk_import
    store, ftm, ftm_bundle, epieos, ontology, sources, transcripts, audio/
                  the archive database, the importers and the services, as before
"""
# "Homo sum, humani nihil a me alienum puto." (Terence, Heauton Timorumenos)
# I am human: nothing human is alien to me.
import logging
import os

from flask import Flask, jsonify

from . import store
from .blueprints import (ai, cases, documents, epieos_api, ftm_io, graph, imports, opensanctions,
                         pages, transcription, translit)
from .core import DATA_DIR
from .paths import FROZEN, RES_DIR

# RES_DIR: the app's RESOURCES (templates, static), in the package or, in the
# PyInstaller executable, extracted to sys._MEIPASS/quaesitor. BASE_DIR: the program
# folder, where the user's DATA live (data/, sources/, chatbot.conf...), external,
# editable and persistent. See paths.py.

app = Flask(
    __name__,
    template_folder=os.path.join(RES_DIR, "templates"),
    static_folder=os.path.join(RES_DIR, "static"),
)
for _bp in (pages, cases, graph, translit, imports, ftm_io, transcription, opensanctions,
            epieos_api, ai, documents):
    app.register_blueprint(_bp.bp)


@app.errorhandler(store.NoCaseError)
def _no_case(e):
    """Any operation on the case database with no case open."""
    return jsonify({"error": str(e), "no_case": True}), 409


def main():
    """Starts the server (app.py in the root; the PyInstaller executable starts from there)."""
    port = int(os.environ.get("PORT", "5000"))
    frozen = FROZEN
    if frozen:
        # built executable: opens the browser by itself and does not use the reloader
        # (which would launch a second process)
        import threading
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
        logging.info(f"Quaesitor avviato su http://127.0.0.1:{port}")
        logging.info(f"Dati letti da: {DATA_DIR}")
        if not os.path.isdir(DATA_DIR):
            logging.warning("La cartella 'data' non è accanto all'eseguibile: "
                            "il grafo sarà vuoto finché non la copi qui.")
    app.run(debug=not frozen, port=port, use_reloader=not frozen)