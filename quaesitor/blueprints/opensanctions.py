# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""OpenSanctions: configuration, search, match, import."""
# "Fiat iustitia, ruat caelum." (legal maxim)
# Let justice be done, though the heavens fall.
from urllib.parse import quote
import logging
import re

from flask import Blueprint, jsonify, request

from .. import ontology as onto
from .. import ftm, store
from ..core import (
    _http_json_full, _load_services_conf, _save_kv_conf, FTM_BATCH, SERVICES, SERVICES_CONF,
)
from ..labels import _cache
from ..bulk_import import _ftm_mapping, commit_plan, ftm_reserved, plan_import

bp = Blueprint("opensanctions", __name__)


OSA_KEYS = ("enabled", "endpoint", "api_key", "dataset", "timeout")


def osa_ready():
    return bool(SERVICES["opensanctions_enabled"] and SERVICES["opensanctions_endpoint"])


def _osa_public():
    k = SERVICES.get("opensanctions_api_key") or ""
    return {"enabled": bool(SERVICES["opensanctions_enabled"]), "endpoint": SERVICES["opensanctions_endpoint"],
            "has_key": bool(k), "key_hint": ("…" + k[-4:]) if len(k) > 8 else ("•" * len(k)),
            "dataset": SERVICES["opensanctions_dataset"], "timeout": SERVICES["opensanctions_timeout"],
            "ready": osa_ready()}


def _http_json(url, payload=None, headers=None, timeout=20):
    """GET (payload None) or POST JSON. Returns (data, error)."""
    data, err, _, _ = _http_json_full(url, payload, headers, timeout)
    return data, err


def _osa_call(path, payload=None, query=None):
    if not osa_ready():
        return None, "OpenSanctions switched off (OpenSanctions panel)"
    url = SERVICES["opensanctions_endpoint"] + path
    if query:
        url += "?" + "&".join(f"{k}={quote(str(v))}" for k, v in query.items() if v not in (None, ""))
    headers = {}
    if SERVICES.get("opensanctions_api_key"):
        headers["Authorization"] = "ApiKey " + SERVICES["opensanctions_api_key"]
    return _http_json(url, payload, headers, SERVICES["opensanctions_timeout"])


def _osa_brief(e):
    """A result reduced to the essentials for the list."""
    p = e.get("properties") or {}
    return {"id": e.get("id"), "schema": e.get("schema"), "caption": e.get("caption") or (p.get("name") or [""])[0],
            "countries": (p.get("country") or p.get("nationality") or p.get("jurisdiction") or [])[:4],
            "topics": (p.get("topics") or [])[:4], "datasets": (e.get("datasets") or [])[:4],
            "birth": (p.get("birthDate") or p.get("incorporationDate") or [""])[0],
            "score": e.get("score"), "match": e.get("match")}


def _osa_flatten(e, out):
    """Entities with nested properties (?nested=true) -> flat {id: entity}:
    the nested entities become entries of their own, the id stays in their place."""
    if not isinstance(e, dict) or not e.get("id") or not e.get("schema"):
        return None
    props = {}
    for k, vals in (e.get("properties") or {}).items():
        flat = []
        for v in (vals if isinstance(vals, list) else [vals]):
            if isinstance(v, dict):
                sub = _osa_flatten(v, out)
                if sub:
                    flat.append(sub)
            elif v not in (None, ""):
                flat.append(str(v))
        if flat:
            props[k] = flat
    out[e["id"]] = {"id": e["id"], "schema": e["schema"], "properties": props,
                    "datasets": e.get("datasets") or []}
    return e["id"]


@bp.route("/api/osa/config", methods=["GET", "POST"])
def api_osa_config():
    if request.method == "GET":
        return jsonify(_osa_public())
    data = request.get_json(silent=True) or {}
    up = {}
    for k in OSA_KEYS:
        if k not in data:
            continue
        v = data[k]
        if k == "enabled":
            up["opensanctions_enabled"] = "true" if v in (True, "true", "1", 1, "on") else "false"
            continue
        v = re.sub(r"[\r\n]+", " ", str(v if v is not None else "")).strip()[:500]
        if k == "api_key" and not v and not data.get("clear_key"):
            continue
        if k == "endpoint" and v and not re.match(r"^https?://[^\s]+$", v, re.I):
            return jsonify({"error": "invalid endpoint (http:// or https:// needed)"}), 400
        if k == "timeout":
            try:
                v = str(max(3, min(120, int(float(v)))))
            except ValueError:
                return jsonify({"error": "invalid timeout"}), 400
        up["opensanctions_" + k] = v
    try:
        _save_kv_conf(SERVICES_CONF, up, "# services.conf - optional online services (OpenSanctions). Do not publish: it holds the API key.")
    except OSError as e:
        return jsonify({"error": f"cannot write services.conf: {e}"}), 500
    SERVICES.clear()
    SERVICES.update(_load_services_conf())
    logging.info(f"OpenSanctions configuration updated: {sorted(up)}")
    return jsonify(_osa_public())


@bp.route("/api/osa/test", methods=["POST"])
def api_osa_test():
    """Connection test: the instance's /healthz, then a minimal search."""
    data, err = _osa_call("/healthz")
    if err:
        return jsonify({"ok": False, "error": err}), 502
    data, err = _osa_call(f"/search/{SERVICES['opensanctions_dataset']}", query={"q": "test", "limit": 1})
    if err:
        return jsonify({"ok": False, "error": err}), 502
    return jsonify({"ok": True, "total": (data.get("total") or {}).get("value") if isinstance(data, dict) else None})


@bp.route("/api/osa/search")
def api_osa_search():
    """Text search: ?q=&schema=&limit= -> reduced list."""
    q = str(request.args.get("q") or "").strip()[:200]
    if len(q) < 2:
        return jsonify({"error": "search term too short"}), 400
    schema = str(request.args.get("schema") or "").strip()
    try:
        limit = max(1, min(50, int(request.args.get("limit", 20))))
    except ValueError:
        limit = 20
    data, err = _osa_call(f"/search/{SERVICES['opensanctions_dataset']}",
                          query={"q": q, "schema": schema or None, "limit": limit})
    if err:
        return jsonify({"error": err}), 502
    results = [_osa_brief(e) for e in (data.get("results") or [])]
    return jsonify({"ok": True, "query": q, "results": results,
                    "total": (data.get("total") or {}).get("value", len(results))})


@bp.route("/api/osa/match", methods=["POST"])
def api_osa_match():
    """Structured match (name + date of birth / country / number):
    {schema, properties: {...}} -> matches with a score."""
    data = request.get_json(silent=True) or {}
    schema = str(data.get("schema") or "Person").strip()
    props = {k: ([v] if not isinstance(v, list) else v) for k, v in (data.get("properties") or {}).items() if v}
    if not props.get("name"):
        return jsonify({"error": "at least the name is needed"}), 400
    body = {"queries": {"q1": {"schema": schema, "properties": props}}}
    out, err = _osa_call(f"/match/{SERVICES['opensanctions_dataset']}", payload=body, query={"limit": 10})
    if err:
        return jsonify({"error": err}), 502
    res = ((out.get("responses") or {}).get("q1") or {}).get("results") or []
    return jsonify({"ok": True, "results": [_osa_brief(e) for e in res]})


@bp.route("/api/osa/import", methods=["POST"])
def api_osa_import():
    """Brings the given entities ({ids: [...]}) into the case with their nested
    relationships, like an FtM file (same engine: ids kept, updates)."""
    data = request.get_json(silent=True) or {}
    ids = [str(x) for x in (data.get("ids") or []) if str(x).strip()][:50]
    if not ids:
        return jsonify({"error": "no entity given"}), 400
    if not store.current_case():
        return jsonify({"error": "no case open"}), 400
    ents, errors, datasets = {}, [], set()
    for eid in ids:
        e, err = _osa_call(f"/entities/{quote(eid)}", query={"nested": "true"})
        if err:
            errors.append(f"{eid}: {err}")
            continue
        _osa_flatten(e, ents)
        datasets.update(e.get("datasets") or [])
    ents = {i: e for i, e in ents.items() if e["schema"] in ftm.schema()}
    if not ents:
        return jsonify({"error": "; ".join(errors) or "no entity received"}), 502
    table = ftm.rows_from_entities(ents, native_types=onto.TYPES, reserved=ftm_reserved)
    header, body = table[0], table[1:]
    totals = {"nodes": 0, "links": 0, "updated": 0, "same_links": 0}
    for i in range(0, len(body), FTM_BATCH):
        plan, _ = plan_import([header] + body[i:i + FTM_BATCH], mapping=_ftm_mapping(header), has_header=True)
        res = commit_plan(plan, update=True, ftm_dataset=",".join(sorted(datasets))[:120] or "opensanctions")
        for k in totals:
            totals[k] += res.get(k, 0)
    _cache["key"] = None
    logging.info(f"OpenSanctions: {len(ents)} entities imported -> {totals['nodes']} nodes, {totals['links']} links")
    return jsonify(dict(totals, ok=True, entities=len(ents), errors=errors))
