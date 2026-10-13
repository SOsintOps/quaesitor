# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Follow the Money: inspect, import with progress, export."""
# "Pecunia non olet." (attributed to Vespasian, in Suetonius)
# Money does not smell.
import json
import logging
import os
import re
import threading
import threading as _threading

from flask import Blueprint, jsonify, request

from .. import ontology as onto
from .. import ftm, ftm_bundle, store
from ..core import (
    _decode_upload, _scan, _scan_lock, DATA_DIR, FTM_BATCH, FTM_MAX_MB, MEDIA_DIRNAME,
    NodeError,
)
from ..labels import _cache
from ..archive import _run_scan, _sources_folder, current_graph, load_annotations
from ..bulk_import import _ftm_mapping, commit_plan, ftm_reserved, plan_import

bp = Blueprint("ftm_io", __name__)


_ftm_job = {"running": False, "finished": False, "error": "", "done": 0, "total": 0,
            "nodes": 0, "links": 0, "updated": 0, "same_links": 0, "errors": 0, "stage": ""}
_ftm_lock = threading.Lock()


def _ftm_source(data):
    """What an FtM import reads: ("bundle", path|bytes) for a Cognitor bundle, or
    ("blob", bytes) for a file of entities. {path} reads a file of this computer
    (the program runs locally), without the 20 MB limit of the upload: a bundle with
    photos is larger. {data} is the upload as before."""
    path = str(data.get("path") or "").strip().strip('"')
    if path:
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isfile(path):
            raise NodeError(f"file not found: {path}")
        if ftm_bundle.is_bundle(path):
            return "bundle", path
        if os.path.getsize(path) > FTM_MAX_MB * 1024 * 1024:
            raise NodeError(f"file too large: max {FTM_MAX_MB} MB")
        with open(path, "rb") as f:
            return "blob", f.read()
    blob = _decode_upload(data)
    if blob[:2] == b"PK" and ftm_bundle.is_bundle(blob):
        return "bundle", blob
    if len(blob) > FTM_MAX_MB * 1024 * 1024:
        raise NodeError(f"file too large: max {FTM_MAX_MB} MB")
    return "blob", blob


def _run_bundle_import(src, opts):
    """A Cognitor bundle: images under data/media/cognitor/<case>/, transcripts in the
    sources folder (then indexed), entities through the same path as an FtM file."""
    try:
        _ftm_job["stage"] = "files"
        with ftm_bundle.Bundle(src) as b:
            media = b.install_media(DATA_DIR, MEDIA_DIRNAME)
            _ftm_job["images"] = len(media)
            _ftm_job["images_refused"] = len(getattr(b, "refused", []))
            paths = b.install_transcripts(_sources_folder())
            _ftm_job["transcripts"] = len(paths)
            blob = b.entities_blob()
            opts = dict(opts, media=media, dataset=opts.get("dataset") or str(b.manifest.get("dataset") or ""))
    except Exception as e:
        logging.error(f"Unreadable FtM bundle: {e}")
        _ftm_job["error"] = str(e)
        _ftm_job["running"] = False
        _ftm_job["finished"] = True
        return
    _run_ftm_import(blob, opts)
    if _ftm_job.get("transcripts") and not _ftm_job.get("error"):
        # the transcripts become searchable: same scan as the button of the sources
        folder = _sources_folder()
        with _scan_lock:
            if not _scan["running"] and os.path.isdir(folder):
                _scan.update({"running": True, "done": 0, "total": 0, "name": "",
                              "finished": False, "error": "", "summary": None})
                _threading.Thread(target=_run_scan, args=(folder,), daemon=True).start()
                _ftm_job["sources_scan"] = True


def _run_ftm_import(blob, opts):
    try:
        _ftm_job["stage"] = "filter"
        ents = ftm.filter_entities(blob, schemas=opts.get("schemas"), text=opts.get("text", ""),
                                   max_entities=opts.get("max_entities", 0),
                                   connected_only=opts.get("connected_only", False))
        if not ents:
            raise NodeError("no entity matches the filters")
        media = dict(opts.get("media") or {})
        for e in ents.values():
            # an Image exported by this program names a file already under DATA_DIR/media
            if e.get("schema") == "Image":
                for fn in e["properties"].get("fileName") or []:
                    rel = str(fn).replace("\\", "/").lstrip("/")
                    if rel not in media and rel.lower().startswith(MEDIA_DIRNAME + "/") and ".." not in rel \
                            and os.path.isfile(os.path.join(DATA_DIR, *rel.split("/"))):
                        media[rel] = rel
        table = ftm.rows_from_entities(ents, native_types=onto.TYPES, media=media,
                                       reserved=ftm_reserved)
        header, body = table[0], table[1:]
        mapping = _ftm_mapping(header)
        _ftm_job["total"] = len(body)
        _ftm_job["stage"] = "import"
        for i in range(0, len(body), FTM_BATCH):
            batch = [header] + body[i:i + FTM_BATCH]
            plan, _ = plan_import(batch, mapping=mapping, has_header=True)
            res = commit_plan(plan, update=True, ftm_dataset=opts.get("dataset") or "")
            for k in ("nodes", "links", "updated", "same_links"):
                _ftm_job[k] += res.get(k, 0)
            _ftm_job["errors"] += len(res.get("errors") or [])
            _ftm_job["done"] = min(len(body), i + FTM_BATCH)
        _cache["key"] = None
        logging.info(f"FtM import: {_ftm_job['nodes']} nodes, {_ftm_job['links']} links, "
                     f"{_ftm_job['updated']} updated")
    except Exception as e:
        logging.error(f"FtM import failed: {e}", exc_info=not isinstance(e, NodeError))
        _ftm_job["error"] = str(e)
    finally:
        _ftm_job["running"] = False
        _ftm_job["finished"] = True


@bp.route("/api/ftm/inspect", methods=["POST"])
def api_ftm_inspect():
    """Counts per schema and dataset of an FtM file. Body: {filename, data}."""
    data = request.get_json(silent=True) or {}
    try:
        kind, src = _ftm_source(data)
        if kind == "bundle":
            with ftm_bundle.Bundle(src) as b:
                out = ftm.inspect(b.entities_blob())
                out.update(b.summary())
            out["size"] = os.path.getsize(src) if isinstance(src, str) else len(src)
        else:
            out = ftm.inspect(src)
    except (NodeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    out["ok"] = True
    out["native"] = {sc: (ftm.FTM_TYPE_OF.get(sc) or ftm.TYPE.get(sc) or "text")
                     for sc in list(out["schemas"])}
    return jsonify(out)


@bp.route("/api/ftm/import", methods=["POST"])
def api_ftm_import():
    """Starts the import in a thread. Body: {data, schemas: [...], text,
    max_entities, connected_only, dataset}. Progress: /api/ftm/progress."""
    data = request.get_json(silent=True) or {}
    try:
        kind, src = _ftm_source(data)
        if kind == "bundle":
            with ftm_bundle.Bundle(src):          # verified before the thread starts
                pass
    except (NodeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    if not store.current_case():
        return jsonify({"error": "no case open"}), 400
    try:
        max_entities = max(0, int(data.get("max_entities") or 0))
    except (TypeError, ValueError):
        max_entities = 0
    opts = {"schemas": [str(s) for s in (data.get("schemas") or []) if str(s) in ftm.schema()],
            "text": str(data.get("text") or "")[:200], "max_entities": max_entities,
            "connected_only": bool(data.get("connected_only")),
            "dataset": str(data.get("dataset") or "")[:120]}
    with _ftm_lock:
        if _ftm_job["running"]:
            return jsonify({"error": "import already running", "running": True}), 409
        _ftm_job.update({"running": True, "finished": False, "error": "", "done": 0, "total": 0,
                         "nodes": 0, "links": 0, "updated": 0, "same_links": 0, "errors": 0,
                         "stage": "parse", "images": 0, "images_refused": 0, "transcripts": 0,
                         "sources_scan": False})
    target = _run_bundle_import if kind == "bundle" else _run_ftm_import
    threading.Thread(target=target, args=(src, opts), daemon=True).start()
    return jsonify({"started": True})


@bp.route("/api/ftm/progress")
def api_ftm_progress():
    return jsonify(dict(_ftm_job))


@bp.route("/api/ftm/export", methods=["GET", "POST"])
def api_ftm_export():
    """The case (or the nodes given in {ids}) as Follow the Money entities, as
    JSON lines readable by Aleph, OpenSanctions and the ftm CLI.
    ?summary=1 returns only the summary (how many nodes, how many without a schema)."""
    from flask import Response
    data = request.get_json(silent=True) or {} if request.method == "POST" else {}
    only = {str(x) for x in (data.get("ids") or [])} or None
    g = current_graph()
    if g.get("no_case"):
        return jsonify({"error": "no case open"}), 400
    ann = load_annotations()
    entries = {str(x.get("id")): x for x in ann["added"]}
    ents, summary = ftm.export_entities(g, entries, store.ftm_by_node(), only)
    new_ids = summary.pop("new_ids", [])
    if request.args.get("summary") or data.get("summary"):
        return jsonify(dict(summary, ok=True))
    if new_ids:                                     # re-importing the export lands on the same nodes
        store.ftm_set((f, n, sc, "export") for f, n, sc in new_ids)
    body = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in ents)
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", (store.get_case(store.current_case()) or {}).get("name") or "case")
    logging.info(f"FtM export: {summary['nodes']} nodes, {summary['links']} links")
    return Response(body, mimetype="application/json; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename={name}.ftm.json",
                             "X-Ftm-Summary": json.dumps(summary)})
