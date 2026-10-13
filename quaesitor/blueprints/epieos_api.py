# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Epieos: configuration, search (paid: every search costs credits), import."""
# "Caveat emptor." (legal maxim)
# Let the buyer beware.
from datetime import datetime
import json
import logging
import re

from flask import Blueprint, jsonify, request

from .. import epieos, store
from ..core import (
    _flat, _http_json_full, _load_services_conf, _save_kv_conf, IMPORT_MAX_MB, SERVICES,
    SERVICES_CONF,
)
from ..records import export_query
from ..identifiers import phone_key
from ..labels import _cache
from ..archive import current_graph

bp = Blueprint("epieos_api", __name__)


EP_KEYS = ("enabled", "endpoint", "api_key", "pack", "timeout")


# ============================== EPIEOS (API) ==============================
# Ricerca inversa di email e telefoni su decine di servizi (api.epieos.com).
# A PAGAMENTO: ogni ricerca consuma crediti, quindi non e' mai automatica e
# l'interfaccia chiede conferma ogni volta. Spenta per impostazione predefinita;
# accesa, l'UNICO dato che esce dal computer e' l'identificativo cercato.
# La risposta viene salvata tale e quale nell'archivio del caso (come un
# export JSON) e tradotta in nodi dall'adattatore epieos.py.
EP_STATE = {"credits": None, "credits_at": "", "ratelimit": {}}
EP_EXPLAIN = {
    400: "richiesta non valida",
    401: "chiave API mancante o non valida",
    402: "crediti esauriti",
    403: "pack non disponibile per questa chiave",
    429: "limite di richieste raggiunto: attendere e riprovare",
    500: "errore del servizio Epieos",
}
EP_QUERY_MAX = 200


def ep_ready():
    return bool(SERVICES["epieos_enabled"] and SERVICES["epieos_endpoint"] and SERVICES.get("epieos_api_key"))


def _ep_public():
    k = SERVICES.get("epieos_api_key") or ""
    return {"enabled": bool(SERVICES["epieos_enabled"]), "endpoint": SERVICES["epieos_endpoint"],
            "has_key": bool(k), "key_hint": ("…" + k[-4:]) if len(k) > 8 else ("•" * len(k)),
            "pack": SERVICES["epieos_pack"], "timeout": SERVICES["epieos_timeout"],
            "ready": ep_ready(), "credits": EP_STATE["credits"], "credits_at": EP_STATE["credits_at"],
            "ratelimit": EP_STATE["ratelimit"], "packs": _ep_saved_packs(),
            "modules": {"email": list(epieos.MODULES_EMAIL), "phone": list(epieos.MODULES_PHONE)}}


def _ep_saved_packs():
    try:
        packs = json.loads(store.get_gmeta("epieos_packs") or "[]")
        return packs if isinstance(packs, list) else []
    except (TypeError, ValueError):
        return []


def _ep_note_headers(hdrs):
    """Crediti residui e limiti di frequenza dagli header della risposta."""
    h = {str(k).lower(): v for k, v in (hdrs or {}).items()}
    if "x-remaining-credits" in h:
        try:
            EP_STATE["credits"] = int(float(h["x-remaining-credits"]))
            EP_STATE["credits_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            pass
    rl = {k[10:]: h[k] for k in ("ratelimit-limit", "ratelimit-remaining", "ratelimit-reset") if k in h}
    if rl:
        EP_STATE["ratelimit"] = rl


def _ep_call(path, payload=None):
    if not SERVICES["epieos_enabled"]:
        return None, "Epieos disattivato (pannello Epieos)", 0
    if not SERVICES.get("epieos_api_key"):
        return None, "chiave API Epieos mancante (Configura)", 0
    url = SERVICES["epieos_endpoint"] + path
    headers = {"api-key": SERVICES["epieos_api_key"]}
    data, err, hdrs, code = _http_json_full(url, payload, headers, SERVICES["epieos_timeout"], EP_EXPLAIN)
    _ep_note_headers(hdrs)
    if err and code == 429:
        reset = (EP_STATE["ratelimit"] or {}).get("reset")
        if reset:
            err += f" (reset fra {reset} s)"
    return data, err, code


def _ep_packs_from_schema(spec):
    """Dalla specifica OpenAPI su misura della chiave (GET /schema):
    [{pack, kinds: {email: [moduli], phone: [moduli]}}]."""
    packs = {}
    for path, item in ((spec or {}).get("paths") or {}).items():
        m = re.match(r"^/v1/search/(email|phone)/([a-z0-9_\-]+)$", str(path))
        if not m or not isinstance(item, dict) or "post" not in item:
            continue
        kind, pack = m.group(1), m.group(2)
        mods = []
        try:
            sch = item["post"]["responses"]["200"]["content"]["application/json"]["schema"]
            mods = sorted((sch.get("properties") or {}).get("result", {}).get("properties", {}).keys())
        except (KeyError, TypeError, AttributeError):
            pass
        if not mods:
            try:
                body = item["post"]["requestBody"]["content"]["application/json"]["schema"]
                mods = sorted(body["properties"]["modules"]["items"]["enum"])
            except (KeyError, TypeError):
                pass
        packs.setdefault(pack, {"pack": pack, "kinds": {}})["kinds"][kind] = mods
    return sorted(packs.values(), key=lambda p: p["pack"])


def _ep_kind(query, kind=""):
    q = re.sub(r"\s+", " ", str(query or "")).strip()[:EP_QUERY_MAX]
    kind = str(kind or "").strip().lower()
    if not kind:
        if "@" in q and "." in q.split("@")[-1]:
            kind = "email"
        elif re.fullmatch(r"\+?[0-9][0-9\s().\-]{5,}", q):
            kind = "phone"
    if kind == "email":
        q = q.lower()
    elif kind == "phone":
        q = re.sub(r"[\s().\-]", "", q)
    return q, kind


def _ep_anchor_node(anchor, query, kind):
    """Nodo a cui agganciare la risposta: quello indicato, altrimenti il nodo
    email/telefono dell'identificativo se gia' presente nel grafo."""
    g = current_graph()
    if anchor:
        return next((n for n in g["nodes"] if n["id"] == anchor or anchor in (n.get("alias_ids") or [])), None)
    want = ("email:" + query) if kind == "email" else ("phone:" + phone_key(query))
    return next((n for n in g["nodes"] if n["id"] == want), None)


def _ep_store(node, kind, query, content):
    """Salva la risposta come import sul nodo (sostituendo una ricerca
    precedente dello stesso identificativo sullo stesso nodo)."""
    filename = f"search_{query}.json"[:200]
    for old in store.list_imports(node["id"]):
        if old.get("filename") == filename:
            store.delete_import(old["id"])
    iid = store.add_import(node["id"], _flat(node.get("label")) or node["id"], filename, content, 1, False,
                           node.get("ntype") or "generic", node.get("platform") or "generic")
    _cache["key"] = None
    return iid, filename


@bp.route("/api/epieos/config", methods=["GET", "POST"])
def api_ep_config():
    if request.method == "GET":
        return jsonify(_ep_public())
    data = request.get_json(silent=True) or {}
    up = {}
    for k in EP_KEYS:
        if k not in data:
            continue
        v = data[k]
        if k == "enabled":
            up["epieos_enabled"] = "true" if v in (True, "true", "1", 1, "on") else "false"
            continue
        v = re.sub(r"[\r\n]+", " ", str(v if v is not None else "")).strip()[:500]
        if k == "api_key" and not v and not data.get("clear_key"):
            continue
        if k == "endpoint" and v and not re.match(r"^https?://[^\s]+$", v, re.I):
            return jsonify({"error": "endpoint non valido (serve http:// o https://)"}), 400
        if k == "timeout":
            try:
                v = str(max(10, min(300, int(float(v)))))
            except ValueError:
                return jsonify({"error": "timeout non valido"}), 400
        if k == "pack":
            v = re.sub(r"[^a-z0-9_\-]", "", v.lower()) or "osinter"
        up["epieos_" + k] = v
    try:
        _save_kv_conf(SERVICES_CONF, up, "# services.conf - servizi online facoltativi (OpenSanctions, Epieos). Non pubblicare: contiene le chiavi API.")
    except OSError as e:
        return jsonify({"error": f"impossibile scrivere services.conf: {e}"}), 500
    SERVICES.clear()
    SERVICES.update(_load_services_conf())
    logging.info(f"Configurazione Epieos aggiornata: {sorted(up)}")
    return jsonify(_ep_public())


@bp.route("/api/epieos/schema", methods=["POST"])
def api_ep_schema():
    """Legge la specifica su misura della chiave (GET /schema): pack e moduli
    disponibili. Non consuma crediti. Salvata nei metadati globali."""
    spec, err, code = _ep_call("/schema")
    if err:
        return jsonify({"ok": False, "error": err}), 502
    packs = _ep_packs_from_schema(spec)
    store.set_gmeta("epieos_packs", json.dumps(packs))
    logging.info(f"Epieos: schema letto, pack disponibili: {[p['pack'] for p in packs]}")
    return jsonify({"ok": True, "packs": packs, "credits": EP_STATE["credits"], "ratelimit": EP_STATE["ratelimit"]})


@bp.route("/api/epieos/search", methods=["POST"])
def api_ep_search():
    """{query, kind?, anchor?, pack?, modules?: [...], excluded_modules?: [...]}
    -> ricerca a pagamento (una chiamata), risposta salvata sul nodo e grafo
    ricostruito. 'anchor' e' il nodo email/telefono (o il target) a cui
    agganciare i risultati: se manca si usa il nodo dell'identificativo, che
    deve gia' esistere (l'interfaccia lo crea prima di chiedere conferma)."""
    data = request.get_json(silent=True) or {}
    if not store.current_case():
        return jsonify({"error": "nessun caso aperto"}), 400
    query, kind = _ep_kind(data.get("query"), data.get("kind"))
    if kind not in ("email", "phone") or not query:
        return jsonify({"error": "indica una email o un numero di telefono"}), 400
    pack = re.sub(r"[^a-z0-9_\-]", "", str(data.get("pack") or SERVICES["epieos_pack"]).lower()) or "osinter"
    node = _ep_anchor_node(str(data.get("anchor") or "").strip(), query, kind)
    if node is None:
        return jsonify({"error": "nodo non trovato: crea prima il nodo dell'identificativo"}), 404
    body = {"query": query}
    for key in ("modules", "excluded_modules"):
        mods = [re.sub(r"[^a-z0-9_]", "", str(m).lower()) for m in (data.get(key) or [])]
        mods = [m for m in mods if m]
        if mods:
            body[key] = mods
    res, err, code = _ep_call(f"/v1/search/{kind}/{pack}", body)
    if err:
        return jsonify({"error": err, "code": code, "credits": EP_STATE["credits"]}), 502
    result = res.get("result") if isinstance(res, dict) else None
    if not isinstance(result, dict):
        return jsonify({"error": "risposta Epieos non riconosciuta"}), 502
    wrapper = epieos.wrap(result, kind, query, pack, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), EP_STATE["credits"])
    content = json.dumps(wrapper, ensure_ascii=False)
    iid, filename = _ep_store(node, kind, query, content)
    summ = epieos.summary(wrapper)
    logging.info(f"Epieos: {kind} {query} ({pack}) -> {len(summ['modules'])} moduli, {summ['records']} record, "
                 f"crediti residui {EP_STATE['credits']}")
    return jsonify({"ok": True, "id": iid, "filename": filename, "anchor": node["id"], "kind": kind, "query": query,
                    "modules": summ["modules"], "records": summ["records"], "credits": EP_STATE["credits"]})


@bp.route("/api/epieos/import", methods=["POST"])
def api_ep_import():
    """{anchor?, content, filename?}: una risposta Epieos salvata su file
    (nuda {"result": ...} o con involucro) registrata come una ricerca.
    Non chiama il servizio e non consuma crediti."""
    data = request.get_json(silent=True) or {}
    if not store.current_case():
        return jsonify({"error": "nessun caso aperto"}), 400
    content = str(data.get("content") or "")
    if len(content.encode("utf-8")) > IMPORT_MAX_MB * 1024 * 1024:
        return jsonify({"error": f"file troppo grande (max {IMPORT_MAX_MB} MB)"}), 400
    obj = epieos.loads(content)
    if not epieos.is_epieos(obj):
        return jsonify({"error": "il file non e' una risposta Epieos"}), 400
    meta, result = epieos.unwrap(obj)
    query, kind = _ep_kind(data.get("query") or meta.get("query"), data.get("kind") or meta.get("kind"))
    if not query or kind not in ("email", "phone"):
        # risposta senza 'query' nei moduli: la si ricava dal nome del file
        query, kind = _ep_kind(export_query(str(data.get("filename") or "")))
    if not query or kind not in ("email", "phone"):
        return jsonify({"error": "identificativo cercato non riconoscibile: indicalo (query)"}), 400
    node = _ep_anchor_node(str(data.get("anchor") or "").strip(), query, kind)
    if node is None:
        return jsonify({"error": "nodo non trovato: crea prima il nodo dell'identificativo", "query": query,
                        "kind": kind}), 404
    wrapper = epieos.wrap(result, kind, query, meta.get("pack") or SERVICES["epieos_pack"],
                          meta.get("fetched_at") or "", meta.get("credits_left"))
    iid, filename = _ep_store(node, kind, query, json.dumps(wrapper, ensure_ascii=False))
    summ = epieos.summary(wrapper)
    logging.info(f"Epieos: importato da file {kind} {query} -> {len(summ['modules'])} moduli, {summ['records']} record")
    return jsonify({"ok": True, "id": iid, "filename": filename, "anchor": node["id"], "kind": kind, "query": query,
                    "modules": summ["modules"], "records": summ["records"]})


@bp.route("/api/epieos/searches")
def api_ep_searches():
    """Ricerche Epieos salvate nel caso: {anchor: [{id, filename, query, kind, fetched_at, modules}]}."""
    out = {}
    for imp in store.iter_imports():
        if not str(imp.get("filename") or "").startswith("search_"):
            continue
        obj = epieos.loads(imp.get("content") or "")
        if not isinstance(obj, dict) or not isinstance(obj.get("epieos"), dict):
            continue
        w = obj["epieos"]
        out.setdefault(imp["anchor"], []).append({"id": imp["id"], "filename": imp["filename"], "query": w.get("query"),
                                                  "kind": w.get("kind"), "pack": w.get("pack"),
                                                  "fetched_at": w.get("fetched_at"),
                                                  "modules": sorted(k for k, v in (w.get("result") or {}).items() if v)})
    return jsonify(out)
