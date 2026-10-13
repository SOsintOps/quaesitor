# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""The archive: the current graph of the open case, annotations, the index of the
document sources and OCR."""
# "Historia magistra vitae." (Cicero, De Oratore II)
# History is life's teacher.
from urllib.parse import quote
import json
import logging
import os
import re

from . import ontology as onto
from . import sources as _src
from . import ftm, store
from .paths import BASE_DIR
from .core import _hash, _scan, DATA_DIR
from .transliteration import add_translit
from .normalize import birth_it, link_persons, merge_places
from .identifiers import build_graph
from .labels import _cache, data_signature, relabel


# ==================== ARCHIVE (SQLite) ====================
# Everything the user creates or imports lives in data/osintgraph.db (see
# store.py): manually added nodes and cards, links, notes, labels,
# hidden nodes, saved views, transliteration dictionary, JSON imported
# from third-party apps and the document index. Only the uploaded images
# (data/media) and the AI configuration (chatbot.conf) remain on disk.
store.init(DATA_DIR)
logging.info(f"Archivio: {store.path() or 'nessun caso aperto'} (caso {store.current_case()})")

# Sources index (indexed documents): in the database, key 'sources_index'.
SOURCES_BLOB = "sources_index"
# default sources folder: SOURCES_DIR if set, otherwise 'sources' NEXT TO the
# executable (fully portable; 'fonti' in installations before 1.8.0, see
# sources.sources_folder).
# Created right away so the user finds it and puts the documents in it.
SOURCES_DEFAULT = _src.sources_folder(BASE_DIR)
try:
    os.makedirs(SOURCES_DEFAULT, exist_ok=True)
except OSError as _e:
    logging.warning(f"Impossibile creare la cartella fonti {SOURCES_DEFAULT}: {_e}")
_ocr_ok = _src.configure_ocr(BASE_DIR)   # look for a local Tesseract (tools/tesseract)
logging.info(f"OCR {'attivo' if _ocr_ok else 'non disponibile'} "
             f"(cerco Tesseract in {os.path.join(BASE_DIR, 'tools', 'tesseract')}; lingue: {_src.OCR_LANG or 'predefinita'})")
_sources_cache = {"idx": None}


def sources_index():
    if _sources_cache["idx"] is None:
        try:
            _sources_cache["idx"] = store.get_blob(SOURCES_BLOB)
        except store.NoCaseError:
            return None                           # no case open: no index
    return _sources_cache["idx"]


def _save_sources_index(index):
    store.set_blob(SOURCES_BLOB, index)


def _clean_labels(raw):
    """{'labels': {id: {label, orig, at}}} - also accepts the short form
    {id: 'new label'} used by hand-written files."""
    out = {}
    for k, v in (raw or {}).items():
        if isinstance(v, str):
            v = {"label": v}
        if not isinstance(v, dict):
            continue
        lab = re.sub(r"\s+", " ", str(v.get("label") or "")).strip()
        if not lab:
            continue
        out[str(k)] = {"label": lab[:300],
                       "orig": str(v.get("orig") or "")[:300],
                       "ntype": str(v.get("ntype") or ""),
                       "at": str(v.get("at") or "")}
    return out


def load_annotations():
    """User annotations, from the database:
    {'added': [...], 'links': [...], 'deleted': [...], 'notes': {id: text},
     'labels': {id: {...}}, 'edits': {id: {...}}, 'edge_styles': {id: {...}}}.
    Saved with save_annotations, which writes only the differences."""
    try:
        ann = store.load_annotations()
    except Exception as e:
        logging.error(f"Annotazioni illeggibili: {e}")
        ann = {"added": [], "links": [], "deleted": [], "notes": {}, "labels": {},
               "edits": {}, "edge_styles": {}}
    ann["labels"] = _clean_labels(ann.get("labels"))
    return ann


def deleted_ids(ann):
    return {str(x.get("id")) for x in ann["deleted"] if x.get("id")}


def save_annotations(ann):
    try:
        return store.save_annotations(ann)
    except Exception as e:
        logging.error(f"Impossibile salvare le annotazioni: {e}")
        return False


def manual_node(a, note=None):
    """Graph node corresponding to a manually added entry."""
    nid = str(a.get("id"))
    ntype = a.get("ntype") or "generic"
    raw = {k: v for k, v in (("valore", a.get("value") if ntype not in onto.TYPES else None),
                             ("cognome", a.get("cognome")), ("nome", a.get("nome")),
                             ("data_nascita", birth_it(a.get("nascita") or "")),
                             ("descrizione", a.get("label") if a.get("ntype") == "vehicle"
                              and a.get("label") != a.get("value") else None),
                             ("colore", a.get("colore")), ("nota", a.get("note")),
                             ("citta", a.get("citta")),
                             ("indirizzo", a.get("indirizzo")), ("civico", a.get("civico")),
                             ("latitudine", a.get("lat")), ("longitudine", a.get("lon")),
                             ("url", a.get("url")), ("testo", a.get("text")),
                             ("aggiunto_il", a.get("at"))) if v}
    # free columns of an imported file: in the card under the column name
    extra = a.get("extra") if isinstance(a.get("extra"), dict) else {}
    for k, v in extra.items():
        if v and k not in raw:
            raw[k] = v
    # manually added photo: URL served from /media/
    img = None
    if ntype == "photo" and a.get("value"):
        img = "/media/" + quote(str(a["value"]).replace("\\", "/").lstrip("/"))
    fields = a.get("fields") if isinstance(a.get("fields"), dict) else {}
    if ntype in onto.TYPES and fields:
        raw.update(onto.raw_of(ntype, fields))      # the readable fields in the card
    if a.get("target"):
        ntype = "target"                  # person highlighted as target
    node = {
        "id": nid, "label": a.get("label") or nid,
        "ntype": ntype,
        "platform": a.get("platform") or "generic",
        "image": img, "sources": ["manuale"],
        "records": [{"collection": "aggiunto a mano",
                     "images": [img] if img else [], "links": [], "raw": raw}],
        "aliases": [], "alias_ids": [], "merged": 1, "cards": 1, "manual": True,
    }
    if a.get("url"):
        node["url"] = a["url"]        # opens with Alt+Click
    if note:
        node["note"] = note
    if ntype in onto.TYPES:
        node["ficon"] = onto.icon_of(ntype, fields)   # e.g. cannabis, syringe, passport
    return node


EDGE_ARROWS = {"none", "target", "source", "both"}
# all Cytoscape line shapes suitable for a link with arrows
# (only 'haystack' is left out, as it does not draw arrows)
EDGE_CURVES = {"bezier", "straight", "unbundled-bezier", "segments",
               "round-segments", "taxi", "round-taxi", "straight-triangle"}
# shapes with an adjustable joint / curvature ('bend', in pixels)
BEND_CURVES = {"unbundled-bezier", "segments", "round-segments"}
DEFAULT_BEND = 40
EDGE_LSTYLES = {"solid", "dashed", "dotted"}


def edge_props(src, prefix=""):
    """Visual properties of a link, validated.
    'src' is the request or an annotations.json entry; 'prefix' is for the
    'added' entries, where the keys are edge_label / edge_color / ... ."""
    g = lambda k: src.get(prefix + k) if prefix and (prefix + k) in src else src.get(k)
    label = re.sub(r"\s+", " ", str(src.get(prefix + "label") or "")).strip()[:300]
    arrow = str(g("arrow") or "none").strip().lower()
    curve = str(g("curve") or "bezier").strip().lower()
    color = str(g("color") or "").strip()
    lstyle = str(g("lstyle") or "").strip().lower()
    try:
        width = float(g("width") or 0)
    except (TypeError, ValueError):
        width = 0
    try:
        bend = int(round(float(g("bend"))))
    except (TypeError, ValueError):
        bend = DEFAULT_BEND
    # Follow the Money relation: edge schema + properties (only the expected ones)
    fschema = str(g("ftm") or "").strip()
    fprops = g("ftm_props")
    if isinstance(fprops, str) and fprops.strip():
        try:
            fprops = json.loads(fprops)
        except ValueError:
            fprops = {}
    if fschema not in ftm.edge_schemas():
        fschema, fprops = "", {}
    allowed = {f["key"] for f in ftm.edge_fields(fschema)} if fschema else set()
    fprops = {k: re.sub(r"\s+", " ", str(v)).strip()[:300] for k, v in (fprops or {}).items()
              if k in allowed and str(v).strip()} if isinstance(fprops, dict) else {}
    if fschema and not label:
        label = ftm.edge_auto_label(fschema, fprops)
    return {
        "label": label,
        "arrow": arrow if arrow in EDGE_ARROWS else "none",
        "curve": curve if curve in EDGE_CURVES else "bezier",
        "color": color if re.fullmatch(r"#[0-9a-fA-F]{6}", color) else "",
        "lstyle": lstyle if lstyle in EDGE_LSTYLES else "",
        "width": width if 0.5 <= width <= 12 else 0,
        "bend": max(-200, min(200, bend)),
        "ftm": fschema,
        "ftm_props": fprops,
    }


def _store_props(entry, props, prefix=""):
    """Write the properties into an annotations.json entry (no empty keys)."""
    entry[prefix + "label"] = props["label"]
    for k in ("arrow", "curve"):
        entry[k] = props[k]
    for k in ("color", "lstyle", "width"):
        key = prefix + k
        if props[k]:
            entry[key] = props[k]
        else:
            entry.pop(key, None)
    if props["curve"] in BEND_CURVES:
        entry[prefix + "bend"] = props["bend"]
    else:
        entry.pop(prefix + "bend", None)
    if props.get("ftm"):
        entry[prefix + "ftm"] = props["ftm"]
        entry[prefix + "ftm_props"] = dict(props.get("ftm_props") or {})
    else:
        entry.pop(prefix + "ftm", None)
        entry.pop(prefix + "ftm_props", None)


def manual_edge(parent, nid, rel=None, label="", arrow="none", curve="bezier",
                edge_id=None, props=None):
    if edge_id:
        key = str(edge_id)
    else:
        key = "-".join(sorted([_hash(parent), _hash(nid)]))
    p = props or edge_props({"label": label, "arrow": arrow, "curve": curve})
    e = {"id": key, "source": parent, "target": nid, "rel": rel or "manuale",
         "manual": True}
    return _edge_with_props(e, p)


def _edge_with_props(e, p):
    """Copy of the edge with the visual properties: only those set, so the
    default style (or that of the relation type) stays in effect."""
    e = dict(e)
    for k in ("label", "arrow", "curve", "color", "lstyle", "width", "bend", "ftm", "ftm_props"):
        e.pop(k, None)
    if p.get("ftm"):
        e["ftm"] = p["ftm"]
        e["ftm_props"] = dict(p.get("ftm_props") or {})
    if p.get("label"):
        e["label"] = p["label"]
    if p.get("arrow") and p["arrow"] != "none":
        e["arrow"] = p["arrow"]
    if p.get("curve") and p["curve"] != "bezier":
        e["curve"] = p["curve"]
    if p.get("color"):
        e["color"] = p["color"]
    if p.get("lstyle"):
        e["lstyle"] = p["lstyle"]
    if p.get("width"):
        e["width"] = p["width"]
    if p.get("curve") in BEND_CURVES:
        e["bend"] = p.get("bend", DEFAULT_BEND)
    return e


_PATH_TOK = re.compile(r"([^.\[\]]+)|\[(\d+)\]")
EXTRA_COLLECTION = "campi aggiunti"


def _set_path(raw, path, value):
    """Set (or remove, with value=None) the value at the path 'a.b[0].c'
    used by the cards. If the path does not resolve (key with a dot in its
    name, different structure) the full path is used as a top-level key."""
    toks = [(m.group(1), m.group(2)) for m in _PATH_TOK.finditer(path)]
    cur = raw
    try:
        for i, (k, idx) in enumerate(toks):
            last = i == len(toks) - 1
            key = int(idx) if idx is not None else k
            if last:
                if value is None:
                    if isinstance(cur, list):
                        cur[key] = None
                    else:
                        cur.pop(key, None)
                else:
                    cur[key] = value
                return
            cur = cur[key]
    except (KeyError, IndexError, TypeError, ValueError):
        pass
    if isinstance(raw, dict):
        if value is None:
            raw.pop(path, None)
        else:
            raw[path] = value


def apply_node_edits(g, edits):
    """Card values edited by hand (annotations.json -> 'edits').
    The source files are not touched: the edits are applied to a copy.
    Format: {id: {"fields": {"<card no.>|<path>": value or null},
                  "extra": {field: value}, "url": "..."}}"""
    if not edits:
        return
    for i, n in enumerate(g["nodes"]):
        ed = edits.get(n["id"])
        if not isinstance(ed, dict):
            continue
        n = dict(n)
        recs = json.loads(json.dumps(n.get("records") or [], ensure_ascii=False))
        for key, val in (ed.get("fields") or {}).items():
            ri, _, path = str(key).partition("|")
            if not ri.isdigit() or not path or int(ri) >= len(recs):
                continue
            r = recs[int(ri)]
            if not isinstance(r.get("raw"), dict):
                r["raw"] = {}
            _set_path(r["raw"], path, None if val is None else str(val))
        extra = {str(k): str(v) for k, v in (ed.get("extra") or {}).items()
                 if str(k).strip() and v not in (None, "")}
        if extra:
            recs.append({"collection": EXTRA_COLLECTION, "images": [], "links": [],
                         "raw": extra, "extra": True})
        n["records"] = recs
        n["cards"] = len(recs)
        if "url" in ed:
            if ed["url"]:
                n["url"] = ed["url"]
            else:
                n.pop("url", None)
        n["edited"] = True
        g["nodes"][i] = n


def apply_targets(g, targets):
    """«Highlight as target» checkbox changed by hand in the node editor:
    True = the node becomes a target (whatever its type), False = it no
    longer is (a target from the source data goes back to being a person)."""
    if not targets:
        return g
    for i, n in enumerate(g["nodes"]):
        v = targets.get(n["id"])
        if v is None:
            continue
        if v and n.get("ntype") != "target":
            g["nodes"][i] = dict(n, ntype="target")
        elif v is False and n.get("ntype") == "target":
            g["nodes"][i] = dict(n, ntype="name")
    return g


def apply_annotations(graph):
    """Apply notes and deletions to the cached graph, without rebuilding it.
    Returns a copy: the cache stays the 'pure' graph of the source data."""
    ann = load_annotations()
    notes, deleted = ann["notes"], deleted_ids(ann)
    labels = ann.get("labels") or {}

    nodes = []
    for n in graph["nodes"]:
        if n["id"] in deleted:
            continue
        # a merged node stays valid if the deleted id was only one of its aliases
        if deleted and any(a in deleted for a in (n.get("alias_ids") or [])):
            n = dict(n)
            n["alias_ids"] = [a for a in n["alias_ids"] if a not in deleted]
        note = notes.get(n["id"])
        if note:
            n = dict(n)
            n["note"] = note
        nodes.append(n)

    # nodes added by hand from the cards
    by_id = {n["id"]: n for n in nodes}
    pos = {n["id"]: i for i, n in enumerate(nodes)}
    manual_edges = []
    scheda_di = {}                  # id of an added card -> id of its node
    for a in ann.get("added", []):
        nid = str(a.get("id") or "")
        if not nid or nid in deleted:
            continue
        # extra card of an existing node: id '<node id>~xxxxxx'
        base = nid.split("~")[0] if "~" in nid else nid
        if base in by_id:
            # the node already exists (from the imported JSON or an earlier entry):
            # the entry becomes an extra CARD of that node
            mine = manual_node(a)
            node = dict(by_id[base])
            node["records"] = list(node.get("records") or []) + mine["records"]
            node["cards"] = len(node["records"])
            node["sources"] = list(dict.fromkeys(list(node.get("sources") or []) + ["manuale"]))
            if nid != base:
                node["alias_ids"] = list(node.get("alias_ids") or []) + [nid]
                node["merged"] = (node.get("merged") or 1) + 1
                scheda_di[nid] = base
            else:
                # the manual entry gives the node its name and type (the "data" node
                # with the same id is the anchor of an imported JSON)
                node["label"] = mine["label"]
                node["ntype"], node["platform"] = mine["ntype"], mine["platform"]
            if mine["ntype"] == "target":
                node["ntype"], node["platform"] = "target", "target"
            node["manual"] = True
            by_id[base] = node
            nodes[pos[base]] = node
            nid = base
        else:
            node = manual_node(a, notes.get(nid))
            pos[nid] = len(nodes)
            nodes.append(node)
            by_id[nid] = node
        parent = str(a.get("parent") or "")
        parent = scheda_di.get(parent, parent)
        if parent and parent in by_id and parent != nid:
            manual_edges.append(manual_edge(
                parent, nid, a.get("rel"), edge_id=a.get("edge_id"),
                props=edge_props(a, "edge_")))

    # links created by hand between existing nodes
    for l in ann.get("links", []):
        a, b = str(l.get("a") or ""), str(l.get("b") or "")
        a, b = scheda_di.get(a, a), scheda_di.get(b, b)
        if a in by_id and b in by_id and a != b:
            manual_edges.append(manual_edge(
                a, b, "collegamento", edge_id=l.get("id") or l.get("edge_id"),
                props=edge_props(l)))

    alive = {n["id"] for n in nodes}
    styles = ann.get("edge_styles") or {}
    edges = []
    for e in graph["edges"]:
        if e["source"] in alive and e["target"] in alive:
            st = styles.get(e["id"])
            edges.append(_edge_with_props(e, edge_props(st)) if isinstance(st, dict) else e)
    have = {e["id"] for e in edges}
    for e in manual_edges:
        eid = e["id"]
        if eid in have:
            # id already used (old links without their own id): DETERMINISTIC
            # suffix, so the edge keeps the same id on every read
            k = 2
            while f"{eid}_m{k}" in have:
                k += 1
            eid = f"{eid}_m{k}"
            e["id"] = eid
        have.add(eid)
        edges.append(e)
    # labels renamed by hand (and the resulting merge of cards)
    g = relabel({"nodes": nodes, "edges": edges}, labels)
    apply_node_edits(g, ann.get("edits") or {})
    apply_targets(g, ann.get("targets") or {})
    # same address (city, street, house number) = one node; same street = dashed line
    g = merge_places(g)
    # first name and surname only ~ same person with the date of birth: dashed line
    g = link_persons(g)

    # Transliteration of manually added nodes: they do not go through build_graph,
    # so a name in a non-Latin alphabet would not get its Latin node.
    # Offline (ICU/dictionary only) to be immediate and without touching the
    # files; refinement with the chatbot happens on reload or with the button.
    manual_ids = {n["id"] for n in g["nodes"] if n.get("manual")}
    if manual_ids:
        add_translit(g, only=manual_ids, offline=True)
    mark_evidence(g)
    return g


def mark_evidence(g):
    """Links and photos that come from a Cognitor bundle or from a transcription.

    An Associate "seen together" edge gets evid="seen" and its weight (photos plus
    video segments, read from the summary); "speaks in" and "appears in" links get
    evid="speaks" / "appears". A person pictured by a photo node shows the first photo
    as its icon and every photo in its card (decision of 2026-10-12)."""
    nodes = {n["id"]: n for n in g["nodes"]}
    photos = {}
    for e in g["edges"]:
        lab = str(e.get("label") or "").strip().lower()
        fp = e.get("ftm_props") or {}
        if e.get("ftm") == "Associate" and "seen together" in str(fp.get("relationship") or "").lower():
            e["evid"] = "seen"
            nums = [int(x) for x in re.findall(r"\d+", str(fp.get("summary") or e.get("label") or ""))[:2]]
            e["seen_n"] = max(1, sum(nums))
        elif lab in ("speaks in", "appears in"):
            e["evid"] = "speaks" if lab == "speaks in" else "appears"
        elif lab == "pictured":
            a, b = nodes.get(e["source"]), nodes.get(e["target"])
            if a and b and a.get("ntype") == "photo" and a.get("image") \
                    and b.get("ntype") in ("name", "target"):
                photos.setdefault(b["id"], []).append(a["image"])
    for nid, imgs in photos.items():
        n = nodes[nid]
        if not n.get("image"):
            n["image"] = imgs[0]
            n["pic"] = True
        recs = n.setdefault("records", [])
        recs.append({"collection": "pictured", "category": "", "images": imgs[:12],
                     "links": [], "raw": {}})


def current_graph():
    """Full graph (data + annotations), rebuilt only if the data have changed.
    With no case open the graph is empty and says so ('no_case')."""
    if not store.current_case():
        return {"nodes": [], "edges": [], "no_case": True}
    key = data_signature()
    if _cache["key"] != key:
        _cache["graph"] = build_graph()
        _cache["key"] = key
    return apply_annotations(_cache["graph"])


def _sources_folder():
    """The folder of the sources the search reads now (default: 'sources')."""
    idx = sources_index()
    return _src.resolved_folder(idx, BASE_DIR, SOURCES_DEFAULT) if idx else SOURCES_DEFAULT


def _run_scan(folder):
    try:
        for ev in _src.scan_folder_stream(folder, _save_sources_index, base_dir=BASE_DIR):
            ph = ev.get("phase")
            if ph == "start":
                _scan["total"] = ev.get("total", 0)
            elif ph == "file":
                _scan["done"] = ev.get("done", 0)
                _scan["total"] = ev.get("total", 0)
                _scan["name"] = ev.get("name", "")
            elif ph == "done":
                _sources_cache["idx"] = None
                ev["ocr_available"] = _src.OCR_AVAILABLE
                ev["indexed"] = True
                _scan["summary"] = {k: v for k, v in ev.items() if k != "phase"}
    except Exception as e:
        logging.error(f"Scansione fonti fallita: {e}")
        _scan["error"] = str(e)
    finally:
        _scan["running"] = False
        _scan["finished"] = True
