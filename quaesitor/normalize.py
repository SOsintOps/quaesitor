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


# ---------------------------------------------------------------- LUOGHI ---
# Chiavi che contengono un luogo vero (città, indirizzo, provenienza).
PLACE_KEYS = {"location", "locations", "address", "addresses", "last_address",
              "hometown", "city", "town", "street", "birthplace", "residence"}
# Sottoalberi da NON esplorare: contengono il paese dell'OPERATORE telefonico,
# non del soggetto. Compare in centinaia di schede e creerebbe un nodo unico
# collegato a tutto (es. «Libyan Arab Jamahiriya»), inutile e fuorviante.
PLACE_SKIP_SUBTREE = {"original_network_details", "current_network_details",
                      "network_details", "sea", "seacomcousub", "seawik",
                      "cheact", "gcon", "raw"}
# valori che sembrano luoghi ma non lo sono
PLACE_STOP = {"true", "false", "none", "null", "n/a", "na", "unknown",
              "available", "not_applicable", "home", "work", "other"}
# Sottoinsieme di PLACE_KEYS che contiene un recapito preciso (non una citta).
ADDRESS_KEYS = {"address", "addresses", "last_address", "street", "residence"}
# Parole che rivelano un indirizzo vero e proprio (via, civico, palazzina...).
# Solo parole intere e non ambigue: le sigle (st, rd, dr...) sono in STREET_ABBR
# perche' da sole comparirebbero anche in nomi di citta' ("St. Petersburg").
STREET_RE = re.compile(
    r"(?i)(?:^|[\s,.-])(via|viale|vicolo|piazza|piazzale|corso|largo|strada|"
    r"contrada|borgo|street|road|avenue|boulevard|lane|drive|square|highway|"
    r"route|rue|calle|avenida|carrera|strasse|straße|platz|sharia|tariq|"
    r"zanqat|zenkat|block|building|apartment|floor|interno|civico|piano)"
    r"(?:[\s,.]|$)")
# Sigle di indirizzo: valgono solo se nell'etichetta c'e' anche un numero civico.
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
    if la == 0 and lo == 0:                       # coordinata nulla: non è un luogo
        return None
    return f"{la:.6f}".rstrip("0").rstrip("."), f"{lo:.6f}".rstrip("0").rstrip(".")


def collect_places(o, out=None, key=""):
    """Estrae dai dati grezzi di una scheda i luoghi citati.
    Ritorna una lista di {'label': ..., 'lat': ..., 'lon': ...} senza duplicati."""
    if out is None:
        out = []
    if isinstance(o, dict):
        # un oggetto con latitudine e longitudine è un luogo, con la sua etichetta
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
    """True se il luogo e' un RECAPITO (indirizzo o punto sulla mappa), non una
    generica citta/regione. Solo un recapito puo' collegare fra loro schede
    diverse: "Tripoli" o "Libya" ricorrono in centinaia di schede e creerebbero
    un nodo-calamita che unisce persone che non c'entrano nulla."""
    if lat and lon:                       # un punto sulla mappa e' gia' preciso
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
        # campo 'address': vale come recapito solo se ha un civico e piu' parti
        return has_num and len(s.split()) >= 2
    return False


# ------------------------------------------------ PERSONE: nome e nascita ---
# Una persona e' identificata da nome e cognome + data di nascita (facoltativa):
#   con la data   -> person:<nome normalizzato>|AAAA-MM-GG   (nodo univoco)
#   senza la data -> name:<nome normalizzato>
# Il nome normalizzato non dipende dall'ordine ("Rossi Mario" = "Mario Rossi").
# Un nodo con il solo nome si collega con un tratteggio alle persone con lo
# stesso nome e una data di nascita (link_persons).
_BIRTH_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d")


def person_key(full):
    return " ".join(sorted(_fold(unicodedata.normalize("NFKC", str(full or ""))).split()))


def parse_birth(value):
    """'12/03/1980', '1980-03-12', '12.03.1980' -> '1980-03-12'; '' se vuota."""
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


def birth_it(iso):
    return f"{iso[8:10]}/{iso[5:7]}/{iso[0:4]}" if iso else ""


def person_id(full, birth=""):
    k = person_key(full)
    return f"person:{k}|{birth}" if birth else f"name:{k}"


def person_label(full, birth=""):
    full = re.sub(r"\s+", " ", str(full or "")).strip()
    return f"{full} ({birth_it(birth)})" if birth else full


def link_persons(g):
    """Tratteggio 'stesso nome' fra un nodo con il solo nome e le persone con
    lo stesso nome e una data di nascita."""
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


# ------------------------------------------- INDIRIZZI: citta' / via / civico ---
# Due luoghi con citta', via e civico uguali sono lo STESSO luogo (un nodo solo);
# con citta' e via uguali ma civico diverso si collegano con un tratteggio.
# Il confronto si fa su una forma normalizzata, cosi' "Via S. Stefano nr. 55"
# e "via Santo Stefano 55" coincidono.
_ABBR_VIA = [
    (r"v\.?\s*le", "viale"), (r"p\.?\s*zz?a", "piazza"), (r"p\.?\s*le", "piazzale"),
    (r"c\.?\s*so", "corso"), (r"l\.?\s*go", "largo"), (r"v\.?\s*lo", "vicolo"),
    (r"str", "strada"), (r"loc", "localita"), (r"fraz", "frazione"),
    (r"ss", "santissimo"), (r"st", "street"), (r"rd", "road"), (r"ave?", "avenue"),
    (r"blvd", "boulevard"), (r"sq", "square"), (r"v", "via"),
]
_ABBR_RE = [(re.compile(rf"^{a}(?:\.|\s|$)\s*", re.I), f"{b} ") for a, b in _ABBR_VIA]
# "S." / "S" / "San" / "Santo" / "Santa" davanti a un nome: si confrontano uguali
_SANTO_RE = re.compile(r"\b(s|ss|san|santo|santa|sant)\b\.?\s*'?\s*", re.I)
# civico in fondo ("Via Roma 12", "Via Roma, n. 12/b") o in testa ("12 Main St")
_CIVICO_FINE = re.compile(
    r"^(.*?\D)[\s,]*(?:\b(?:n|nr|no|num|numero|civico)\b\.?\s*)?"
    r"(\d{1,5}(?:\s*[/-]?\s*[a-z]\b|\s*/\s*\d{1,4})?)\s*$", re.I)
_CIVICO_INIZIO = re.compile(r"^(\d{1,5}[a-z]?)[\s,]+(\D.*)$", re.I)


_LATIN_DIACRITICS = _rx.compile(r"[\u0300-\u036F]")   # solo i diacritici latini/cirillici/greci


def _fold(s):
    """minuscole, senza accenti latini, spazi compattati. I segni combinanti
    delle scritture indiane, thai e giapponese (vocali, virama, dakuten) sono
    parte della parola e restano: toglierli spezzava e confondeva i nomi."""
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


# Tipi di via (toponimi): nel modulo si scelgono dalla tendina e NON contano nel
# confronto, cosi' "Via Giacomo Leopardi" e "Giacomo Leopardi" sono la stessa via.
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
    """Chiave di confronto di una via: abbreviazioni sciolte, 'S.' = 'San',
    senza il tipo di via (via, piazza, street...), che non conta."""
    s = re.sub(r"\s+", " ", str(street or "")).strip()
    for rx, full in _ABBR_RE:
        if rx.match(s):
            s = rx.sub(full, s, count=1)
            break
    s = _SANTO_RE.sub("san ", s)
    s = _fold(s)
    nome = _TYPE_TAIL.sub("", _TYPE_HEAD.sub("", s)).strip()
    return nome or s                       # "Piazza" da sola resta com'e'


def _initials(street_key):
    return sum(1 for w in street_key.split() if len(w) == 1 and w.isalpha())


def streets_match(a, b):
    """Stessa via a meno delle iniziali: 'g leopardi' ~ 'giacomo leopardi'."""
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
    """{(citta', via): via canonica} per un insieme di chiavi (citta', via).
    Una via con iniziali ('g leopardi') diventa la via completa compatibile
    della stessa citta' ('giacomo leopardi'), ma solo se questa e' UNICA:
    con 'giacomo leopardi' e 'giovanni leopardi' l'iniziale resta com'e'."""
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
    # si tolgono CAP e sigla di provincia: "25100 Brescia (BS)" -> "brescia"
    c = re.sub(r"\(\s*[A-Za-z]{2}\s*\)|\b\d{4,6}\b", " ", str(city or ""))
    return _fold(c)


def place_parts(node):
    """(citta', via, civico) di un nodo luogo, None se non ha una via.
    Nodi aggiunti a mano: campi citta'/indirizzo/civico. Nodi dai dati:
    etichetta libera 'Via Roma 12, Brescia' (o 'Brescia — Via Roma 12')."""
    raw = {}
    for r in node.get("records") or []:
        if isinstance(r.get("raw"), dict) and r.get("collection") == "aggiunto a mano":
            raw = r["raw"]
            break
    city, addr, civ = raw.get("citta"), raw.get("indirizzo"), raw.get("civico")
    if not city:
        parts = [p.strip() for p in re.split(r"\s+[—–]\s+|,", str(node.get("label") or ""))
                 if p.strip()]
        # la via: la parte con una parola da indirizzo (via, piazza, street...)
        via = next((p for p in parts if STREET_RE.search(" " + p + " ")), "")
        if not via:
            return None
        # la citta': la prima altra parte che, tolto il CAP, non ha numeri
        altri = [re.sub(r"\b\d{4,6}\b", "", p).strip() for p in parts if p != via]
        city = next((p for p in altri if p and not re.search(r"\d", p)), "")
        addr = via
    if not addr:
        return None
    street, c2 = split_civico(addr)
    civ = civ or c2
    return norm_city(city), norm_street(street), norm_civico(civ)


def merge_places(g):
    """Unisce i luoghi con citta', via e civico uguali e collega con un
    tratteggio quelli con citta' e via uguali ma civico diverso."""
    parts = {}
    for n in g["nodes"]:
        if n.get("ntype") == "place":
            p = place_parts(n)
            if p and p[0] and p[1]:
                parts[n["id"]] = p
    if not parts:
        return g
    # 'Via G. Leopardi' e 'Via Giacomo Leopardi' della stessa citta': stessa via
    canon = canon_streets({(c, s) for c, s, _ in parts.values()})
    parts = {nid: (c, canon[(c, s)], v) for nid, (c, s, v) in parts.items()}

    # 1) stesso indirizzo completo -> un nodo solo
    full = {}
    for nid, (c, s, v) in parts.items():
        if v:
            full.setdefault((c, s, v), []).append(nid)
    alias = {}
    by_id = {n["id"]: n for n in g["nodes"]}
    for ids in full.values():
        if len(ids) < 2:
            continue
        # il nodo che resta deve essere STABILE (le note, le posizioni e i
        # collegamenti sono legati al suo id): prima quello dei dati, poi una
        # voce originale (non una scheda aggiunta, id con '~'), poi la piu' vecchia
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

    # 2) stessa citta' e stessa via, civico diverso -> tratteggio
    streets = {}
    for nid, (c, s, v) in parts.items():
        if nid in alias:
            continue
        streets.setdefault((c, s), {}).setdefault(v, nid)   # un nodo per civico
    for group in streets.values():
        ids = [group[v] for v in sorted(group, key=lambda x: (len(x), x))]
        if len(ids) < 2:
            continue
        # fino a 6 civici tutti con tutti, oltre una catena in ordine di civico
        pairs = ([(a, b) for i, a in enumerate(ids) for b in ids[i + 1:]]
                 if len(ids) <= 6 else list(zip(ids, ids[1:])))
        for a, b in pairs:
            edges.append({"id": "street-" + "-".join(sorted([_hash(a), _hash(b)])),
                          "source": a, "target": b, "rel": "stessa_via",
                          "label": "stessa via", "lstyle": "dashed", "auto": True})
    return {"nodes": nodes, "edges": edges}


# etichette che nelle rubriche non sono nomi di persona
NAME_STOP = {
    "unknown", "sconosciuto", "no name", "noname", "null", "none", "n/a", "na",
    "spam", "telemarketing", "private", "privato", "anonimo", "anonymous",
    "mobile", "cellulare", "telefono", "phone", "number", "numero", "contact",
    "contatto", "user", "utente", "business", "azienda", "customer service",
}
