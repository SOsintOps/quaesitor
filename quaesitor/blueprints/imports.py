# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Bulk import (CSV, Excel) and the JSON exports of third-party OSINT apps."""
# "Ex nihilo nihil fit." (after Lucretius, De Rerum Natura)
# Nothing comes from nothing.
import logging
import os

from flask import Blueprint, jsonify, request

from .. import ontology as onto
from .. import ftm, store
from ..core import _decode_upload, _flat, _truthy, IMPORT_MAX_MB, NodeError
from ..records import parse_records
from ..archive import current_graph
from ..bulk_import import _plan_json, commit_plan, IMPORT_MAX_ROWS, map_header, plan_import

bp = Blueprint("imports", __name__)


def read_table(filename, blob):
    """File CSV, Excel (.xlsx) o entita' Follow the Money (JSON) -> lista di
    righe (liste di stringhe)."""
    name = (filename or "").lower()
    if ftm.is_ftm(name, blob):
        try:
            return ftm.entities_to_rows(blob, native_types=onto.TYPES)
        except ValueError as e:
            raise NodeError(f"file Follow the Money: {e}")
    if name.endswith((".xlsx", ".xlsm")) or blob[:2] == b"PK":
        try:
            import openpyxl
        except ImportError:
            raise NodeError("per leggere i file Excel serve il modulo openpyxl")
        import io
        try:
            wb = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True)
        except Exception as e:
            raise NodeError(f"file Excel illeggibile: {e}")
        for ws in wb.worksheets:               # il primo foglio con dei dati
            rows = []
            for r in ws.iter_rows(values_only=True):
                cells = ["" if v is None else
                         (str(int(v)) if isinstance(v, float) and v.is_integer() else str(v))
                         for v in r]
                if any(c.strip() for c in cells):
                    rows.append(cells)
                if len(rows) > IMPORT_MAX_ROWS + 1:
                    break
            if rows:
                return rows
        return []
    if name.endswith(".xls"):
        raise NodeError("il vecchio formato .xls non e' supportato: salva il file come .xlsx o .csv")
    import csv
    import io
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = blob.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    sample = text[:5000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = max(",;\t|", key=sample.count)
    rows = [r for r in csv.reader(io.StringIO(text), dialect) if any(c.strip() for c in r)]
    return rows[:IMPORT_MAX_ROWS + 1]


def import_columns(table):
    """Per la procedura guidata: intestazioni, esempi e mappatura automatica.
    'header' dice se la prima riga sembra un'intestazione."""
    if not table:
        raise NodeError("il file e' vuoto")
    auto = map_header(table[0]) or {}
    width = max(len(r) for r in table[:50])
    first = table[0] + [""] * (width - len(table[0]))
    body = table[1:] if auto else table
    cols = []
    for c in range(width):
        samples = [r[c] for r in body[:40] if c < len(r) and str(r[c]).strip()][:3]
        cols.append({"index": c, "name": first[c].strip(), "auto": auto.get(c, ""),
                     "samples": [str(x)[:60] for x in samples]})
    return {"columns": cols, "header": bool(auto), "first_row": first,
            "rows": len(body), "max_rows": IMPORT_MAX_ROWS}


def _import_opts(data):
    """Opzioni della procedura guidata dalla richiesta (tutte facoltative)."""
    mapping = data.get("mapping")
    out = {"mapping": None, "has_header": None, "defaults": {}}
    if isinstance(mapping, dict) and mapping:
        out["mapping"] = {int(k): str(v) for k, v in mapping.items()
                          if str(k).isdigit() and str(v or "").strip()}
        out["has_header"] = bool(data.get("header", True))
    d = data.get("defaults") if isinstance(data.get("defaults"), dict) else {}
    out["defaults"] = {k: str(d.get(k) or "").strip()[:120] for k in ("type1", "type2", "rel")}
    return out


@bp.route("/api/imports")
def api_imports_list():
    return jsonify({"items": store.list_imports(str(request.args.get("anchor") or "") or None)})


@bp.route("/api/imports/add", methods=["POST"])
def api_imports_add():
    """{anchor: id del nodo, filename, content: testo del JSON, dossier: bool}"""
    data = request.get_json(silent=True) or {}
    anchor = str(data.get("anchor") or "").strip()
    filename = os.path.basename(str(data.get("filename") or "export.json"))[:200]
    content = str(data.get("content") or "")
    if not anchor:
        return jsonify({"error": "scegli il nodo (target) a cui agganciare il file"}), 400
    if len(content.encode("utf-8")) > IMPORT_MAX_MB * 1024 * 1024:
        return jsonify({"error": f"file troppo grande (max {IMPORT_MAX_MB} MB)"}), 400
    node = next((n for n in current_graph()["nodes"]
                 if n["id"] == anchor or anchor in (n.get("alias_ids") or [])), None)
    if node is None:
        return jsonify({"error": "nodo non trovato"}), 404
    recs = [r for r in parse_records(content) if isinstance(r, dict)]
    if not recs:
        return jsonify({"error": f"{filename}: nessun record JSON leggibile"}), 400
    iid = store.add_import(node["id"], _flat(node.get("label")) or node["id"], filename,
                           content, len(recs), _truthy(data.get("dossier")),
                           node.get("ntype") or "generic", node.get("platform") or "generic")
    logging.info(f"Importato {filename} ({len(recs)} record) su {node['id']}")
    return jsonify({"ok": True, "id": iid, "records": len(recs), "anchor": node["id"]})


@bp.route("/api/imports/delete", methods=["POST"])
def api_imports_delete():
    data = request.get_json(silent=True) or {}
    try:
        iid = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"error": "id mancante"}), 400
    if not store.delete_import(iid):
        return jsonify({"error": "import non trovato"}), 404
    return jsonify({"ok": True, "id": iid})


@bp.route("/api/import/columns", methods=["POST"])
def api_import_columns():
    """Procedura guidata, passo 2: colonne del file, esempi e mappatura
    automatica dalle intestazioni (l'utente puo' cambiarla)."""
    data = request.get_json(silent=True) or {}
    try:
        table = read_table(data.get("filename"), _decode_upload(data))
        out = import_columns(table)
    except NodeError as e:
        return jsonify({"error": str(e)}), 400
    out["ok"] = True
    return jsonify(out)


@bp.route("/api/import/preview", methods=["POST"])
def api_import_preview():
    """Legge il file e mostra cosa verra' creato, senza scrivere niente."""
    data = request.get_json(silent=True) or {}
    try:
        table = read_table(data.get("filename"), _decode_upload(data))
        plan, header = plan_import(table, **_import_opts(data))
    except NodeError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True, "columns": sorted(set(header.values())),
                    "rows": _plan_json(plan), "total": len(plan)})


@bp.route("/api/import/commit", methods=["POST"])
def api_import_commit():
    """Crea davvero i nodi e i collegamenti del file."""
    data = request.get_json(silent=True) or {}
    skip = {int(x) for x in (data.get("skip") or []) if str(x).isdigit()}
    try:
        table = read_table(data.get("filename"), _decode_upload(data))
        plan, _ = plan_import(table, **_import_opts(data))
        res = commit_plan(plan, skip)
    except NodeError as e:
        return jsonify({"error": str(e)}), 400
    logging.info(f"Importazione: {res['nodes']} nodi, {res['links']} collegamenti, "
                 f"{len(res['errors'])} righe con errori")
    return jsonify(res)
