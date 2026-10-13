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
    """Rilegge i dati da disco e ricostruisce il grafo, senza riavviare l'app.
    Serve dopo aver aggiunto schede o cartelle target: una cartella nuova ma
    vuota non cambia la firma dei file, quindi la cache va invalidata a mano."""
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
    """Salva (o rimuove, se testo vuoto) la nota di un nodo."""
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
    """Cambia l'etichetta di una scheda ({'id': ..., 'label': ...}).
    Con etichetta vuota si torna a quella dei dati di origine.
    I file di origine NON vengono toccati: la modifica sta in annotations.json.
    Se dopo la modifica un'altra scheda rappresenta lo stesso identificativo
    (es. lo stesso numero scritto con 00 e con +) le due diventano una sola:
    la risposta dice su quale id e' finita la scheda."""
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
        # id gia' confluito in un'altra scheda: se non ha una sua etichetta
        # modificata si lavora direttamente sulla scheda che lo ha assorbito
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
        # si torna alle etichette dei dati: si tolgono anche quelle degli id
        # che la rinomina aveva fatto confluire in questa scheda, altrimenti
        # la fusione resterebbe in piedi senza piu' motivo
        for k in [nid] + list(prima.get("alias_ids") or []):
            labels.pop(k, None)
    if not save_annotations(ann):
        return jsonify({"error": "salvataggio fallito"}), 500
    if label:
        _translit_new_labels([label])

    dopo = current_graph()
    node = next((n for n in dopo["nodes"] if n["id"] == nid), None)
    if node is None:                               # la scheda e' confluita in un'altra
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
    """Nasconde definitivamente un nodo (i dati di origine restano intatti).
    Conserva anche le info utili a riconoscerlo nell'elenco dei cancellati."""
    data = request.get_json(silent=True) or {}
    nid = str(data.get("id") or "").strip()
    if not nid:
        return jsonify({"error": "id mancante"}), 400
    ann = load_annotations()
    # Tutti gli id confluiti nel nodo (schede di un luogo, alias fusi): si
    # ricavano dal grafo, non dal client. Senza questo, cancellando un luogo
    # con due schede ne sparirebbe una sola e il nodo ricomparirebbe.
    g = current_graph()
    node = next((n for n in g["nodes"] if n["id"] == nid or
                 nid in (n.get("alias_ids") or [])), None)
    group = {nid}
    if node:
        group |= {node["id"]} | set(node.get("alias_ids") or [])
    manual = {str(x.get("id")) for x in ann["added"]} & group
    # un nodo creato a mano non si "nasconde": si elimina davvero dal file,
    # insieme a collegamenti, note, etichette e modifiche
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
        # il nodo che resta dopo una fusione e' manuale solo se lo sono tutte
        # le voci (un nodo dei dati avrebbe la precedenza): allora e' finita
        if node is None or node.get("manual") or not data_ids:
            if not save_annotations(ann):
                return jsonify({"error": "salvataggio fallito"}), 500
            # i JSON importati agganciati al nodo (il target) spariscono con lui
            n_imp = store.delete_imports_of(group)
            logging.info(f"Nodo manuale eliminato: {nid} ({len(manual)} voci, "
                         f"{n_imp} JSON importati)")
            return jsonify({"ok": True, "id": nid, "manual": True, "removed": len(manual),
                            "imports": n_imp})
        # nodo dei dati con schede aggiunte a mano: le schede si eliminano,
        # il nodo dei dati si nasconde (i file di export non si toccano)
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
    for a in (data.get("alias_ids") or []):          # anche gli id fusi nel nodo
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
    """Aggiunge a mano un nodo. Con 'parent' lo collega al nodo della scheda
    (con nome, frecce e stile del collegamento); senza 'parent' crea un nodo
    indipendente ("Nuovo nodo"). Gli id seguono le stesse regole del grafo,
    così un valore già presente NON crea un doppione: viene solo collegato."""
    data = request.get_json(silent=True) or {}
    parent = str(data.get("parent") or "").strip()
    try:
        nid, label, platform, ntype, value = resolve_node(data, parent)
    except NodeError as e:
        return jsonify({"error": str(e)}), 400

    ann = load_annotations()
    # proprieta' del collegamento: oggetto 'edge' (nuovo) o chiavi sciolte (vecchio)
    esrc = data.get("edge") if isinstance(data.get("edge"), dict) else \
        {"label": data.get("edge_label") or data.get("rel_label"),
         "arrow": data.get("arrow"), "curve": data.get("curve")}
    props = edge_props(esrc)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    g = current_graph()
    edge_id = f"e_{_hash(parent)[:8]}_{_hash(nid)[:8]}_{uuid.uuid4().hex[:8]}"
    if ntype in ("place", "name", "vehicle") or ntype in onto.TYPES:
        # Luogo, persona o veicolo (stessa targa) gia' presente (anche scritto diversamente: "Via G.
        # Leopardi 1" / "giacomo leopardi 1"; "Rossi Mario" / "Mario Rossi"):
        # niente nodo nuovo, ma una SCHEDA nuova dentro quello esistente. Si
        # salva una voce con id proprio ('<id>~xxxxxx') che apply_annotations
        # e merge_places fondono nel nodo esistente.
        same = (same_place_id(g, value, data) if ntype == "place" else None) or \
            next((n["id"] for n in g["nodes"]
                  if n["id"] == nid or nid in (n.get("alias_ids") or [])), None)
        if same:
            rid = f"{same}~{uuid.uuid4().hex[:6]}"   # scheda del nodo 'same'
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
            # nodo indipendente gia' presente: niente doppione, si restituisce quello
            node = existing_node or manual_node(existing_entry)
            return jsonify({"ok": True, "id": nid, "label": node.get("label"),
                            "platform": node.get("platform"), "script": "",
                            "node": node, "edge": None, "existed": True})
        # Il nodo esiste gia' (aggiunto a mano o presente nei dati): si crea un
        # ulteriore collegamento, con nome, frecce e stile propri. Fra due nodi
        # possono cosi' esserci piu' collegamenti diversi.
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
    # il client inserisce il nodo nel grafo senza ricaricare la pagina; se c'e'
    # una traslitterazione (script non latino) sincronizza per mostrare il nodo latino
    return jsonify({"ok": True, "id": nid, "label": entry["label"],
                    "platform": platform, "script": scr,
                    "node": existing_node or manual_node(entry), "edge": edge})


# firme dei formati immagine accettati, per non fidarsi dell'estensione
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
    """Riceve un'immagine (data URL base64) e la salva in data/media/.
    Ritorna il percorso relativo da usare come valore del nodo foto."""
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
    """Collega nodi con supporto a frecce, etichette, forma della linea e collegamenti multipli."""
    data = request.get_json(silent=True) or {}
    ids = [str(x) for x in (data.get("ids") or []) if str(x).strip()]
    ids = list(dict.fromkeys(ids))                       # senza duplicati, ordine stabile
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
        pairs = [(req_source, req_target)]          # verso scelto dall'utente
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
    """Elimina un collegamento manuale (per id arco o per coppia di nodi)."""
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
    """Modifica un collegamento esistente: nome, frecce, forma, colore, tipo e
    spessore della linea. Vale per TUTTI i collegamenti:
    - creati a mano (fra nodi esistenti o insieme a un nodo aggiunto): si
      aggiorna la loro voce in annotations.json;
    - provenienti dai dati: lo stile si salva a parte ('edge_styles'), i file
      di origine non si toccano. Con 'reset' si torna allo stile predefinito."""
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
        if data.get("swap"):                           # inverte il verso
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
    """Modifica i valori di un nodo: i campi delle schede, i campi aggiunti a
    mano e l'URL. I file di origine restano intatti: le modifiche stanno in
    annotations.json ('edits') e si applicano quando si costruisce il grafo.
    Per i nodi creati a mano si aggiorna anche la loro voce."""
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
    """Rende un nodo qualsiasi un target (o toglie l'evidenza). Per i nodi
    creati a mano si aggiorna la loro voce; per quelli dei dati la scelta sta
    nelle annotazioni ('targets') e si applica costruendo il grafo."""
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
    """Elenco delle modifiche manuali: nodi aggiunti e collegamenti creati."""
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
    """Elimina davvero un nodo aggiunto a mano (e i suoi collegamenti)."""
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
    """Elenco dei nodi cancellati, dal più recente."""
    ann = load_annotations()
    items = sorted(ann["deleted"], key=lambda x: x.get("at") or "", reverse=True)
    return jsonify({"items": items, "count": len(items)})


@bp.route("/api/node/restore", methods=["POST"])
def api_node_restore():
    """Ripristina un nodo ({'id': ...}) oppure tutti ({'all': true}).
    Restituisce i nodi e gli archi tornati disponibili, così il client può
    reinserirli nel grafo senza ricaricare la pagina."""
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
    back = before - after                       # id effettivamente ripristinati
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
    """Elenco delle viste salvate (senza il payload pesante), dalla più recente."""
    if not store.current_case():
        return jsonify({"items": [], "count": 0})
    views = sorted(store.load_views(), key=lambda x: x.get("at") or "", reverse=True)
    out = [{"id": v["id"], "name": v.get("name") or v["id"],
            "at": v.get("at") or "", "count": v.get("count") or 0} for v in views]
    return jsonify({"items": out, "count": len(out)})


@bp.route("/api/views/save", methods=["POST"])
def api_views_save():
    """Salva (o sovrascrive per nome) una vista. Corpo: {name, view:{...}}."""
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
    # sovrascrive se esiste già una vista con lo stesso nome (confronto senza maiuscole)
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
    """Restituisce il payload completo di una vista ({'id': ...})."""
    data = request.get_json(silent=True) or {}
    vid = str(data.get("id") or "").strip()
    v = store.get_view(vid)
    if not v:
        return jsonify({"error": "vista non trovata"}), 404
    return jsonify({"ok": True, "id": v["id"], "name": v.get("name") or v["id"],
                    "view": v.get("view") or {}})


@bp.route("/api/views/delete", methods=["POST"])
def api_views_delete():
    """Elimina una vista salvata ({'id': ...})."""
    data = request.get_json(silent=True) or {}
    vid = str(data.get("id") or "").strip()
    if not store.delete_view(vid):
        return jsonify({"error": "vista non trovata"}), 404
    logging.info(f"Vista eliminata: {vid}")
    return jsonify({"ok": True, "id": vid})
