# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Bulk import: tables (CSV, Excel) read, mapped and turned into nodes."""
# "Gutta cavat lapidem." (after Ovid, Epistulae ex Ponto)
# The drop hollows the stone.
from datetime import datetime
import json
import re
import unicodedata
import uuid

from . import ontology as onto
from . import ftm, store
from .core import _hash, _json_obj, _truthy, NodeError
from .dictionary import _translit_new_labels, new_added_entry, resolve_node, same_place_id
from .archive import _store_props, current_graph, edge_props, load_annotations, save_annotations


# ============================ BULK IMPORT (CSV / EXCEL) ============================
# Each row describes a node, or two nodes and the link between them:
#   name1, type1, link, name2, type2  (+ optional columns)
# Headers are recognised in Italian and in English; without a header the
# first five columns are used in this order.

IMPORT_MAX_ROWS = 5000

SOCIAL_HOSTS = {
    "instagram.com": "instagram", "tiktok.com": "tiktok",
    "facebook.com": "facebook", "fb.com": "facebook", "fb.me": "facebook",
    "x.com": "x", "twitter.com": "x", "threads.net": "threads", "threads.com": "threads",
    "t.me": "telegram", "telegram.me": "telegram", "telegram.org": "telegram",
    "vk.com": "vk", "vk.ru": "vk", "vkontakte.ru": "vk",
    "snapchat.com": "snapchat", "linkedin.com": "linkedin", "github.com": "github",
    "youtube.com": "youtube", "youtu.be": "youtube", "spotify.com": "spotify",
    "pinterest.com": "pinterest", "reddit.com": "reddit",
    "wa.me": "whatsapp", "whatsapp.com": "whatsapp",
}
SOCIAL_PLATFORMS = set(SOCIAL_HOSTS.values()) | {
    "discord", "signal", "viber", "skype", "wechat", "line", "kakaotalk", "icq",
    "threema", "tango", "imo", "botim", "zangi", "twitter"}


def parse_social_url(raw):
    """From a profile URL derives (platform, handle); None if it is not a social network."""
    from urllib.parse import urlparse, parse_qs, unquote
    s = str(raw or "").strip()
    if not s:
        return None
    if not re.match(r"^https?://", s, re.I):
        s = "https://" + s
    try:
        u = urlparse(s)
    except ValueError:
        return None
    host = re.sub(r"^(www|m|mobile|open|api)\.", "", (u.hostname or "").lower())
    platform = SOCIAL_HOSTS.get(host)
    if not platform:
        return None
    segs = [unquote(x) for x in u.path.split("/") if x]
    q = parse_qs(u.query)
    strip = lambda x: str(x or "").lstrip("@").strip()
    first = lambda i: segs[i] if len(segs) > i else ""
    if platform == "facebook" and u.path.lower().endswith("profile.php"):
        h = (q.get("id") or [""])[0]
    elif platform == "youtube":
        h = first(1) if first(0) in ("channel", "c", "user") else strip(first(0))
    elif platform == "snapchat":
        h = first(1) if first(0) == "add" else strip(first(0))
    elif platform == "linkedin":
        h = first(1) if first(0) in ("in", "company") else strip(first(0))
    elif platform == "reddit":
        h = first(1) if first(0) in ("user", "u") else strip(first(0))
    elif platform == "spotify":
        h = first(1) if first(0) == "user" else strip(first(0))
    elif platform == "whatsapp":
        h = re.sub(r"\D", "", (q.get("phone") or [first(0)])[0])
    else:
        h = strip(first(0))
    h = strip(h).rstrip("/")
    return (platform, h) if h else None


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", s.lower())


# recognised headers (normalised: lower case, no accents or spaces)
_NODE_COLS = {
    "name": {"nome", "name", "nomenodo", "nodo", "node", "nodename", "valore", "value",
             "identificativo", "id", "entita", "entity"},
    "type": {"tipo", "type", "tiponodo", "nodetype", "categoria", "category"},
    "label": {"etichetta", "label", "displayname", "nomevisualizzato", "titolo", "title"},
    "url": {"url", "link", "profilo", "profile", "sito", "website"},
    "platform": {"piattaforma", "platform", "social", "servizio", "service"},
    "text": {"testo", "text", "descrizione", "description", "contenuto"},
    "cognome": {"cognome", "surname", "lastname", "familyname"},
    "colore": {"colore", "color", "colour"},
    "nascita": {"nascita", "datanascita", "datadinascita", "natoil", "birthdate",
                "dateofbirth", "dob", "birthday"},
    "flag": {"target", "evidenzia", "flagtarget"},
    "address": {"indirizzo", "address", "via", "street"},
    "civico": {"civico", "numerocivico", "ncivico", "nr", "housenumber", "streetnumber"},
    "lat": {"lat", "latitudine", "latitude"},
    "lon": {"lon", "lng", "long", "longitudine", "longitude"},
    "note": {"nota", "note", "notes", "commento", "comment"},
    "fields": {"campi", "fields", "dati"},            # JSON of the fields of an ontology type
}
_SIDE_ALIASES = {"1": {"da", "from", "sorgente", "source", "origine", "partenza"},
                 "2": {"a", "to", "destinazione", "destination", "arrivo", "dest"}}
_EDGE_COLS = {
    "rel": {"collegamento", "tipocollegamento", "relazione", "relation", "relationship",
            "rel", "edge", "edgelabel", "nomecollegamento", "legame", "connessione",
            "connection", "linktype"},
    "arrow": {"frecce", "freccia", "arrow", "arrows", "direzione", "direction", "verso"},
    "curve": {"forma", "shape", "curve", "formalinea", "curvestyle"},
    "color": {"colore", "color", "colour", "colorecollegamento"},
    "lstyle": {"linea", "tipolinea", "linestyle", "stilelinea", "tratto", "line", "linetype",
               "stroke", "dash"},
    "width": {"spessore", "width", "larghezza"},
    "ftm": {"ftmedge", "relazioneftm", "schemaarco", "ftmrelation", "ftm"},
    "ftm_props": {"ftmprops", "proprietaarco", "proprietaftm", "ftmproperties"},
}


def _reserved_norms():
    out = set(_SIDE_ALIASES["1"]) | set(_SIDE_ALIASES["2"])
    for al in list(_NODE_COLS.values()) + list(_EDGE_COLS.values()):
        out |= set(al)
    return out


_RESERVED = None


def ftm_reserved(name):
    """True when a free column of a Follow the Money file would be read as a fixed
    column (title -> label, type -> node type, service -> platform...)."""
    global _RESERVED
    if _RESERVED is None:
        _RESERVED = _reserved_norms()
    return _norm(name) in _RESERVED


def map_header(cells):
    """Maps the headers: {column index: key}. Keys such as 'name1',
    'type2', 'url1', 'rel', 'arrow'. None if the row does not look like a header."""
    out, sides = {}, {}
    for i, c in enumerate(cells):
        n = _norm(c)
        if not n:
            continue
        if n in _SIDE_ALIASES["1"]:
            sides[i] = "name1"
            continue
        if n in _SIDE_ALIASES["2"]:
            sides[i] = "name2"
            continue
        key = next((k for k, al in _EDGE_COLS.items() if n in al), None)
        if key:
            out[i] = key
            continue
        m = re.match(r"^(.*?)(1|2)$", n)
        base, side = (m.group(1), m.group(2)) if m else (n, "")
        base = re.sub(r"(nodo|node)$", "", base) or base
        base = re.sub(r"^(nodo|node)", "", base) or base
        key = next((k for k, al in _NODE_COLS.items() if base in al), None)
        if key is None:
            continue
        if not side:
            # column without a number: applies to the first node if not already taken
            side = "1" if f"{key}1" not in out.values() else "2"
        out[i] = f"{key}{side}"
    # «da / from / source» and «a / to / destination» count as the node name
    # only if that side does not already have a name column: otherwise (e.g. a
    # "Source" column with the origin of the data) they are left to assign by hand
    for i, k in sides.items():
        if k not in out.values():
            out[i] = k
    # the same key on two columns: the first wins, the other stays free
    seen = set()
    for i in sorted(out):
        if out[i] in seen:
            del out[i]
        else:
            seen.add(out[i])
    return out if "name1" in out.values() else None


_TYPE_ALIASES = {
    "account": {"social", "account", "profilo", "profile", "socialnetwork", "socialmedia"},
    "link": {"link", "url", "sito", "website", "web", "pagina", "page"},
    "phone": {"phone", "telefono", "tel", "cellulare", "mobile", "utenza", "numero",
              "number", "cell", "sim"},
    "email": {"email", "mail", "posta", "emailaddress"},
    "username": {"username", "user", "utente", "nick", "nickname", "alias", "handle"},
    "name": {"name", "nome", "persona", "person", "people", "individuo", "soggetto"},
    "place": {"place", "luogo", "localita", "citta", "city", "indirizzo", "address",
              "location", "posizione"},
    "vehicle": {"vehicle", "veicolo", "auto", "targa", "plate", "car", "moto", "mezzo"},
    "text": {"text", "testo", "nota", "note", "appunto"},
    "target": {"target", "obiettivo", "bersaglio"},
    # a photo already under DATA_DIR/media (Follow the Money Image with its file, 2026-10-12)
    "photo": {"photo", "foto", "immagine", "image"},
}


def _guess_type(value, url):
    v = str(value or "").strip()
    if url and parse_social_url(url):
        return "account"
    if parse_social_url(v) and re.match(r"^(https?://)?[\w.-]+\.\w+/", v, re.I):
        return "account"
    if re.match(r"^https?://", v, re.I) or (url and not v):
        return "link"
    if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", v):
        return "email"
    if re.fullmatch(r"\+?[\d\s().-]{6,}", v) and len(re.sub(r"\D", "", v)) >= 6:
        return "phone"
    if v.startswith("@"):
        return "username"
    return "name"


def import_node_spec(row, side):
    """Data of one side of the row -> request for resolve_node (or None)."""
    g = lambda k: str(row.get(f"{k}{side}") or "").strip()
    name, url = g("name"), g("url")
    if not name and not url:
        return None
    t = _norm(g("type"))
    plat = _norm(g("platform"))
    if t in SOCIAL_PLATFORMS:                     # type = name of the social network
        ntype, plat = "account", t
    else:
        ntype = next((k for k, al in _TYPE_ALIASES.items() if t in al), None) if t else None
        if t and ntype is None:
            ntype = onto.type_of(g("type"))         # weapon, narcotic, cheque...
        if t and ntype is None:
            raise NodeError(f"tipo di nodo sconosciuto: «{g('type')}»")
        ntype = ntype or _guess_type(name, url)
    spec = {"ntype": ntype, "value": name, "label": g("label"), "url": url,
            "text": g("text"), "address": g("address"), "civico": g("civico"),
            "cognome": g("cognome"), "nascita": g("nascita"), "colore": g("colore"),
            "fields": _json_obj(g("fields")),
            "target": ntype == "target" or _truthy(g("flag")),
            "lat": g("lat"), "lon": g("lon"),
            "platform": plat, "note": g("note"),
            "extra": row.get(f"extra{side}") if isinstance(row.get(f"extra{side}"), dict) else {}}
    if ntype == "account":
        p = parse_social_url(url) or parse_social_url(name)
        if p:
            spec["platform"] = spec["platform"] or p[0]
            spec["value"] = p[1]
            spec["label"] = spec["label"] or (name if name and not parse_social_url(name) else "")
            spec["url"] = url or (name if re.match(r"^https?://", name, re.I) else "")
        elif not spec["platform"]:
            raise NodeError("social: serve l'URL del profilo o la piattaforma")
        if spec["platform"] == "twitter":
            spec["platform"] = "x"
    elif ntype == "link":
        link = url if re.match(r"^https?://", url, re.I) else name
        spec["value"] = link
        spec["label"] = spec["label"] or (name if name and name != link else "")
        spec["url"] = link
    elif ntype == "text":
        spec["label"] = spec["label"] or name
        spec["text"] = spec["text"] or spec["note"]
    elif ntype == "vehicle" and spec["label"]:
        targa = re.sub(r"\s+", "", name).upper()
        if not re.sub(r"\s+", "", spec["label"]).upper().startswith(targa):
            spec["label"] = f"{targa} {spec['label']}"
    return spec


_ARROWS = {"target": {"target", "avanti", "forward", "si", "yes", "true", "1", "x",
                      "destinazione", "to", "a"},
           "source": {"source", "indietro", "back", "backward", "sorgente", "from", "da"},
           "both": {"both", "entrambe", "entrambi", "doppia", "doppio", "bidirezionale",
                    "bidirectional", "2"},
           "none": {"none", "nessuna", "no", "false", "0", ""}}
_ARROW_SYM = {"->": "target", "→": "target", ">": "target", "<-": "source",
              "←": "source", "<": "source", "<->": "both", "↔": "both", "<>": "both",
              "-": "none", "—": "none"}
_CURVE_ALIASES = {"bezier": {"auto", "automatica", "automatic", "bezier", "predefinita",
                             "default"},
                  "straight": {"retta", "dritta", "straight", "lineare"},
                  "unbundled-bezier": {"curva", "arco", "curve", "curved", "arc",
                                       "unbundledbezier"},
                  "segments": {"spezzata", "snodo", "segmenti", "segments", "polyline",
                               "gomito"},
                  "round-segments": {"spezzataarrotondata", "roundsegments",
                                     "snodoarrotondato"},
                  "taxi": {"angolo", "angoloretto", "ortogonale", "taxi", "rightangle",
                           "orthogonal"},
                  "round-taxi": {"angoloarrotondato", "roundtaxi", "angolorettoarrotondato"},
                  "straight-triangle": {"cuneo", "wedge", "triangolo", "straighttriangle"}}
_LSTYLES = {"solid": {"continua", "solid", "piena", "continuo"},
            "dashed": {"tratteggiata", "dashed", "trattini", "tratteggio"},
            "dotted": {"punteggiata", "dotted", "puntini", "punti"}}
_COLORS = {"rosso": "#dc2626", "red": "#dc2626", "blu": "#2563eb", "blue": "#2563eb",
           "verde": "#16a34a", "green": "#16a34a", "arancione": "#ea580c",
           "orange": "#ea580c", "giallo": "#d97706", "yellow": "#d97706",
           "viola": "#7c3aed", "purple": "#7c3aed", "rosa": "#db2777", "pink": "#db2777",
           "nero": "#0f172a", "black": "#0f172a", "grigio": "#94a3b8", "gray": "#94a3b8",
           "grey": "#94a3b8", "azzurro": "#0891b2", "cyan": "#0891b2"}


def import_edge_props(row):
    a = str(row.get("arrow") or "").strip()
    arrow = _ARROW_SYM.get(a.replace(" ", "")) or \
        next((k for k, al in _ARROWS.items() if _norm(a) in al), "none")
    c = _norm(row.get("curve"))
    curve = next((k for k, al in _CURVE_ALIASES.items() if c in al), "bezier")
    col = str(row.get("color") or "").strip()
    if re.fullmatch(r"#?[0-9a-fA-F]{6}", col):
        col = "#" + col.lstrip("#")
    else:
        col = _COLORS.get(_norm(col), "")
    ls = _norm(row.get("lstyle"))
    return edge_props({"label": row.get("rel"), "arrow": arrow, "curve": curve,
                       "color": col,
                       "lstyle": next((k for k, al in _LSTYLES.items() if ls in al), ""),
                       "width": str(row.get("width") or "").replace(",", "."),
                       "ftm": row.get("ftm"), "ftm_props": row.get("ftm_props")})


def plan_rows(rows):
    """Interprets rows already "as dictionaries" ({'name1', 'type1', 'rel', ...}):
    for each, the two nodes (id, label, type) and the link. Writes nothing:
    it serves the preview and the import (from a file or from the AI).
    A side can point directly to an existing node with 'id1' / 'id2'."""
    g = current_graph()
    have = {n["id"]: n for n in g["nodes"]}
    plan = []
    for row in rows:
        item = {"row": int(row.get("_row") or len(plan) + 1), "raw": row,
                "nodes": [], "error": ""}
        try:
            for side in ("1", "2"):
                fixed = str(row.get(f"id{side}") or "").strip()
                if fixed:                              # node already in the graph
                    n = have.get(fixed)
                    if n is None:
                        raise NodeError("il nodo di partenza non esiste piu'")
                    item["nodes"].append({"side": side, "id": fixed, "label": n.get("label"),
                                          "ntype": n.get("ntype"), "platform": n.get("platform"),
                                          "exists": True, "spec": None})
                    continue
                spec = import_node_spec(row, side)
                if spec is None:
                    continue
                nid, label, platform, ntype, value = resolve_node(spec, "")
                spec.update(value=value, platform=platform)
                item["nodes"].append({"side": side, "id": nid,
                                      "label": spec.get("label") or label,
                                      "ntype": ntype, "platform": platform,
                                      "exists": nid in have, "spec": spec})
            if not item["nodes"]:
                raise NodeError("riga senza nodi")
            if len(item["nodes"]) == 2:
                item["edge"] = import_edge_props(row)
        except NodeError as e:
            item["error"] = str(e)
        plan.append(item)
    return plan


# columns the user can assign in the wizard (besides
# "extra1:<name>" / "extra2:<name>", which end up in the node's card)
IMPORT_NODE_KEYS = ("name", "type", "label", "url", "platform", "text", "cognome", "nascita",
                    "colore", "flag", "address", "civico", "lat", "lon", "note")
IMPORT_EDGE_KEYS = ("rel", "arrow", "curve", "color", "lstyle", "width", "ftm", "ftm_props")


def plan_import(table, mapping=None, has_header=None, defaults=None):
    """Rows read from a file (lists of cells) -> import plan.
    Without 'mapping' the columns are recognised from the headers (or, with no
    header, in the fixed order name1, type1, link, name2, type2);
    with 'mapping' ({column index: key}) the user's choice applies."""
    if not table:
        raise NodeError("il file e' vuoto")
    defaults = defaults or {}
    if mapping:
        header = dict(mapping)
        if has_header is None:
            has_header = True
    else:
        header = map_header(table[0])
        has_header = bool(header)
        if not header:                      # no header: fixed order
            header = dict(enumerate(["name1", "type1", "rel", "name2", "type2"]))
    if "name1" not in header.values():
        raise NodeError("serve una colonna con il nome (o il valore) del nodo 1")
    first = 2 if has_header else 1          # number of the first data row
    body = table[1:] if has_header else table
    if len(body) > IMPORT_MAX_ROWS:
        raise NodeError(f"troppe righe (massimo {IMPORT_MAX_ROWS})")
    rows = []
    for i, cells in enumerate(body):
        row = {}
        for c, k in header.items():
            v = cells[c] if c < len(cells) else ""
            if k.startswith(("extra1:", "extra2:")):          # card field
                side, _, name = k.partition(":")
                if str(v).strip() and name.strip():
                    row.setdefault(side, {})[name.strip()[:120]] = str(v).strip()
            else:
                row[k] = v
        for side in ("1", "2"):
            if defaults.get(f"type{side}") and not str(row.get(f"type{side}") or "").strip():
                row[f"type{side}"] = defaults[f"type{side}"]
        if defaults.get("rel") and not str(row.get("rel") or "").strip():
            row["rel"] = defaults["rel"]
        row["_row"] = i + first
        rows.append(row)
    return plan_rows(rows), header


def _merge_entry(entry, n, spec):
    """Re-import: updates the existing entry of a node (fields, free columns,
    label) instead of adding a card."""
    changed = False
    if n["ntype"] in onto.TYPES and spec.get("fields"):
        cur = dict(entry.get("fields") or {})
        new = onto.clean_fields(n["ntype"], spec["fields"])
        if any(cur.get(k) != v for k, v in new.items()):
            cur.update(new)
            entry["fields"] = cur
            entry["label"] = onto.label_of(n["ntype"], cur)
            changed = True
    ex = spec.get("extra") if isinstance(spec.get("extra"), dict) else {}
    if ex:
        cur = dict(entry.get("extra") or {})
        new = {str(k).strip()[:120]: str(v).strip()[:20000] for k, v in ex.items()
               if str(k).strip() and str(v).strip()}
        if any(cur.get(k) != v for k, v in new.items()):
            cur.update(new)
            entry["extra"] = cur
            changed = True
    if spec.get("note") and spec["note"] != entry.get("note"):
        entry["note"] = str(spec["note"])[:4000]
        changed = True
    return changed


def _ftm_id_of(spec):
    """Follow the Money id of an imported row, if any."""
    f = spec.get("fields") if isinstance(spec.get("fields"), dict) else {}
    if f.get("ftmId"):
        return str(f["ftmId"])
    ex = spec.get("extra") if isinstance(spec.get("extra"), dict) else {}
    return str(ex.get("FtM id") or "")


def _ftm_schema_of(spec, ntype):
    """FtM schema of an imported row: from the native type or from the card."""
    sc = ftm.FTM_SCHEMA_OF.get(ntype)
    if sc:
        return sc
    ex = spec.get("extra") if isinstance(spec.get("extra"), dict) else {}
    return str(ex.get("Schema FtM") or "")


def commit_plan(plan, skip=(), update=False, ftm_dataset=None):
    """Writes the plan's nodes and links to annotations.json. Rows already
    imported create no duplicates (same node = same id; same link with the
    same name between the same nodes = skipped).
    update=True (Follow the Money re-import): a node already present is
    UPDATED (fields, free columns, label) instead of receiving one more
    card; ftm_dataset: name of the dataset recorded with the FtM ids."""
    ann = load_annotations()
    by_id = {str(x.get("id")): x for x in ann["added"]}
    updated, ftm_pairs = 0, []
    known = store.ftm_map() if update else {}       # FtM id already in the case -> node
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    g0 = current_graph()
    have = {n["id"] for n in g0["nodes"]}
    added_ids = {str(x.get("id")) for x in ann["added"]}
    in_commit, remap = set(), {}            # places already handled in this import
    link_keys = {(str(l.get("a")), str(l.get("b")), str(l.get("label") or ""))
                 for l in ann["links"]}
    # also the links created with a node added by hand ('added' entry with
    # 'parent'): otherwise a re-import would create them a second time
    for x in ann["added"]:
        if x.get("parent"):
            link_keys.add((str(x["parent"]), str(x.get("id")), str(x.get("edge_label") or "")))
    made_nodes, made_links, same_links, errors, touched = 0, 0, 0, [], []
    for it in plan:
        if it["row"] in skip:
            continue
        if it["error"]:
            errors.append({"row": it["row"], "error": it["error"]})
            continue
        ids = []
        for n in it["nodes"]:
            nid, spec = n["id"], n["spec"]
            if known and spec:
                fid = _ftm_id_of(spec)
                if fid and known.get(fid) and known[fid] != nid and (known[fid] in have or known[fid] in by_id):
                    remap[nid] = known[fid]          # same FtM entity, node already in the case
                    nid = known[fid]
            # same row repeated (the AI mentions the same node in several links):
            # it counts once; different data (two rows with the same number plate)
            # are different cards
            firma = (nid, json.dumps(spec, sort_keys=True, ensure_ascii=False) if spec else "")
            if (n["ntype"] in ("place", "vehicle") or n["ntype"] in onto.TYPES)                     and spec and firma not in in_commit:
                in_commit.add(firma)
                same = (same_place_id(g0, spec["value"], spec) if n["ntype"] == "place" else None)                     or remap.get(nid) or (nid if nid in have else None)
                if same and update and same in by_id:
                    # re-import: same node, updated data, no extra card
                    remap[nid] = same
                    if _merge_entry(by_id[same], n, spec):
                        updated += 1
                    ids.append(same)
                    touched.append(same)
                    fid = _ftm_id_of(spec)
                    if fid:
                        ftm_pairs.append((fid, same, _ftm_schema_of(spec, n["ntype"]), ftm_dataset))
                    continue
                if same:
                    remap[nid] = same
                    # place / vehicle already present: one more card in the
                    # existing node (entry with its own id '<id>~xxxxxx')
                    ann["added"].append(new_added_entry(
                        f"{same}~{uuid.uuid4().hex[:6]}", n["label"], n["platform"],
                        n["ntype"], spec["value"], spec, "", now))
                    nid = same
                    ids.append(nid)
                    touched.append(nid)
                    made_nodes += 1
                    continue
            nid = remap.get(nid, nid)
            ids.append(nid)
            touched.append(nid)
            if spec is not None:
                fid = _ftm_id_of(spec)
                if fid:
                    ftm_pairs.append((fid, nid, _ftm_schema_of(spec, n["ntype"]), ftm_dataset))
            if spec is None or nid in have or nid in added_ids:
                if spec is not None and update and nid in by_id and _merge_entry(by_id[nid], n, spec):
                    updated += 1
                continue
            ann["deleted"] = [x for x in ann["deleted"] if str(x.get("id")) != nid]
            entry = new_added_entry(nid, n["label"], n["platform"], n["ntype"], spec["value"], spec, "", now)
            ann["added"].append(entry)
            by_id[nid] = entry
            added_ids.add(nid)
            if spec.get("note") and n["ntype"] != "text" and nid not in ann["notes"]:
                ann["notes"][nid] = spec["note"][:4000]
            have.add(nid)
            made_nodes += 1
        if len(ids) == 2 and ids[0] != ids[1]:
            props = it["edge"]
            key = (ids[0], ids[1], props["label"])
            if key in link_keys:
                same_links += 1
                continue
            entry = {"id": f"e_{_hash(ids[0])[:8]}_{_hash(ids[1])[:8]}_{uuid.uuid4().hex[:8]}",
                     "a": ids[0], "b": ids[1], "at": now}
            _store_props(entry, props)
            ann["links"].append(entry)
            link_keys.add(key)
            made_links += 1

    if (made_nodes or made_links or updated) and not save_annotations(ann):
        raise NodeError("salvataggio fallito")
    if ftm_pairs:
        store.ftm_set(ftm_pairs)
    if made_nodes:                               # import and nodes proposed by the AI
        _translit_new_labels([x.get("label") for x in ann["added"]
                              if str(x.get("id")) in set(touched)])
    return {"ok": True, "nodes": made_nodes, "links": made_links, "updated": updated,
            "same_links": same_links, "errors": errors,
            "ids": list(dict.fromkeys(touched))}


def _plan_json(plan):
    """Plan for the client (without the internal raw data)."""
    return [{k: v for k, v in it.items() if k != "raw"} for it in plan]


def _ftm_mapping(header):
    """Mapping of the columns produced by ftm.rows_from_entities: those
    recognised from the header, the others as free fields of node 1 or 2."""
    auto = map_header(header) or {}
    out = {}
    for i, name in enumerate(header):
        k = auto.get(i)
        if k:
            out[i] = k
            continue
        name = str(name)
        side = "2" if name.endswith("2") else "1"
        # the card key is the name without the side suffix, so the same value
        # has the same key from node 1 or from node 2 (stable re-import)
        out[i] = f"extra{side}:{name[:-1] if name[-1:] in '12' else name}"
    return out
