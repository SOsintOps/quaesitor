# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Places, people and addresses: the normal forms that decide when two nodes are
the same."""
# "Simplex sigillum veri." (traditional maxim)
# Simplicity is the seal of truth.
from datetime import datetime
import re
import unicodedata

import regex as _rx

from .core import _flat, _hash, NodeError
from .transliteration import WORD_RE


# ---------------------------------------------------------------- PLACES ---
# Keys that hold a real place (city, address, origin).
PLACE_KEYS = {"location", "locations", "address", "addresses", "last_address",
              "hometown", "city", "town", "street", "birthplace", "residence"}
# Subtrees NOT to explore: they hold the country of the phone CARRIER, not of
# the subject. It appears in hundreds of cards and would create a single node
# linked to everything (e.g. «Libyan Arab Jamahiriya»), useless and misleading.
PLACE_SKIP_SUBTREE = {"original_network_details", "current_network_details",
                      "network_details", "sea", "seacomcousub", "seawik",
                      "cheact", "gcon", "raw"}
# values that look like places but are not
PLACE_STOP = {"true", "false", "none", "null", "n/a", "na", "unknown",
              "available", "not_applicable", "home", "work", "other"}
# Subset of PLACE_KEYS that holds a precise address (not a city).
ADDRESS_KEYS = {"address", "addresses", "last_address", "street", "residence"}
# Words that reveal an actual address (street, house number, building...).
# Only whole, unambiguous words: abbreviations (st, rd, dr...) are in STREET_ABBR
# because on their own they would also match city names ("St. Petersburg").
STREET_RE = re.compile(
    r"(?i)(?:^|[\s,.-])(via|viale|vicolo|piazza|piazzale|corso|largo|strada|"
    r"contrada|borgo|street|road|avenue|boulevard|lane|drive|square|highway|"
    r"route|rue|calle|avenida|carrera|strasse|straße|platz|sharia|tariq|"
    r"zanqat|zenkat|block|building|apartment|floor|interno|civico|piano)"
    r"(?:[\s,.]|$)")
# Address abbreviations: they count only if the label also has a house number.
STREET_ABBR = re.compile(
    r"(?i)(?:^|[\s,.-])(v\.le|p\.zza|st|str|rd|ave|blvd|ln|dr|sq|hwy|rte|apt|"
    r"bldg|km|n|no|nr)(?:[\s,.]|$)")
GOOGLE_PLACE_ID = re.compile(r"^(ChIJ|EI|Gh)[A-Za-z0-9_\-]{8,}$")
COORD_PAIR = re.compile(r"^\s*(-?\d{1,3}(?:\.\d+)?)\s*[,;]\s*(-?\d{1,3}(?:\.\d+)?)\s*$")


def _valid_coord(lat, lon):
    try:
        la, lo = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not (-90 <= la <= 90) or not (-180 <= lo <= 180):
        return None
    if la == 0 and lo == 0:                       # null coordinate: not a place
        return None
    return f"{la:.6f}".rstrip("0").rstrip("."), f"{lo:.6f}".rstrip("0").rstrip(".")


def collect_places(o, out=None, key=""):
    """Extracts the places mentioned in the raw data of a card.
    Returns a list of {'label': ..., 'lat': ..., 'lon': ...} without duplicates."""
    if out is None:
        out = []
    if isinstance(o, dict):
        # an object with latitude and longitude is a place, with its label
        pair = _valid_coord(o.get("latitude", o.get("lat")),
                            o.get("longitude", o.get("lon", o.get("lng"))))
        if pair:
            lab, lab_key = "", key
            for k in ("address", "name", "city", "label", "location"):
                if isinstance(o.get(k), str) and o[k].strip():
                    lab, lab_key = o[k].strip(), k
                    break
            out.append({"label": lab, "lat": pair[0], "lon": pair[1],
                        "key": str(lab_key).lower()})
        for k, v in o.items():
            if str(k).lower() in PLACE_SKIP_SUBTREE:
                continue
            collect_places(v, out, str(k))
    elif isinstance(o, list):
        for v in o[:40]:
            collect_places(v, out, key)
    elif isinstance(o, str):
        s = re.sub(r"\s+", " ", o).strip().strip(",;")
        if not s:
            return out
        m = COORD_PAIR.match(s)                   # "48.857,2.351"
        if m and key.lower() in ("coordinates", "coords", "coordinate", "geo"):
            pair = _valid_coord(m.group(1), m.group(2))
            if pair:
                out.append({"label": "", "lat": pair[0], "lon": pair[1],
                            "key": key.lower()})
            return out
        if key.lower() not in PLACE_KEYS:
            return out
        if (len(s) < 3 or len(s) > 120 or s.lower() in PLACE_STOP
                or GOOGLE_PLACE_ID.match(s) or not WORD_RE.search(s)):
            return out
        out.append({"label": s, "lat": None, "lon": None, "key": key.lower()})
    return out


def place_is_address(label, lat=None, lon=None, key=""):
    """True if the place is an ADDRESS (street address or point on the map), not a
    generic city/region. Only an address can link different cards together:
    "Tripoli" or "Libya" recur in hundreds of cards and would create a magnet
    node joining people who have nothing to do with each other."""
    if lat and lon:                       # a point on the map is already precise
        return True
    s = re.sub(r"\s+", " ", str(label or "")).strip()
    if len(s) < 4:
        return False
    has_num = bool(re.search(r"\d", s))
    if STREET_RE.search(s):               # "Via del Porto 12", "12 Main Street"
        return has_num or len(s.split()) >= 2
    if has_num and STREET_ABBR.search(s):  # "12 Green St", "Blvd 7, apt 3"
        return True
    if str(key or "").lower() in ADDRESS_KEYS:
        # 'address' field: counts as an address only with a house number and several parts
        return has_num and len(s.split()) >= 2
    return False


# ------------------------------------------------ PEOPLE: name and birth ---
# A person is identified by first name and surname + date of birth (optional):
#   with the date    -> person:<normalised name>|YYYY-MM-DD   (unique node)
#   without the date -> name:<normalised name>
# The normalised name does not depend on order ("Rossi Mario" = "Mario Rossi").
# A name-only node is linked with a dashed line to the people with the same
# name and a date of birth (link_persons).
_BIRTH_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d")


def person_key(full):
    return " ".join(sorted(_fold(unicodedata.normalize("NFKC", str(full or ""))).split()))


def parse_birth(value):
    """'12/03/1980', '1980-03-12', '12.03.1980' -> '1980-03-12'; '' if empty."""
    v = re.sub(r"\s+", "", str(value or ""))
    if not v:
        return ""
    for fmt in _BIRTH_FORMATS:
        try:
            d = datetime.strptime(v, fmt)
        except ValueError:
            continue
        if not (1850 <= d.year <= datetime.now().year):
            break
        return d.strftime("%Y-%m-%d")
    raise NodeError("data di nascita non valida (es. 12/03/1980)")


SEX_WORDS = {
    "male": {"m", "male", "man", "maschio", "uomo", "masculin", "homme", "mannlich", "männlich",
             "mann", "masculino", "hombre", "ذكر"},
    "female": {"f", "female", "woman", "femmina", "donna", "feminin", "féminin", "femme",
               "weiblich", "frau", "femenino", "mujer", "w", "أنثى"},
}


def parse_sex(v):
    """'male', 'female' or '' (not known): the values of the Follow the Money
    gender property. Accepts M/F and the words of the interface languages."""
    w = str(v or "").strip().lower().rstrip(".")
    for sex, words in SEX_WORDS.items():
        if w in words:
            return sex
    return ""


def birth_it(iso):
    return f"{iso[8:10]}/{iso[5:7]}/{iso[0:4]}" if iso else ""


def person_id(full, birth=""):
    k = person_key(full)
    return f"person:{k}|{birth}" if birth else f"name:{k}"


def person_label(full, birth=""):
    full = re.sub(r"\s+", " ", str(full or "")).strip()
    return f"{full} ({birth_it(birth)})" if birth else full


def link_persons(g):
    """Dashed 'same name' link between a name-only node and the people with
    the same name and a date of birth."""
    datate, solo_nome = {}, {}
    for n in g["nodes"]:
        nid = n["id"]
        if nid.startswith("person:"):
            datate.setdefault(nid[len("person:"):].split("|")[0], []).append(nid)
        elif nid.startswith("name:"):
            solo_nome.setdefault(person_key(nid[len("name:"):]), []).append(nid)
    extra = []
    for k, nomi in solo_nome.items():
        for a in nomi:
            for b in datate.get(k, []):
                extra.append({"id": "pname-" + "-".join(sorted([_hash(a), _hash(b)])),
                              "source": a, "target": b, "rel": "stesso_nome",
                              "label": "stesso nome", "lstyle": "dashed", "auto": True})
    if extra:
        g = {"nodes": g["nodes"], "edges": g["edges"] + extra}
    return g


# ---------------------------------- ADDRESSES: city / street / house number ---
# Two places with the same city, street and house number are the SAME place (one
# node); same city and street but a different house number get a dashed link.
# The comparison uses a normalised form, so "Via S. Stefano nr. 55"
# and "via Santo Stefano 55" match.
_ABBR_VIA = [
    (r"v\.?\s*le", "viale"), (r"p\.?\s*zz?a", "piazza"), (r"p\.?\s*le", "piazzale"),
    (r"c\.?\s*so", "corso"), (r"l\.?\s*go", "largo"), (r"v\.?\s*lo", "vicolo"),
    (r"str", "strada"), (r"loc", "localita"), (r"fraz", "frazione"),
    (r"ss", "santissimo"), (r"st", "street"), (r"rd", "road"), (r"ave?", "avenue"),
    (r"blvd", "boulevard"), (r"sq", "square"), (r"v", "via"),
]
_ABBR_RE = [(re.compile(rf"^{a}(?:\.|\s|$)\s*", re.I), f"{b} ") for a, b in _ABBR_VIA]
# "S." / "S" / "San" / "Santo" / "Santa" before a name: they compare as equal
_SANTO_RE = re.compile(r"\b(s|ss|san|santo|santa|sant)\b\.?\s*'?\s*", re.I)
# house number at the end ("Via Roma 12", "Via Roma, n. 12/b") or at the start ("12 Main St")
_CIVICO_FINE = re.compile(
    r"^(.*?\D)[\s,]*(?:\b(?:n|nr|no|num|numero|civico)\b\.?\s*)?"
    r"(\d{1,5}(?:\s*[/-]?\s*[a-z]\b|\s*/\s*\d{1,4})?)\s*$", re.I)
_CIVICO_INIZIO = re.compile(r"^(\d{1,5}[a-z]?)[\s,]+(\D.*)$", re.I)


_LATIN_DIACRITICS = _rx.compile(r"[\u0300-\u036F]")   # only Latin/Cyrillic/Greek diacritics


def _fold(s):
    """Lower case, no Latin accents, collapsed spaces. The combining marks of
    Indic, Thai and Japanese scripts (vowel signs, virama, dakuten) are part of
    the word and stay: removing them broke names apart and mixed them up."""
    s = unicodedata.normalize("NFKD", str(s or "")).casefold()
    s = _LATIN_DIACRITICS.sub("", s)
    s = unicodedata.normalize("NFC", s)
    s = _rx.sub(r"[^\p{L}\p{M}\p{N}_/]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def split_civico(address):
    """'Via Santo Stefano, nr. 55' -> ('Via Santo Stefano', '55')."""
    a = re.sub(r"\s+", " ", str(address or "")).strip(" ,")
    if not a:
        return "", ""
    m = _CIVICO_FINE.match(a)
    if m and re.search(r"[^\W\d_]", m.group(1)):
        return m.group(1).strip(" ,"), re.sub(r"\s+", "", m.group(2))
    m = _CIVICO_INIZIO.match(a)
    if m:
        return m.group(2).strip(" ,"), m.group(1)
    return a, ""


# Street types: in the form they are picked from the drop-down and do NOT count in
# the comparison, so "Via Giacomo Leopardi" and "Giacomo Leopardi" are the same street.
STREET_TYPES = [
    "via", "viale", "piazza", "piazzale", "piazzetta", "corso", "largo", "vicolo",
    "vico", "strada", "stradone", "contrada", "localita", "frazione", "borgo",
    "lungomare", "lungolago", "lungofiume", "salita", "discesa", "traversa",
    "galleria", "rotonda", "circonvallazione", "passaggio", "calle", "rue",
    "avenue", "boulevard", "avenida", "carrera", "plaza", "street", "road",
    "lane", "drive", "square", "way", "place", "court",
]
_TYPE_HEAD = re.compile(r"^(?:%s)\b\s*" % "|".join(STREET_TYPES))
_TYPE_TAIL = re.compile(r"\s*\b(?:street|road|avenue|lane|drive|square|way|place|"
                        r"court|boulevard)$")


def norm_street(street):
    """Comparison key of a street: abbreviations expanded, 'S.' = 'San',
    without the street type (via, piazza, street...), which does not count."""
    s = re.sub(r"\s+", " ", str(street or "")).strip()
    for rx, full in _ABBR_RE:
        if rx.match(s):
            s = rx.sub(full, s, count=1)
            break
    s = _SANTO_RE.sub("san ", s)
    s = _fold(s)
    nome = _TYPE_TAIL.sub("", _TYPE_HEAD.sub("", s)).strip()
    return nome or s                       # "Piazza" on its own stays as it is


def _initials(street_key):
    return sum(1 for w in street_key.split() if len(w) == 1 and w.isalpha())


def streets_match(a, b):
    """Same street up to initials: 'g leopardi' ~ 'giacomo leopardi'."""
    wa, wb = a.split(), b.split()
    if len(wa) != len(wb):
        return False
    for x, y in zip(wa, wb):
        if x == y:
            continue
        if len(x) == 1 and x.isalpha() and y.startswith(x):
            continue
        if len(y) == 1 and y.isalpha() and x.startswith(y):
            continue
        return False
    return True


def canon_streets(keys):
    """{(city, street): canonical street} for a set of (city, street) keys.
    A street with initials ('g leopardi') becomes the compatible full street
    of the same city ('giacomo leopardi'), but only if that one is UNIQUE:
    with 'giacomo leopardi' and 'giovanni leopardi' the initial stays as it is."""
    per_city = {}
    for c, s in keys:
        per_city.setdefault(c, set()).add(s)
    out = {}
    for c, streets in per_city.items():
        for s in streets:
            out[(c, s)] = s
            if not _initials(s):
                continue
            cand = [f for f in streets if f != s and _initials(f) < _initials(s)
                    and streets_match(s, f)]
            best = [f for f in cand if _initials(f) == min(_initials(x) for x in cand)] if cand else []
            if len(best) == 1:
                out[(c, s)] = best[0]
    return out


def norm_civico(civico):
    return re.sub(r"[^0-9a-z/]", "", _fold(civico))


def norm_city(city):
    # postcode and province code are removed: "25100 Brescia (BS)" -> "brescia"
    c = re.sub(r"\(\s*[A-Za-z]{2}\s*\)|\b\d{4,6}\b", " ", str(city or ""))
    return _fold(c)


def place_parts(node):
    """(city, street, house number) of a place node, None if it has no street.
    Nodes added by hand: fields citta/indirizzo/civico. Nodes from the data:
    free label 'Via Roma 12, Brescia' (or 'Brescia — Via Roma 12')."""
    raw = {}
    for r in node.get("records") or []:
        if isinstance(r.get("raw"), dict) and r.get("collection") == "aggiunto a mano":
            raw = r["raw"]
            break
    city, addr, civ = raw.get("citta"), raw.get("indirizzo"), raw.get("civico")
    if not city:
        parts = [p.strip() for p in re.split(r"\s+[—–]\s+|,", str(node.get("label") or ""))
                 if p.strip()]
        # the street: the part with an address word (via, piazza, street...)
        via = next((p for p in parts if STREET_RE.search(" " + p + " ")), "")
        if not via:
            return None
        # the city: the first other part that, once the postcode is removed, has no digits
        altri = [re.sub(r"\b\d{4,6}\b", "", p).strip() for p in parts if p != via]
        city = next((p for p in altri if p and not re.search(r"\d", p)), "")
        addr = via
    if not addr:
        return None
    street, c2 = split_civico(addr)
    civ = civ or c2
    return norm_city(city), norm_street(street), norm_civico(civ)


def merge_places(g):
    """Merges the places with the same city, street and house number and links
    with a dashed line those with the same city and street but another number."""
    parts = {}
    for n in g["nodes"]:
        if n.get("ntype") == "place":
            p = place_parts(n)
            if p and p[0] and p[1]:
                parts[n["id"]] = p
    if not parts:
        return g
    # 'Via G. Leopardi' and 'Via Giacomo Leopardi' in the same city: same street
    canon = canon_streets({(c, s) for c, s, _ in parts.values()})
    parts = {nid: (c, canon[(c, s)], v) for nid, (c, s, v) in parts.items()}

    # 1) same full address -> a single node
    full = {}
    for nid, (c, s, v) in parts.items():
        if v:
            full.setdefault((c, s, v), []).append(nid)
    alias = {}
    by_id = {n["id"]: n for n in g["nodes"]}
    for ids in full.values():
        if len(ids) < 2:
            continue
        # the node that stays must be STABLE (notes, positions and links are
        # tied to its id): first the one from the data, then an original entry
        # (not an added card, id with '~'), then the oldest
        def _at(i):
            recs = by_id[i].get("records") or [{}]
            return str((recs[0].get("raw") or {}).get("aggiunto_il") or "")
        ids.sort(key=lambda i: (bool(by_id[i].get("manual")), "~" in i,
                                -len(by_id[i].get("records") or []), _at(i),
                                -len(_flat(by_id[i].get("label"))), i))
        canon = dict(by_id[ids[0]])
        canon["records"] = list(canon.get("records") or [])
        canon["sources"] = list(canon.get("sources") or [])
        canon["aliases"] = list(canon.get("aliases") or [])
        canon["alias_ids"] = list(canon.get("alias_ids") or [])
        for other in ids[1:]:
            o = by_id[other]
            alias[other] = canon["id"]
            canon["records"].extend(o.get("records") or [])
            for s_ in o.get("sources") or []:
                if s_ not in canon["sources"]:
                    canon["sources"].append(s_)
            lab = _flat(o.get("label"))
            if lab and lab.casefold() != _flat(canon.get("label")).casefold() \
                    and lab not in canon["aliases"]:
                canon["aliases"].append(lab)
            canon["alias_ids"] += [other] + list(o.get("alias_ids") or [])
            if not canon.get("note") and o.get("note"):
                canon["note"] = o["note"]
            for k in ("lat", "lon", "url"):
                if not canon.get(k) and o.get(k):
                    canon[k] = o[k]
        canon["merged"] = sum(by_id[i].get("merged") or 1 for i in ids)
        canon["cards"] = len(canon["records"])
        by_id[canon["id"]] = canon

    nodes = [by_id[n["id"]] for n in g["nodes"] if n["id"] not in alias]
    edges, seen = [], set()
    for e in g["edges"]:
        s, t = alias.get(e["source"], e["source"]), alias.get(e["target"], e["target"])
        if s == t:
            continue
        if s != e["source"] or t != e["target"]:
            e = dict(e, source=s, target=t)
        key = (e["id"], s, t)
        if key in seen:
            continue
        seen.add(key)
        edges.append(e)

    # 2) same city and same street, different house number -> dashed link
    streets = {}
    for nid, (c, s, v) in parts.items():
        if nid in alias:
            continue
        streets.setdefault((c, s), {}).setdefault(v, nid)   # one node per house number
    for group in streets.values():
        ids = [group[v] for v in sorted(group, key=lambda x: (len(x), x))]
        if len(ids) < 2:
            continue
        # up to 6 house numbers all with all, beyond that a chain in house-number order
        pairs = ([(a, b) for i, a in enumerate(ids) for b in ids[i + 1:]]
                 if len(ids) <= 6 else list(zip(ids, ids[1:])))
        for a, b in pairs:
            edges.append({"id": "street-" + "-".join(sorted([_hash(a), _hash(b)])),
                          "source": a, "target": b, "rel": "stessa_via",
                          "label": "stessa via", "lstyle": "dashed", "auto": True})
    return {"nodes": nodes, "edges": edges}


# labels that in address books are not personal names
NAME_STOP = {
    "unknown", "sconosciuto", "no name", "noname", "null", "none", "n/a", "na",
    "spam", "telemarketing", "private", "privato", "anonimo", "anonymous",
    "mobile", "cellulare", "telefono", "phone", "number", "numero", "contact",
    "contatto", "user", "utente", "business", "azienda", "customer service",
}
