# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""The page itself, the images of the archive, the ontology and the platform icons."""
# "Festina lente." (Augustus, in Suetonius, Divus Augustus)
# Make haste slowly.
import json
import logging
import os
import re

from flask import abort, Blueprint, jsonify, render_template, send_from_directory

from .. import ontology as onto
from .. import ontology_i18n as onto_i18n
from .. import ftm
from ..paths import RES_DIR
from ..core import DATA_DIR, PHOTO_EXT

bp = Blueprint("pages", __name__)


def entity_icons():
    """Keys of the colour node icons installed in static/icons/entities (index.json,
    written by scripts/icons/install.py); empty when the folder is missing."""
    try:
        with open(os.path.join(os.path.join(RES_DIR, "static"), "icons", "entities", "index.json"), encoding="utf-8") as f:
            keys = json.load(f)
        return [str(k) for k in keys if isinstance(k, str)]
    except (OSError, ValueError):
        return []


@bp.route("/")
def index():
    # versione = mtime di app.js/style.css: forza il browser a riscaricare i
    # file statici quando cambiano (niente più JS servito dalla cache)
    def _mtime(fn):
        try:
            return int(os.path.getmtime(os.path.join(os.path.join(RES_DIR, "static"), fn)))
        except OSError:
            return 0
    ver = max(_mtime("app.js"), _mtime("style.css"), _mtime("i18n.js"))
    return render_template("index.html", asset_ver=ver, fa_icons=fa_icons(),
                           ontology=onto.public(), base_icons=onto.BASE_ICONS,
                           onto_i18n=onto_i18n.table(), ftm_edges=ftm.edges_public(),
                           entity_icons=entity_icons())


_FA_DIR = os.path.join(RES_DIR, "static", "vendor", "fa")
_fa_cache = {}


def fa_icons():
    """Icone Font Awesome Free (static/vendor/fa): {nome: svg}. Stanno dentro
    l'app, non su internet. Si inseriscono nella pagina, cosi' sono pronte
    prima che il grafo venga disegnato."""
    if not _fa_cache:
        try:
            for fn in os.listdir(_FA_DIR):
                if fn.endswith(".svg"):
                    with open(os.path.join(_FA_DIR, fn), encoding="utf-8") as f:
                        svg = re.sub(r"<!--.*?-->", "", f.read(), flags=re.S).strip()
                    _fa_cache[fn[:-4]] = svg
        except OSError as e:
            logging.warning(f"Icone non trovate in {_FA_DIR}: {e}")
    return _fa_cache


@bp.route("/api/ontology")
def api_ontology():
    return jsonify(onto.public())


@bp.route("/media/<path:relpath>")
def media(relpath):
    """Serve le immagini contenute in DATA_DIR (solo lettura, path controllato)."""
    root = os.path.abspath(DATA_DIR)
    full = os.path.abspath(os.path.join(root, relpath))
    if not full.startswith(root + os.sep) or not os.path.isfile(full):
        abort(404)
    if not full.lower().endswith(PHOTO_EXT):
        abort(403)
    return send_from_directory(os.path.dirname(full), os.path.basename(full),
                               max_age=3600)


@bp.route("/api/brand-icons")
def api_brand_icons():
    """Sigle dei marchi che hanno l'icona in static/vendor/icons/.
    Il front-end la usa per non chiedere file inesistenti: le icone stanno
    DENTRO l'eseguibile, non su internet, e non tutti i marchi ce l'hanno
    (per quelli che mancano resta il badge con l'iniziale)."""
    cartella = os.path.join(RES_DIR, "static", "vendor", "icons")
    try:
        nomi = [f[:-4] for f in os.listdir(cartella) if f.lower().endswith(".svg")]
    except OSError:
        nomi = []
    return jsonify(sorted(nomi))
