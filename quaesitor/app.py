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

# RES_DIR: le RISORSE dell'app (templates, static), nel package o, nell'eseguibile
# PyInstaller, estratte in sys._MEIPASS/quaesitor. BASE_DIR: la cartella del
# programma, dove stanno i DATI dell'utente (data/, sources/, chatbot.conf...),
# esterni, modificabili e persistenti. Vedi paths.py.

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
    """Qualsiasi operazione sul database del caso senza un caso aperto."""
    return jsonify({"error": str(e), "no_case": True}), 409


def main():
    """Avvia il server (app.py nella radice; l'eseguibile PyInstaller parte da lì)."""
    port = int(os.environ.get("PORT", "5000"))
    frozen = FROZEN
    if frozen:
        # eseguibile finito: apre il browser da solo e non usa il reloader
        # (che rilancerebbe un secondo processo)
        import threading
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
        logging.info(f"Quaesitor avviato su http://127.0.0.1:{port}")
        logging.info(f"Dati letti da: {DATA_DIR}")
        if not os.path.isdir(DATA_DIR):
            logging.warning("La cartella 'data' non è accanto all'eseguibile: "
                            "il grafo sarà vuoto finché non la copi qui.")
    app.run(debug=not frozen, port=port, use_reloader=not frozen)