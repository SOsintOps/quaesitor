# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Cases: list, create, rename, switch, delete, merge."""
# "Suum cuique." (after Cicero, De Officiis)
# To each his own.
import logging
import re

from flask import Blueprint, jsonify, request

from .. import store
from ..core import _truthy
from ..labels import _cache

bp = Blueprint("cases", __name__)


# ============================== CASES (DOSSIERS) ==============================
# Each case has its own database (store.py): nodes, cards, links, notes, views
# and imported JSON. The transliteration dictionary and the document index are
# shared by all cases.
def _case_name(data, key="name"):
    return re.sub(r"\s+", " ", str(data.get(key) or "")).strip()[:120]


@bp.route("/api/cases")
def api_cases():
    return jsonify({"items": store.list_cases(), "current": store.current_case()})


@bp.route("/api/cases/add", methods=["POST"])
def api_cases_add():
    data = request.get_json(silent=True) or {}
    name = _case_name(data)
    if not name:
        return jsonify({"error": "nome del caso mancante"}), 400
    c = store.create_case(name, str(data.get("description") or "")[:2000])
    store.open_case(c["id"])
    _cache["key"] = None
    logging.info(f"Nuovo caso: {name} ({c['id']})")
    return jsonify({"ok": True, "case": c})


@bp.route("/api/cases/update", methods=["POST"])
def api_cases_update():
    data = request.get_json(silent=True) or {}
    cid = str(data.get("id") or "")
    if not store.get_case(cid):
        return jsonify({"error": "caso non trovato"}), 404
    name = _case_name(data)
    if not name:
        return jsonify({"error": "nome del caso mancante"}), 400
    c = store.update_case(cid, name, str(data.get("description") or "")[:2000])
    return jsonify({"ok": True, "case": c})


@bp.route("/api/cases/switch", methods=["POST"])
def api_cases_switch():
    data = request.get_json(silent=True) or {}
    cid = str(data.get("id") or "")
    if not store.case_exists(cid):
        return jsonify({"error": "caso non trovato"}), 404
    store.open_case(cid)
    _cache["key"] = None
    logging.info(f"Caso aperto: {cid}")
    return jsonify({"ok": True, "case": store.get_case(cid)})


@bp.route("/api/cases/delete", methods=["POST"])
def api_cases_delete():
    """Deletes the case and ALL its content (its database)."""
    data = request.get_json(silent=True) or {}
    cid = str(data.get("id") or "")
    if not store.get_case(cid):
        return jsonify({"error": "caso non trovato"}), 404
    was_current = cid == store.current_case()
    store.delete_case(cid)
    if was_current:
        # switch to another case; if it was the last one, none stays open
        # (the interface asks to create one)
        altri = store.list_cases()
        if altri:
            store.open_case(altri[0]["id"])
        _cache["key"] = None
    logging.info(f"Caso eliminato: {cid}")
    return jsonify({"ok": True, "current": store.current_case()})


@bp.route("/api/cases/merge", methods=["POST"])
def api_cases_merge():
    """{ids: [...], name, delete_sources: bool} -> new case with the content of
    all of them; identical nodes become one (the differences as extra cards)."""
    data = request.get_json(silent=True) or {}
    ids = [str(x) for x in (data.get("ids") or []) if store.get_case(str(x))]
    ids = list(dict.fromkeys(ids))
    if len(ids) < 2:
        return jsonify({"error": "scegli almeno due casi da unire"}), 400
    name = _case_name(data) or " + ".join(store.get_case(i)["name"] for i in ids)[:120]
    c = store.merge_cases(ids, name, str(data.get("description") or "")[:2000])
    store.open_case(c["id"])
    _cache["key"] = None
    if _truthy(data.get("delete_sources")):
        for i in ids:
            store.delete_case(i)
    logging.info(f"Casi uniti in {name}: {ids}")
    return jsonify({"ok": True, "case": c})
