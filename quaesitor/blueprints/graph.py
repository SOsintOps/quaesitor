# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""The graph: nodes, links, notes, hand-made labels, deleted nodes, saved views, uploads."""
# "Natura non facit saltus." (after Linnaeus, Philosophia Botanica)
# Nature makes no leaps.
from datetime import datetime
from urllib.parse import quote
import logging
import os
import re
import uuid

from flask import Blueprint, jsonify, request

from .. import ontology as onto
from .. import store
from ..core import _flat, _hash, DATA_DIR, MEDIA_DIRNAME, NodeError
from ..transliteration import translit_mode
from ..labels import _cache
from ..dictionary import _translit_new_labels, new_added_entry, resolve_node, same_place_id
from ..archive import (
    _store_props, BEND_CURVES, current_graph, deleted_ids, edge_props, load_annotations,
    manual_edge, manual_node, save_annotations,
)

bp = Blueprint("graph", __name__)


@bp.route("/api/graph")
def api_graph():
    try:
        g = dict(current_graph())
        g["translit_mode"] = translit_mode()
        return jsonify(g)
    except Exception as e:
        logging.error("Errore in /api/graph", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/reload", methods=["POST"])
def api_reload():
    """Rereads the data from disk and rebuilds the graph, without restarting the app.
    Needed after adding cards or target folders: a new but empty folder does not
    change the file signature, so the cache has to be invalidated by hand."""
    try:
        _cache["key"] = None
        g = dict(current_graph())
        g["translit_mode"] = translit_mode()
        logging.info(f"Dati ricaricati: {len(g['nodes'])} nodi, {len(g['edges'])} archi")
        return jsonify(g)
    except Exception as e:
        logging.error("Errore in /api/reload", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/note", methods=["POST"])
def api_note():
    """Saves (or removes, if the text is empty) the note of a node."""
    data = request.get_json(silent=True) or {}
    nid = str(data.get("id") or "").strip()
    text = str(data.get("note") or "").strip()
    if not nid:
        return jsonify({"error": "id mancante"}), 400
    ann = load_annotations()
    if text:
        ann["notes"][nid] = text[:4000]
    else:
        ann["notes"].pop(nid, None)
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    return jsonify({"ok": True, "id": nid, "note": text})


@bp.route("/api/node/label", methods=["POST"])
def api_node_label():
    """Changes the label of a card ({'id': ..., 'label': ...}).
    With an empty label it goes back to the one from the source data.
    The source files are NOT touched: the edit lives in annotations.json.
    If after the edit another card represents the same identifier
    (e.g. the same number written with 00 and with +) the two become one:
    the response says which id the card ended up on."""
    data = request.get_json(silent=True) or {}
    nid = str(data.get("id") or "").strip()
    label = re.sub(r"\s+", " ", str(data.get("label") or "")).strip()[:300]
    if not nid:
        return jsonify({"error": "id mancante"}), 400

    ann = load_annotations()
    labels = ann.setdefault("labels", {})
    g = current_graph()
    prima = next((n for n in g["nodes"] if n["id"] == nid), None)
    if prima is None:
        # id already merged into another card: if it has no edited label of its
        # own, work directly on the card that absorbed it
        prima = next((n for n in g["nodes"] if nid in (n.get("alias_ids") or [])), None)
        if prima is not None and nid not in labels:
            nid = prima["id"]
    if prima is None:
        return jsonify({"error": "nodo non trovato"}), 404

    if label and label != _flat(prima.get("label")):
        labels[nid] = {"label": label,
                       "orig": _flat(prima.get("label_orig") or prima.get("label")),
                       "ntype": prima.get("ntype") or "",
                       "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    elif not label:
        # back to the labels from the data: also remove those of the ids that
        # the rename had merged into this card, otherwise the merge would stay
        # in place with no reason any more
        for k in [nid] + list(prima.get("alias_ids") or []):
            labels.pop(k, None)
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    if label:
        _translit_new_labels([label])

    dopo = current_graph()
    node = next((n for n in dopo["nodes"] if n["id"] == nid), None)
    if node is None:                               # the card was merged into another one
        node = next((n for n in dopo["nodes"] if nid in (n.get("alias_ids") or [])), None)
    if node is None:
        return jsonify({"error": "nodo non trovato dopo la modifica"}), 404
    fusa = node["id"] != nid
    logging.info(f"Etichetta modificata: {nid} -> '{label}'"
                 + (f" (fusa in {node['id']})" if fusa else ""))
    return jsonify({"ok": True, "id": node["id"], "asked": nid,
                    "label": node.get("label"), "merged": fusa,
                    "reset": not label})


@bp.route("/api/node/delete", methods=["POST"])
def api_node_delete():
    """Hides a node for good (the source data stay intact).
    Also keeps the info useful to recognise it in the list of deleted nodes."""
    data = request.get_json(silent=True) or {}
    nid = str(data.get("id") or "").strip()
    if not nid:
        return jsonify({"error": "id mancante"}), 400
    ann = load_annotations()
    # All the ids merged into the node (cards of a place, merged aliases): they
    # are taken from the graph, not from the client. Without this, deleting a place
    # with two cards would remove only one of them and the node would reappear.
    g = current_graph()
    node = next((n for n in g["nodes"] if n["id"] == nid or
                 nid in (n.get("alias_ids") or [])), None)
    group = {nid}
    if node:
        group |= {node["id"]} | set(node.get("alias_ids") or [])
    manual = {str(x.get("id")) for x in ann["added"]} & group
    # a node created by hand is not "hidden": it is really deleted from the file,
    # together with links, notes, labels and edits
    if manual:
        ann["added"] = [x for x in ann["added"] if str(x.get("id")) not in manual]
        ann["links"] = [x for x in ann["links"]
                        if not ({str(x.get("a")), str(x.get("b"))} & group)]
        for k in group:
            ann["notes"].pop(k, None)
            ann["labels"].pop(k, None)
            ann["edits"].pop(k, None)
            ann.get("targets", {}).pop(k, None)
        data_ids = group - manual
        # the node left after a merge is manual only if all the entries are
        # (a data node would take precedence): then it is gone
        if node is None or node.get("manual") or not data_ids:
            if not save_annotations(ann):
                return jsonify({"error": "salvataggio fallito"}), 500
            # the imported JSON attached to the node (the target) go with it
            n_imp = store.delete_imports_of(group)
            logging.info(f"Nodo manuale eliminato: {nid} ({len(manual)} voci, "
                         f"{n_imp} JSON importati)")
            return jsonify({"ok": True, "id": nid, "manual": True, "removed": len(manual),
                            "imports": n_imp})
        # data node with cards added by hand: the cards are deleted, the data
        # node is hidden (the export files are not touched)
        data["alias_ids"] = list(data_ids - {node["id"]})
        nid = node["id"]

    have = deleted_ids(ann)
    entry = {
        "id": nid,
        "label": str(data.get("label") or nid)[:300],
        "ntype": str(data.get("ntype") or "")[:40],
        "platform": str(data.get("platform") or "")[:60],
        "targets": [str(t)[:200] for t in (data.get("targets") or [])][:20],
        "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if nid not in have:
        ann["deleted"].append(entry)
    for a in (data.get("alias_ids") or []):          # also the ids merged into the node
        a = str(a)
        if a and a not in have and a != nid:
            ann["deleted"].append(dict(entry, id=a, label=f"{entry['label']} (alias)"))
    ann["notes"].pop(nid, None)
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    logging.info(f"Nodo cancellato dall'utente: {nid}")
    return jsonify({"ok": True, "id": nid, "deleted": len(ann["deleted"])})


@bp.route("/api/node/add", methods=["POST"])
def api_node_add():
    """Adds a node by hand. With 'parent' it links it to the node of the card
    (with name, arrows and style of the link); without 'parent' it creates an
    independent node ("Nuovo nodo"). The ids follow the same rules as the graph,
    so a value already present does NOT create a duplicate: it is only linked."""
    data = request.get_json(silent=True) or {}
    parent = str(data.get("parent") or "").strip()
    try:
        nid, label, platform, ntype, value = resolve_node(data, parent)
    except NodeError as e:
        return jsonify({"error": str(e)}), 400

    ann = load_annotations()
    # link properties: 'edge' object (new) or loose keys (old)
    esrc = data.get("edge") if isinstance(data.get("edge"), dict) else \
        {"label": data.get("edge_label") or data.get("rel_label"),
         "arrow": data.get("arrow"), "curve": data.get("curve")}
    props = edge_props(esrc)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    g = current_graph()
    edge_id = f"e_{_hash(parent)[:8]}_{_hash(nid)[:8]}_{uuid.uuid4().hex[:8]}"
    if ntype in ("place", "name", "vehicle") or ntype in onto.TYPES:
        # Place, person or vehicle (same plate) already present (even written differently: "Via G.
        # Leopardi 1" / "giacomo leopardi 1"; "Rossi Mario" / "Mario Rossi"):
        # no new node, but a new CARD inside the existing one. An entry is saved
        # with its own id ('<id>~xxxxxx') which apply_annotations and merge_places
        # merge into the existing node.
        same = (same_place_id(g, value, data) if ntype == "place" else None) or \
            next((n["id"] for n in g["nodes"]
                  if n["id"] == nid or nid in (n.get("alias_ids") or [])), None)
        if same:
            rid = f"{same}~{uuid.uuid4().hex[:6]}"   # card of the node 'same'
            entry = new_added_entry(rid, label, platform, ntype, value, data, parent, now)
            edge = None
            if parent:
                entry["edge_id"] = edge_id
                _store_props(entry, props, "edge_")
                edge = manual_edge(parent, same, "manuale", edge_id=edge_id, props=props)
            ann["added"].append(entry)
            if not save_annotations(ann):
                return jsonify({"error": "salvataggio fallito"}), 500
            logging.info(f"Nuova scheda nel nodo {same} (voce {rid})")
            node = next((n for n in current_graph()["nodes"] if n["id"] == same), None)
            return jsonify({"ok": True, "id": same, "label": (node or {}).get("label"),
                            "platform": platform, "script": "", "node": node,
                            "edge": edge, "record": True})

    existing_entry = next((x for x in ann["added"] if str(x.get("id")) == nid), None)
    existing_node = next((n for n in g["nodes"] if n["id"] == nid), None)
    edge = None
    if existing_entry is not None or existing_node is not None:
        if not parent:
            # independent node already present: no duplicate, that one is returned
            node = existing_node or manual_node(existing_entry)
            return jsonify({"ok": True, "id": nid, "label": node.get("label"),
                            "platform": node.get("platform"), "script": "",
                            "node": node, "edge": None, "existed": True})
        # The node already exists (added by hand or present in the data): a further
        # link is created, with its own name, arrows and style. Between two nodes
        # there can thus be several different links.
        link_entry = {"id": edge_id, "a": parent, "b": nid, "at": now}
        _store_props(link_entry, props)
        ann["links"].append(link_entry)
        entry = existing_entry or {"id": nid, "label": label}
        edge = manual_edge(parent, nid, "collegamento", edge_id=edge_id, props=props)
        logging.info(f"Collegamento manuale aggiuntivo creato: {parent} -> {nid} (arco: {edge_id})")
    else:
        ann["deleted"] = [x for x in ann["deleted"] if str(x.get("id")) != nid]
        entry = new_added_entry(nid, label, platform, ntype, value, data, parent, now)
        if parent:
            entry["edge_id"] = edge_id
            _store_props(entry, props, "edge_")
            edge = manual_edge(parent, nid, "manuale", edge_id=edge_id, props=props)
        ann["added"].append(entry)
        logging.info(f"Nodo aggiunto a mano: {nid}" + (f" -> {parent}" if parent else " (indipendente)"))

    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500

    scr = _translit_new_labels([entry["label"]])
    # the client inserts the node into the graph without reloading the page; if there
    # is a transliteration (non-Latin script) it syncs to show the Latin node
    return jsonify({"ok": True, "id": nid, "label": entry["label"],
                    "platform": platform, "script": scr,
                    "node": existing_node or manual_node(entry), "edge": edge})


# signatures of the accepted image formats, so as not to trust the extension
_IMG_MAGIC = [
    (b"\xff\xd8\xff", ".jpg"), (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"GIF87a", ".gif"), (b"GIF89a", ".gif"), (b"BM", ".bmp"),
]
MAX_IMAGE_BYTES = 12 * 1024 * 1024


def _sniff_image(blob):
    for magic, ext in _IMG_MAGIC:
        if blob.startswith(magic):
            return ext
    if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return ".webp"
    return None


@bp.route("/api/upload", methods=["POST"])
def api_upload():
    """Receives an image (base64 data URL) and saves it in data/media/.
    Returns the relative path to use as the value of the photo node."""
    import base64
    data = request.get_json(silent=True) or {}
    raw = str(data.get("data") or "")
    m = re.match(r"^data:image/[\w.+-]+;base64,(.+)$", raw, re.S)
    if not m:
        return jsonify({"error": "immagine mancante o formato non riconosciuto"}), 400
    try:
        blob = base64.b64decode(m.group(1), validate=True)
    except Exception:
        return jsonify({"error": "immagine illeggibile"}), 400
    if len(blob) > MAX_IMAGE_BYTES:
        return jsonify({"error": f"immagine troppo grande (max {MAX_IMAGE_BYTES // (1024*1024)} MB)"}), 400
    ext = _sniff_image(blob)
    if not ext:
        return jsonify({"error": "il file non è un'immagine valida"}), 400

    mdir = os.path.join(DATA_DIR, MEDIA_DIRNAME)
    os.makedirs(mdir, exist_ok=True)
    base = re.sub(r"[^A-Za-z0-9._-]+", "_",
                  os.path.splitext(str(data.get("filename") or "img"))[0])[:50] or "img"
    fname = f"{base}_{datetime.now():%Y%m%d-%H%M%S}_{os.urandom(3).hex()}{ext}"
    try:
        with open(os.path.join(mdir, fname), "wb") as f:
            f.write(blob)
    except Exception as e:
        logging.error(f"Salvataggio immagine fallito: {e}")
        return jsonify({"error": "salvataggio dell'immagine fallito"}), 500

    rel = f"{MEDIA_DIRNAME}/{fname}"
    logging.info(f"Immagine salvata: {rel} ({len(blob)} byte)")
    return jsonify({"ok": True, "path": rel, "url": "/media/" + quote(rel),
                    "size": len(blob)})


@bp.route("/api/link/add", methods=["POST"])
def api_link_add():
    """Links nodes, with support for arrows, labels, line shape and multiple links."""
    data = request.get_json(silent=True) or {}
    ids = [str(x) for x in (data.get("ids") or []) if str(x).strip()]
    ids = list(dict.fromkeys(ids))                       # without duplicates, stable order
    if len(ids) < 2:
        return jsonify({"error": "servono almeno due nodi"}), 400
    if len(ids) > 60:
        return jsonify({"error": "troppi nodi selezionati (max 60)"}), 400

    props = edge_props(data)

    req_source = str(data.get("source") or "").strip()
    req_target = str(data.get("target") or "").strip()

    ann = load_annotations()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    created, edges = 0, []

    if len(ids) == 2 and req_source and req_target and {req_source, req_target} == set(ids):
        pairs = [(req_source, req_target)]          # direction chosen by the user
    else:
        pairs = [(ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids))]
    for a, b in pairs:
        eid = f"e_{_hash(a)[:8]}_{_hash(b)[:8]}_{uuid.uuid4().hex[:8]}"
        link_entry = {"id": eid, "a": a, "b": b, "at": now}
        _store_props(link_entry, props)
        ann["links"].append(link_entry)
        edges.append(manual_edge(a, b, "collegamento", edge_id=eid, props=props))
        created += 1

    if created and not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    logging.info(f"Collegamenti manuali creati: {created} su {len(ids)} nodi")
    return jsonify({"ok": True, "created": created,
                    "coppie": len(ids) * (len(ids) - 1) // 2, "edges": edges})


@bp.route("/api/link/delete", methods=["POST"])
def api_link_delete():
    """Deletes a manual link (by edge id or by pair of nodes)."""
    data = request.get_json(silent=True) or {}
    eid = str(data.get("id") or data.get("edge_id") or "").strip()
    a, b = str(data.get("a") or "").strip(), str(data.get("b") or "").strip()
    if not eid and (not a or not b):
        return jsonify({"error": "identificativo o coppia di nodi mancante"}), 400

    ann = load_annotations()
    before = len(ann["links"])
    deleted_edge_id = eid

    if eid:
        ann["links"] = [x for x in ann["links"]
                        if str(x.get("id") or x.get("edge_id") or "") != eid]
    if len(ann["links"]) == before and a and b:
        ann["links"] = [x for x in ann["links"]
                        if {str(x.get("a")), str(x.get("b"))} != {a, b}]
        deleted_edge_id = deleted_edge_id or manual_edge(a, b)["id"]

    if len(ann["links"]) == before:
        return jsonify({"error": "collegamento non trovato"}), 404
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    return jsonify({"ok": True, "edge_id": deleted_edge_id})


@bp.route("/api/link/update", methods=["POST"])
def api_link_update():
    """Edits an existing link: name, arrows, shape, colour, type and
    width of the line. Applies to ALL links:
    - created by hand (between existing nodes or together with an added node): their
      entry in annotations.json is updated;
    - coming from the data: the style is saved separately ('edge_styles'), the
      source files are not touched. With 'reset' it goes back to the default style."""
    data = request.get_json(silent=True) or {}
    eid = str(data.get("id") or "").strip()
    if not eid:
        return jsonify({"error": "id del collegamento mancante"}), 400
    ann = load_annotations()
    props = edge_props(data)
    reset = bool(data.get("reset"))

    link = next((x for x in ann["links"]
                 if str(x.get("id") or x.get("edge_id") or "") == eid), None)
    added = None if link else next(
        (x for x in ann["added"] if str(x.get("edge_id") or "") == eid), None)
    kind = "link" if link else "added" if added else "data"
    if reset:
        props = edge_props({})
    if link is not None:
        _store_props(link, props)
        if data.get("swap"):                           # reverses the direction
            link["a"], link["b"] = link["b"], link["a"]
    elif added is not None:
        _store_props(added, props, "edge_")
    else:
        g = current_graph()
        if not any(e["id"] == eid for e in g["edges"]):
            return jsonify({"error": "collegamento non trovato"}), 404
        styles = ann.setdefault("edge_styles", {})
        if reset:
            styles.pop(eid, None)
        else:
            styles[eid] = {k: v for k, v in props.items()
                           if v or (k == "bend" and props["curve"] in BEND_CURVES)}
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    logging.info(f"Collegamento modificato ({kind}): {eid}")
    return jsonify({"ok": True, "id": eid, "kind": kind, "props": props})


@bp.route("/api/node/edit", methods=["POST"])
def api_node_edit():
    """Edits the values of a node: the fields of the cards, the fields added by
    hand and the URL. The source files stay intact: the edits live in
    annotations.json ('edits') and are applied when the graph is built.
    For nodes created by hand their entry is updated too."""
    data = request.get_json(silent=True) or {}
    nid = str(data.get("id") or "").strip()
    if not nid:
        return jsonify({"error": "id mancante"}), 400
    ann = load_annotations()
    edits = ann.setdefault("edits", {})
    if data.get("reset"):
        edits.pop(nid, None)
    else:
        ed = edits.setdefault(nid, {})
        fields = ed.setdefault("fields", {})
        for k, v in (data.get("fields") or {}).items():
            ri, _, path = str(k).partition("|")
            if not ri.isdigit() or not path:
                continue
            fields[str(k)[:500]] = None if v is None else str(v)[:20000]
        if isinstance(data.get("extra"), dict):
            ed["extra"] = {str(k).strip()[:120]: str(v)[:20000]
                           for k, v in data["extra"].items()
                           if str(k).strip() and str(v).strip()}
        if "url" in data:
            url = str(data.get("url") or "").strip()[:1000]
            if url and not re.match(r"^https?://", url, re.I):
                return jsonify({"error": "URL non valido (serve http:// o https://)"}), 400
            ed["url"] = url
        if not fields:
            ed.pop("fields", None)
        if not ed.get("extra"):
            ed.pop("extra", None)
        if not ed:
            edits.pop(nid, None)
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    logging.info(f"Valori del nodo modificati: {nid}")
    return jsonify({"ok": True, "id": nid})


@bp.route("/api/node/target", methods=["POST"])
def api_node_target():
    """Makes any node a target (or removes the highlight). For nodes created
    by hand their entry is updated; for those from the data the choice lives
    in the annotations ('targets') and is applied when building the graph."""
    data = request.get_json(silent=True) or {}
    nid = str(data.get("id") or "").strip()
    if not nid:
        return jsonify({"error": "id mancante"}), 400
    want = bool(data.get("target"))
    ann = load_annotations()
    targets = ann.setdefault("targets", {})
    added = next((x for x in ann["added"] if str(x.get("id")) == nid), None)
    if added is not None:
        added["target"] = want
        targets.pop(nid, None)
    else:
        targets[nid] = want
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    logging.info(f"Nodo {nid}: target = {want}")
    return jsonify({"ok": True, "id": nid, "target": want})


@bp.route("/api/manual")
def api_manual():
    """List of the manual edits: added nodes and created links."""
    ann = load_annotations()
    added = sorted(ann["added"], key=lambda x: x.get("at") or "", reverse=True)
    links = sorted(ann["links"], key=lambda x: x.get("at") or "", reverse=True)
    for l in links:
        l["edge_id"] = l.get("id") or l.get("edge_id") or manual_edge(str(l["a"]), str(l["b"]))["id"]
        l["id"] = l["edge_id"]
        l["label"] = str(l.get("label") or "")
        l["arrow"] = str(l.get("arrow") or "none")
        l["curve"] = str(l.get("curve") or "bezier")
    labels = [{"id": k, "label": v["label"], "orig": v.get("orig") or "",
               "ntype": v.get("ntype") or "", "at": v.get("at") or ""}
              for k, v in (ann.get("labels") or {}).items()]
    labels.sort(key=lambda x: x.get("at") or "", reverse=True)
    return jsonify({"added": added, "links": links, "labels": labels,
                    "count": len(added) + len(links) + len(labels)})


@bp.route("/api/node/remove_manual", methods=["POST"])
def api_node_remove_manual():
    """Really deletes a node added by hand (and its links)."""
    data = request.get_json(silent=True) or {}
    nid = str(data.get("id") or "").strip()
    if not nid:
        return jsonify({"error": "id mancante"}), 400
    ann = load_annotations()
    before = len(ann["added"])
    ann["added"] = [x for x in ann["added"] if str(x.get("id")) != nid]
    if len(ann["added"]) == before:
        return jsonify({"error": "nodo manuale non trovato"}), 404
    ann["links"] = [x for x in ann["links"]
                    if nid not in (str(x.get("a")), str(x.get("b")))]
    ann["notes"].pop(nid, None)
    ann.get("labels", {}).pop(nid, None)
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    logging.info(f"Nodo manuale rimosso: {nid}")
    return jsonify({"ok": True, "id": nid})


@bp.route("/api/deleted")
def api_deleted():
    """List of the deleted nodes, most recent first."""
    ann = load_annotations()
    items = sorted(ann["deleted"], key=lambda x: x.get("at") or "", reverse=True)
    return jsonify({"items": items, "count": len(items)})


@bp.route("/api/node/restore", methods=["POST"])
def api_node_restore():
    """Restores a node ({'id': ...}) or all of them ({'all': true}).
    Returns the nodes and edges available again, so the client can
    reinsert them into the graph without reloading the page."""
    data = request.get_json(silent=True) or {}
    ann = load_annotations()
    before = deleted_ids(ann)
    if data.get("all"):
        ann["deleted"] = []
    else:
        nid = str(data.get("id") or "").strip()
        if not nid:
            return jsonify({"error": "id mancante"}), 400
        ann["deleted"] = [x for x in ann["deleted"] if str(x.get("id")) != nid]
    after = deleted_ids(ann)
    back = before - after                       # ids actually restored
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500

    nodes, edges = [], []
    if back:
        g = current_graph()
        nodes = [n for n in g["nodes"] if n["id"] in back]
        edges = [e for e in g["edges"]
                 if e["source"] in back or e["target"] in back]
    return jsonify({"ok": True, "restored": len(back), "remaining": len(after),
                    "nodes": nodes, "edges": edges})


@bp.route("/api/views")
def api_views_list():
    """List of the saved views (without the heavy payload), most recent first."""
    if not store.current_case():
        return jsonify({"items": [], "count": 0})
    views = sorted(store.load_views(), key=lambda x: x.get("at") or "", reverse=True)
    out = [{"id": v["id"], "name": v.get("name") or v["id"],
            "at": v.get("at") or "", "count": v.get("count") or 0} for v in views]
    return jsonify({"items": out, "count": len(out)})


@bp.route("/api/views/save", methods=["POST"])
def api_views_save():
    """Saves (or overwrites by name) a view. Body: {name, view:{...}}."""
    data = request.get_json(silent=True) or {}
    name = re.sub(r"\s+", " ", str(data.get("name") or "").strip())[:80]
    view = data.get("view")
    if not name:
        return jsonify({"error": "nome mancante"}), 400
    if not isinstance(view, dict):
        return jsonify({"error": "vista non valida"}), 400
    views = store.load_views()
    at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = len(view.get("nodes") or [])
    # overwrites if a view with the same name already exists (case-insensitive comparison)
    existing = next((v for v in views if (v.get("name") or "").casefold() == name.casefold()), None)
    vid = existing["id"] if existing else "view_" + datetime.now().strftime("%Y%m%d%H%M%S%f")
    try:
        store.save_view({"id": vid, "name": name, "at": at, "count": count, "view": view})
    except Exception as e:
        logging.error(f"Salvataggio vista fallito: {e}")
        return jsonify({"error": "salvataggio fallito"}), 500
    logging.info(f"Vista salvata: {name} ({count} nodi)")
    return jsonify({"ok": True, "id": vid, "name": name, "at": at,
                    "count": count, "overwritten": bool(existing)})


@bp.route("/api/views/load", methods=["POST"])
def api_views_load():
    """Returns the full payload of a view ({'id': ...})."""
    data = request.get_json(silent=True) or {}
    vid = str(data.get("id") or "").strip()
    v = store.get_view(vid)
    if not v:
        return jsonify({"error": "vista non trovata"}), 404
    return jsonify({"ok": True, "id": v["id"], "name": v.get("name") or v["id"],
                    "view": v.get("view") or {}})


@bp.route("/api/views/delete", methods=["POST"])
def api_views_delete():
    """Deletes a saved view ({'id': ...})."""
    data = request.get_json(silent=True) or {}
    vid = str(data.get("id") or "").strip()
    if not store.delete_view(vid):
        return jsonify({"error": "vista non trovata"}), 404
    logging.info(f"Vista eliminata: {vid}")
    return jsonify({"ok": True, "id": vid})
