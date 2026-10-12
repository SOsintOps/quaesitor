# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

# "Homo sum, humani nihil a me alienum puto." (Terence, Heauton Timorumenos)
# I am human: nothing human is alien to me.
import json
import os
import threading
import re
import sys
import hashlib
import logging
import time
import unicodedata
import urllib.error
import urllib.request
import uuid
import regex as _rx                 # \p{L}\p{M}: lettere e segni combinanti di ogni scrittura
from datetime import datetime
from urllib.parse import quote
from flask import (Flask, jsonify, render_template, request,
                   send_from_directory, abort, stream_with_context)

logging.basicConfig(level=logging.INFO)

if getattr(sys, "frozen", False):
    # Eseguibile PyInstaller (onefile):
    #  - le RISORSE dell'app (templates, static) sono estratte in sys._MEIPASS;
    #  - i DATI dell'utente (data/, chatbot.conf, annotations) stanno ACCANTO
    #    all'eseguibile, così restano esterni, modificabili e persistenti.
    RES_DIR = sys._MEIPASS
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    RES_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = RES_DIR

app = Flask(
    __name__,
    template_folder=os.path.join(RES_DIR, "templates"),
    static_folder=os.path.join(RES_DIR, "static"),
)

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))

IMG_KEYS = ("pic", "photo", "avatar", "image", "img")
IMG_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif)(\?|$)", re.I)
PHOTO_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff")
# sottocartella di DATA_DIR con le immagini caricate a mano: non è un target
MEDIA_DIRNAME = "media"
URL_RE = re.compile(r"^https?://", re.I)

PLATFORM_TABLE = {
    "instagram": "instagram", "threads": "threads", "snapchat": "snapchat",
    "facebook": "facebook", "google": "google", "discord": "discord",
    "microsoft": "microsoft", "apple": "apple", "amazon": "amazon",
    "tiktok": "tiktok", "linkedin": "linkedin", "github": "github",
    "vkontakte": "vk", "airbnb": "airbnb", "zynga": "zynga", "yahoo": "yahoo",
    "telegram": "telegram", "whatsapp": "whatsapp", "spotify": "spotify",
    "x": "x", "twitter": "x", "fotostrana": "generic",
    "people data labs": "generic", "cuitonline": "generic",
    "naz.api": "breach", "domain whois history": "domain",
}
PHONE_SRC = {"callapp", "showcaller", "hlrlookup", "callerid", "truecaller"}

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

# ==================== ROMANIZZAZIONE ====================
# Scritture "ambigue": abjad senza vocali brevi. Nessun motore automatico può
# restituire un nome leggibile (محمد = m-h-m-d), servono i dizionari manuali.
AMBIGUOUS_SCRIPTS = {"ARABIC", "HEBREW", "SYRIAC", "THAANA", "CJK"}   # CJK: lettura dei kanji ambigua

WORD_RE = _rx.compile(r"[\p{L}\p{M}]+")   # lettere + segni combinanti (devanagari, thai, kana con dakuten)

try:                                    # PyICU: qualità migliore, tutti gli alfabeti
    import icu
    _ICU = icu.Transliterator.createInstance("Any-Latin; Latin-ASCII")
    _romanize_raw = _ICU.transliterate
    TRANSLIT_ENGINE = "icu"
except Exception:                       # fallback puro Python
    try:
        from anyascii import anyascii as _romanize_raw
        TRANSLIT_ENGINE = "anyascii"
    except Exception:
        _romanize_raw = None
        TRANSLIT_ENGINE = None

# alfabeti non occidentali riconosciuti (prefisso del nome Unicode del carattere)
SCRIPTS = (
    "CYRILLIC", "ARABIC", "GREEK", "HEBREW", "HIRAGANA", "KATAKANA", "HANGUL",
    "THAI", "DEVANAGARI", "ARMENIAN", "GEORGIAN", "BENGALI", "GUJARATI",
    "GURMUKHI", "TAMIL", "TELUGU", "KANNADA", "MALAYALAM", "SINHALA",
    "ETHIOPIC", "KHMER", "LAO", "MYANMAR", "TIBETAN", "SYRIAC", "THAANA",
    "CJK", "IDEOGRAPH", "BOPOMOFO", "MONGOLIAN", "CHEROKEE",
)


def script_of(text):
    """Alfabeto dominante di una stringa, None se è già latina/neutra."""
    counts = {}
    letters = 0
    for ch in str(text or ""):
        if not ch.isalpha():
            continue
        letters += 1
        try:
            name = unicodedata.name(ch)
        except ValueError:
            continue
        if name.startswith("LATIN"):
            counts["LATIN"] = counts.get("LATIN", 0) + 1
            continue
        for s in SCRIPTS:
            if name.startswith(s):
                key = "CJK" if s in ("CJK", "IDEOGRAPH") else s
                counts[key] = counts.get(key, 0) + 1
                break
    if not letters:
        return None
    best = max(((k, v) for k, v in counts.items() if k != "LATIN"),
               key=lambda kv: kv[1], default=None)
    if not best or best[1] / letters < 0.3:
        return None
    return best[0]


# ---------- dizionario di traslitterazione (tabella 'translit' di SQLite) ----------
# Ogni parola ha una sola riga: 'manual' (scritta a mano, vince sempre),
# 'ai' (proposta dal chatbot) o 'pending' (nota ma ancora da tradurre).
def load_word_dict():
    """{parola originale: traslitterazione}; '' = da tradurre."""
    return store.translit_dict()


def write_pending(pending):
    """Parole nuove, da tradurre (a mano o con l'AI)."""
    n = store.translit_add_pending(sorted(pending or []), script_of)
    if n:
        logging.info(f"{n} parole da traslitterare aggiunte al dizionario")
    return n


# ==================== CHATBOT REMOTO (AI) ====================
# Chatbot dell'utente (Ollama dietro un reverse proxy). Serve a compilare da
# solo il dizionario di traslitterazione: le scritture senza vocali brevi
# (arabo, ebraico...) non sono traducibili da un motore automatico.
# REGOLA: se il chatbot non risponde NON succede nulla. Si prosegue con il
# dizionario compilato a mano e la traslitterazione automatica di sempre.
CHATBOT_CONF = os.path.join(BASE_DIR, "chatbot.conf")
CHATBOT_DEFAULTS = {
    "enabled": "true", "endpoint": "", "api_key": "", "model": "gemma3:12b",
    "timeout": "25", "auth_header": "Authorization", "auth_prefix": "Bearer",
    "api": "auto", "auto": "true", "max_words": "120", "batch": "15",
    "budget": "60",
}


def _load_chatbot_conf():
    """chatbot.conf (chiave = valore) + variabili d'ambiente CHATBOT_*."""
    conf = dict(CHATBOT_DEFAULTS)
    try:
        with open(CHATBOT_CONF, "r", encoding="utf-8-sig") as f:
            for riga in f:
                riga = riga.strip()
                if not riga or riga.startswith("#"):
                    continue
                k, sep, v = riga.partition("=")
                if sep:
                    conf[k.strip().lower()] = v.strip()
    except FileNotFoundError:
        pass
    except Exception as e:
        logging.error(f"chatbot.conf illeggibile: {e}")
    for k in list(conf):
        env = os.environ.get("CHATBOT_" + k.upper())
        if env is not None:
            conf[k] = env
    # Un solo interruttore: 'enabled' (lo switch "AI attiva" dell'app). Spento
    # = il chatbot non viene mai contattato, per nessuna funzione.
    conf["endpoint"] = conf["endpoint"].rstrip("/")
    for k, minimo in (("timeout", 1), ("max_words", 1), ("batch", 1), ("budget", 5)):
        try:
            conf[k] = max(minimo, int(float(conf[k])))
        except (TypeError, ValueError):
            conf[k] = int(CHATBOT_DEFAULTS[k])
    for k in ("enabled", "auto"):
        conf[k] = str(conf[k]).strip().lower() in ("1", "true", "si", "yes", "on")
    return conf


CHATBOT = _load_chatbot_conf()

# stato in memoria: quale formato di API funziona e da quando il chatbot e'
# considerato irraggiungibile (per non riprovare a ogni ricostruzione)
BOT_RETRY_AFTER = 300              # secondi di attesa dopo un tentativo fallito
_bot = {"api": None, "down_until": 0.0, "reason": "", "ok_at": 0.0}


def chatbot_ready():
    """Il chatbot si puo' usare: interruttore acceso ed endpoint impostato.
    Da spento non si tenta nessun collegamento."""
    return bool(CHATBOT["enabled"] and CHATBOT["endpoint"])


def _bot_call(path, payload):
    """POST JSON al chatbot. Ritorna (dati, errore): uno dei due e' sempre None."""
    url = CHATBOT["endpoint"] + path
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    testa = (CHATBOT["auth_header"] or "").strip()
    if testa and CHATBOT["api_key"]:
        pre = (CHATBOT["auth_prefix"] or "").strip()
        req.add_header(testa, (pre + " " if pre else "") + CHATBOT["api_key"])
    try:
        with urllib.request.urlopen(req, timeout=CHATBOT["timeout"]) as r:
            return json.loads(r.read().decode("utf-8", "replace")), None
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace").strip()[:120]
        except Exception:
            pass
        return None, f"HTTP {e.code} {e.reason}" + (f" - {detail}" if detail else "")
    except urllib.error.URLError as e:
        return None, f"{e.reason}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


PROBE_TIMEOUT = 5
AI_NUM_CTX = 8192                      # finestra di contesto chiesta a Ollama (token)                      # come il CONNECTTIMEOUT del client PHP


def chatbot_probe():
    """Colpo di sonda veloce: il SERVER risponde? Serve solo a non far
    aspettare il timeout pieno quando la macchina e' spenta o irraggiungibile.
    Un 401 NON conta come guasto: il proxy puo' proteggere /api/tags e lasciare
    passare /api/generate, che e' la rotta che ci interessa davvero.
    Ritorna (raggiungibile, motivo)."""
    url = CHATBOT["endpoint"] + "/api/tags"
    req = urllib.request.Request(url, method="GET")
    testa = (CHATBOT["auth_header"] or "").strip()
    if testa and CHATBOT["api_key"]:
        pre = (CHATBOT["auth_prefix"] or "").strip()
        req.add_header(testa, (pre + " " if pre else "") + CHATBOT["api_key"])
    try:
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as r:
            r.read(1)
            return True, ""
    except urllib.error.HTTPError:
        return True, ""                    # ha risposto: si prova la generazione
    except urllib.error.URLError as e:
        return False, f"{e.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _bot_down(motivo):
    _bot["down_until"] = time.time() + BOT_RETRY_AFTER
    _bot["reason"] = motivo
    logging.warning(f"Chatbot non raggiungibile ({motivo}): "
                    f"si prosegue senza, riprovo fra {BOT_RETRY_AFTER}s")


def chatbot_ask(prompt, force=False, json_mode=False, ignore_switch=False):
    """Manda un prompt al chatbot. Ritorna il testo, oppure None se il chatbot
    non risponde: in quel caso il chiamante DEVE proseguire senza.
    ignore_switch=True (prova di collegamento dal pannello): basta l'endpoint.
    json_mode: chiede a Ollama una risposta in JSON valido."""
    if ignore_switch:
        if not CHATBOT["endpoint"]:
            return None
    elif not chatbot_ready():
        return None
    if not force and time.time() < _bot["down_until"]:
        return None

    forme = ["ollama", "openai"] if CHATBOT["api"] == "auto" else [CHATBOT["api"]]
    if _bot["api"] in forme:                     # quella che ha gia' funzionato
        forme = [_bot["api"]]
    ultimo = ""
    for forma in forme:
        if forma == "openai":
            dati, err = _bot_call("/v1/chat/completions", {
                "model": CHATBOT["model"], "temperature": 0, "stream": False,
                "messages": [{"role": "user", "content": prompt}]})
            testo = ""
            if dati:
                try:
                    testo = dati["choices"][0]["message"]["content"]
                except Exception:
                    testo = ""
        else:
            # num_ctx: il prompt dei nodi (con gli elenchi di armi, sostanze,
            # reati...) supera la finestra predefinita di Ollama (2-4k token), che
            # altrimenti lo troncherebbe in silenzio
            req = {"model": CHATBOT["model"], "prompt": prompt, "stream": False,
                   "options": {"temperature": 0, "num_ctx": AI_NUM_CTX}}
            if json_mode:
                req["format"] = "json"
            dati, err = _bot_call("/api/generate", req)
            testo = (dati or {}).get("response") or ""
        if err:
            ultimo = err
            if err.startswith(("HTTP 401", "HTTP 403")):
                break                            # la chiave e' sbagliata: inutile insistere
            if not err.startswith("HTTP"):
                break                            # server irraggiungibile: vale per ogni formato
            continue
        if testo:
            _bot["api"] = forma
            _bot["down_until"] = 0.0
            _bot["reason"] = ""
            _bot["ok_at"] = time.time()
            return testo
        ultimo = "risposta vuota"
    _bot_down(ultimo or "nessuna risposta")
    return None


# ---------- traslitterazione con il chatbot ----------
# La risposta del modello e' un DATO, non un comando: se ne prende solo il
# testo latino e si scarta tutto il resto (istruzioni, spiegazioni, markup).
LATIN_OUT = re.compile(r"^[A-Za-z][A-Za-z0-9 '\-.]{0,79}$")

TRANSLIT_PROMPT = (
    "Transliterate each word into the Latin alphabet.\n"
    "Rules:\n"
    "- Reply with a JSON object only, nothing else.\n"
    "- One key for every input word, written exactly as given.\n"
    "- The value is the usual English romanization of the word "
    "(personal names: e.g. Mohamed, Ali, Al-Sharif).\n"
    "- Plain ASCII letters only: no diacritics, no scholarly marks "
    "(write Muhammad, not Muḥammad; Antani, not ʿAntānī).\n"
    "- Do not translate the meaning, do not add comments or extra keys.\n"
    "Words: {parole}"
)


def _pulisci_translit(valore):
    """Tiene solo una traslitterazione plausibile: testo latino, breve."""
    v = re.sub(r"\s+", " ", str(valore or "")).strip().strip('"\'')
    v = "".join(c for c in v if c.isprintable())
    if script_of(v):                       # contiene ancora caratteri non latini
        return ""
    # i modelli usano spesso la trascrizione accademica (Muḥammad, ʿAntānī):
    # si tolgono diacritici e segni invece di scartare la parola
    v = _clean(v)
    if not v or not LATIN_OUT.match(v):
        return ""
    if script_of(v):                       # contiene ancora caratteri non latini
        return ""
    return v


def _estrai_json(testo):
    """Il primo oggetto JSON contenuto nella risposta (i modelli aggiungono
    spesso ``` o una frase di cortesia)."""
    t = str(testo or "")
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return {}
    try:
        d = json.loads(t[i:j + 1])
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def chatbot_translit(parole):
    """{parola: forma latina} per le parole che il chatbot sa tradurre."""
    parole = [p for p in parole if p]
    if not parole or not chatbot_ready():
        return {}
    prompt = TRANSLIT_PROMPT.format(parole=json.dumps(parole, ensure_ascii=False))
    risposta = chatbot_ask(prompt)
    if not risposta:
        return {}
    grezzo = _estrai_json(risposta)
    fuori = {}
    for k, v in grezzo.items():
        if k in parole:                     # solo le parole chieste
            val = _pulisci_translit(v)
            if val:
                fuori[k] = val
    if not fuori:
        logging.warning("Chatbot: risposta senza traslitterazioni utilizzabili: "
                        + re.sub(r"\s+", " ", risposta)[:200])
    return fuori


def save_ai_translit(nuove):
    """Salva le parole tradotte dal chatbot; una traduzione fatta a mano
    ha sempre la precedenza e non viene sovrascritta."""
    try:
        return store.translit_save_ai(nuove, CHATBOT["model"])
    except Exception as e:
        logging.error(f"Impossibile salvare le traslitterazioni: {e}")
        return 0


def _per_ai(w):
    """La parola va fatta tradurre all'AI? Con l'AI attiva: qualunque alfabeto
    non latino (e' piu' precisa del motore locale); senza, solo le scritture
    ambigue, che finiscono nel dizionario da compilare a mano."""
    s = script_of(w)
    return bool(s) and (s in AMBIGUOUS_SCRIPTS or chatbot_ready())


def parole_da_traslitterare(graph=None, wdict=None):
    """Tutte le parole ancora senza traslitterazione: le voci vuote dei
    dizionari piu' le parole non latine che compaiono nelle etichette."""
    wdict = load_word_dict() if wdict is None else wdict
    todo = {w for w, v in wdict.items()
            if not str(v or "").strip() and _per_ai(w)}
    for n in (graph or {}).get("nodes", []):
        if n.get("ntype") == "latin":
            continue
        for lab in [n.get("label")] + list(n.get("aliases") or []):
            for w in WORD_RE.findall(str(lab or "")):
                if _per_ai(w) and not str(wdict.get(w) or "").strip():
                    todo.add(w)
    return sorted(todo)


def ai_fill_translit(todo, budget=None, max_words=None, force=False):
    """Fa tradurre al chatbot le parole di 'todo', a gruppi, e le salva.
    Ritorna le statistiche; se il chatbot tace, 'tradotte' e' 0 e basta."""
    stat = {"chieste": 0, "tradotte": 0, "restano": len(todo), "errore": "",
            "salvate": 0}
    if not todo or not chatbot_ready():
        stat["errore"] = "" if todo else "niente da tradurre"
        return stat
    if not force and time.time() < _bot["down_until"]:
        stat["errore"] = _bot["reason"] or "chatbot non raggiungibile"
        return stat
    if force:
        _bot["down_until"] = 0.0
    vivo, perche = chatbot_probe()             # sonda veloce, niente attese lunghe
    if not vivo:
        _bot_down(perche)
        stat["errore"] = perche
        return stat

    limite = max_words or CHATBOT["max_words"]
    scadenza = time.time() + (budget or CHATBOT["budget"])
    lotto = CHATBOT["batch"]
    fatte = {}
    for i in range(0, min(len(todo), limite), lotto):
        if time.time() > scadenza:
            break
        gruppo = todo[i:i + lotto]
        stat["chieste"] += len(gruppo)
        got = chatbot_translit(gruppo)
        if not got and _bot["reason"]:
            stat["errore"] = _bot["reason"]
            break
        fatte.update(got)
    stat["tradotte"] = len(fatte)
    stat["salvate"] = save_ai_translit(fatte)
    stat["restano"] = len(todo) - len(fatte)
    if fatte:
        logging.info(f"Chatbot: {len(fatte)} parole traslitterate "
                     f"({stat['restano']} ancora da fare)")
    return stat


# ---------- motore ----------
_MOD_CATS = {"Lm", "Sk", "Mn", "Mc"}


def _clean(s):
    """Toglie diacritici e lettere modificatrici (ʿ ʾ ̣ ...) lasciate da ICU."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) not in _MOD_CATS)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[`'\"]", "", s)          # ʿayn/hamza resi da anyascii come ` e '
    return re.sub(r"\s+", " ", s).strip(" -_.")


_auto_cache = {}
_HAN_RE = _rx.compile(r"^\p{Han}+$")


def _is_han(word):
    """Solo ideogrammi (cinese, o kanji senza kana)."""
    return bool(_HAN_RE.match(str(word or "")))


def _auto(word):
    """Traslitterazione automatica di una singola parola, con capitalizzazione."""
    if word in _auto_cache:
        return _auto_cache[word]
    if not _romanize_raw:
        return ""
    try:
        if _is_han(word):
            # cinese: una sillaba per carattere, separate da spazi ("Zhang Wei",
            # non "ZhangWei"); vale per entrambi i motori (ICU e anyascii)
            out = " ".join(_clean(_romanize_raw(ch)) for ch in word)
        else:
            out = _clean(_romanize_raw(word))
    except Exception:
        out = ""
    out = " ".join(p.capitalize() if p.islower() else p for p in out.split())
    _auto_cache[word] = out
    return out


def romanize(text, wdict, pending):
    """(forma latina, alfabeto, quante parole dal dizionario manuale/AI).
    Le stringhe multi-parola vengono spezzate: ogni parola è tradotta
    singolarmente, così il dizionario è riutilizzabile ovunque.
    Il dizionario (a mano o compilato dall'AI) vince sempre sul motore
    automatico, per qualunque alfabeto."""
    text = str(text or "")
    scr = script_of(text)
    if not scr:
        return None, None, 0

    parts, manual = [], 0
    for w in WORD_RE.findall(text):
        ws = script_of(w)
        if not ws:
            parts.append(w)                    # già latina
            continue
        val = wdict.get(w)
        if val and val.strip():
            parts.append(val.strip())          # dizionario manuale o AI
            manual += 1
            continue
        if val is None and ws in AMBIGUOUS_SCRIPTS:
            pending.add(w)                     # parola nuova -> nel prossimo file
        auto = _auto(w)                        # ripiego automatico (ICU/anyascii)
        if not auto:
            return None, scr, 0                # nessun motore: niente nodo a metà
        parts.append(auto)
    out = re.sub(r"\s+", " ", " ".join(p for p in parts if p)).strip()
    return (out or None), scr, manual


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"


TRANSLIT_MODES = ("attribute", "nodes")


def translit_mode():
    """'attribute' (predefinito in questo fork): la forma latina e' un attributo
    del nodo (campo 'roman': seconda riga dell'etichetta, riga della scheda,
    ricerca); 'nodes': come nell'originale, un nodo latino gemello collegato
    all'originale. Impostazione globale, nell'archivio (meta)."""
    try:
        m = store.get_gmeta("translit_mode", "attribute")
    except Exception:
        m = "attribute"
    return m if m in TRANSLIT_MODES else "attribute"


def add_translit(graph, only=None, offline=False):
    """Aggiunge un nodo latino per ogni etichetta in alfabeto non occidentale,
    collegato all'originale con un arco 'translit'. Idempotente.

    only    : se dato, elabora solo i nodi con questi id (gli altri restano
              intatti). Serve per traslitterare i nodi aggiunti a mano, che non
              passano da build_graph.
    offline : niente chatbot e niente scrittura di file (nuove parole non
              raccolte). Usato a ogni richiesta per i nodi manuali: dev'essere
              istantaneo e senza effetti collaterali. In questa modalita' non
              si toccano i nodi latini gia' esistenti (potrebbero venire dalla
              cache), ci si limita a crearne di nuovi e a collegarli."""
    if not _romanize_raw and not offline:
        # si prosegue lo stesso: le parole gia' nel dizionario (AI o a mano)
        # danno comunque il loro nodo latino
        logging.warning("Nessun motore di traslitterazione locale: solo dizionario/AI")

    wdict = load_word_dict()
    # Il chatbot compila da solo le parole ancora scoperte. Se non risponde
    # non cambia nulla: si prosegue con il dizionario e il motore automatico.
    if not offline and CHATBOT["auto"] and chatbot_ready():
        todo = parole_da_traslitterare(graph, wdict)
        if todo:
            ai_fill_translit(todo)
            wdict = load_word_dict()
    pending = set()
    existing = {n["id"]: n for n in graph["nodes"]}
    edge_keys = {e["id"] for e in graph["edges"]}
    added = 0
    mode = translit_mode()

    for n in list(graph["nodes"]):
        if n.get("ntype") == "latin":
            continue
        if only is not None and n["id"] not in only:
            continue
        labels = [n.get("label")] + list(n.get("aliases") or [])
        rom, scr, manual = romanize(labels[0], wdict, pending)
        for extra in labels[1:]:               # anche gli alias alimentano il dizionario
            romanize(extra, wdict, pending)
        if not rom:
            continue

        n["roman"] = rom
        n["script"] = scr
        n["roman_manual"] = manual

        if slug(rom) == slug(n.get("label")):
            continue
        if mode == "attribute":                # niente nodo gemello: basta 'roman'
            continue

        lid = "latin:" + slug(rom)
        if lid not in existing:
            existing[lid] = {
                "id": lid, "label": rom, "ntype": "latin", "platform": "latin",
                "image": None,
                "sources": ["translit:" + ("dizionario" if manual else TRANSLIT_ENGINE or "")],
                "records": [], "aliases": [], "alias_ids": [], "merged": 1,
                "cards": 0, "script": scr, "manual": bool(manual),
            }
            graph["nodes"].append(existing[lid])
            added += 1
        elif not offline:                      # non mutare i latini gia' in cache
            al = existing[lid].setdefault("aliases", [])
            if n.get("label") and n["label"] not in al:
                al.append(n["label"])

        key = "-".join(sorted([_hash(lid), _hash(n["id"])]))
        if key not in edge_keys:
            edge_keys.add(key)
            graph["edges"].append({"id": key, "source": lid,
                                   "target": n["id"], "rel": "translit"})

    if not offline:
        write_pending(pending)
        done = sum(1 for v in wdict.values() if v.strip())
        logging.info(f"Traslitterazione ({TRANSLIT_ENGINE}): {added} nodi latini · "
                     f"dizionario {done}/{len(wdict)} parole compilate · "
                     f"{len(pending)} nuove")
    return graph
def _hash(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:12]


def parse_records(txt):
    """Record di un export: un array JSON, un oggetto singolo o JSON Lines."""
    txt = str(txt or "").lstrip("﻿").strip()
    if not txt:
        return []
    try:
        data = json.loads(txt)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        pass
    recs = []
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return recs


def norm_platform(collection):
    c = (collection or "").lower()
    c = re.sub(r"\(.*?\)", "", c).strip()
    c = c.replace(" accounts", "").strip()
    if c in PLATFORM_TABLE:
        return PLATFORM_TABLE[c]
    if c in PHONE_SRC:
        return "phone_src"
    for k, v in PLATFORM_TABLE.items():
        # le chiavi cortissime ("x") solo su corrispondenza esatta, già gestita sopra:
        # altrimenti qualsiasi collection contenente una "x" diventerebbe Twitter/X
        if len(k) > 2 and re.search(r"\b" + re.escape(k) + r"\b", c):
            return v
    return re.sub(r"[^a-z0-9]", "", c) or "generic"


def photo_label(filename):
    """Etichetta leggibile dal nome del file: separatori -> spazi,
    via simboli e numeri. 'andrea_cumini_02.jpg' -> 'andrea cumini'."""
    stem = os.path.splitext(filename)[0]
    s = re.sub(r"[_\-.+]+", " ", stem)
    s = re.sub(r"[^\w\s]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\d+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) < 3:                      # es. 'IMG_20240101_1234' -> ripiego sul nome
        s = re.sub(r"[_\-.+]+", " ", stem)
        s = re.sub(r"\s+", " ", s).strip()
    return s or filename


def export_query(filename):
    """Dal nome di un export OSINT estrae l'identificativo cercato che ha
    generato la risposta. Es. 'export_khalifa.ashini@gmail.com.json' ->
    'khalifa.ashini@gmail.com'; 'export_khalifaashini (1).json' -> 'khalifaashini'.
    Ritorna None se il file non è un export riconoscibile."""
    stem = os.path.splitext(filename)[0].strip()
    m = re.match(r"(?:export|ricerca|search|lookup)[ _-]+(.+)$", stem, re.I)
    if not m:
        return None
    q = m.group(1).strip()
    q = re.sub(r"\s*\(\d+\)\s*$", "", q)          # toglie il suffisso ' (1)', ' (2)'…
    q = q.strip().strip("_-. ")
    return q or None


def norm_ident(val):
    """Chiave normalizzata usata per unire nodi che rappresentano lo stesso identificativo."""
    s = str(val or "").strip().lower()
    if not s:
        return ""
    digits = re.sub(r"\D", "", s)
    # numeri di telefono: confronto sulle ultime 9 cifre
    if digits and len(digits) >= 8 and len(re.sub(r"[\d\s\+\-\(\)\.]", "", s)) == 0:
        return "num:" + digits[-9:]
    if "@" in s:
        return "mail:" + re.sub(r"\s", "", s)
    s = re.sub(r"[^a-z0-9@._-]", "", s)
    return ("id:" + s) if len(s) >= 4 else ""


# etichette troppo generiche per essere una chiave di fusione
STOP_LABELS = {
    "social", "generic", "account", "accounts", "unknown", "sconosciuto",
    "null", "none", "n a", "na", "nd", "n d", "vehicle", "target", "profilo",
    "profile", "user", "utente", "anagrafica", "dossier", "scheda",
}
STOP_LABELS |= set(PLATFORM_TABLE.keys()) | set(PLATFORM_TABLE.values()) | PHONE_SRC


def norm_label(label, platform=""):
    """Chiave di fusione ricavata dall'etichetta: due nodi con la stessa
    etichetta sono la stessa entità, anche senza identificativi in comune.
    Restituisce '' per le etichette non affidabili (generiche o troppo corte)."""
    s = unicodedata.normalize("NFKD", str(label or "")).lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) < 3:
        return ""
    if s in STOP_LABELS or s == str(platform or "").lower():
        return ""
    if s.isdigit():                      # i numeri passano da norm_ident
        return ""
    return "lbl:" + s


def collect(obj, images, links):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and URL_RE.match(v):
                if any(t in k.lower() for t in IMG_KEYS) or IMG_RE.search(v):
                    images.add(v)
                else:
                    links.add(v)
            else:
                collect(v, images, links)
    elif isinstance(obj, list):
        for it in obj:
            collect(it, images, links)


# ==================== SERVIZI E IDENTIFICATIVI ====================
# servizi di messaggistica: l'account è il numero di telefono
MESSAGING = {
    "whatsapp", "viber", "imo", "botim", "telegram", "signal", "wechat",
    "line", "skype", "zangi", "tango", "kakaotalk", "threema", "icq", "snapchat",
}

# schede che descrivono il NUMERO (non un account): finiscono nel nodo telefono
PHONE_CARD_SCHEMAS = {"callerid"}
PHONE_CARD_CATEGORIES = {"technical", "checker"}

# prefisso dell'identifier -> servizio
IDENT_SERVICE = {
    "gaiaid": "google", "gaia": "google", "googleid": "google",
    "snapchatid": "snapchat", "snapchat": "snapchat",
    "discordid": "discord", "botimid": "botim", "imoid": "imo",
    "microsofthexcid": "microsoft", "skypeid": "skype", "viberid": "viber",
    "fbid": "facebook", "facebookid": "facebook", "igid": "instagram",
    "instagramid": "instagram", "vkid": "vk", "tgid": "telegram",
    "telegramid": "telegram", "waid": "whatsapp", "whatsappid": "whatsapp",
    "twitterid": "x", "xid": "x", "tiktokid": "tiktok", "appleid": "apple",
    "amazonid": "amazon", "linkedinid": "linkedin", "githubid": "github",
    "yahooid": "yahoo", "threadsid": "threads", "spotifyid": "spotify",
}

# sigle usate nei dossier: 'FB 1234 (nick)', 'IG nick', 'TikTok @nick'
DOSSIER_SOCIAL = {
    "fb": "facebook", "facebook": "facebook", "ig": "instagram",
    "instagram": "instagram", "tw": "x", "x": "x", "twitter": "x",
    "tiktok": "tiktok", "tt": "tiktok", "tg": "telegram", "telegram": "telegram",
    "wa": "whatsapp", "whatsapp": "whatsapp", "sc": "snapchat",
    "snapchat": "snapchat", "ln": "linkedin", "linkedin": "linkedin",
    "vk": "vk", "yt": "youtube", "youtube": "youtube", "sk": "skype",
    "viber": "viber", "imo": "imo", "botim": "botim", "th": "threads",
}

OPAQUE_ID = re.compile(r"^(?:[0-9]{5,}|[0-9a-fA-F][0-9a-fA-F\-]{15,})$")


def phone_key(value):
    """Identificativo univoco di un numero: sole cifre."""
    d = re.sub(r"\D", "", str(value or ""))
    return d or re.sub(r"\s+", "", str(value or "")).lower()


def parse_identifier(ident):
    """'snapchat:mohaned9376'      -> ('snapchat', 'mohaned9376')
       'microsoft-hexcid:5170A24A' -> ('microsoft', '5170A24A')
       'gaiaid:1072300798'         -> ('google', '1072300798')"""
    s = str(ident or "").strip()
    if not s:
        return "", ""
    pre, sep, val = s.partition(":")
    if not sep:
        return "generic", s
    key = re.sub(r"[^a-z0-9]", "", pre.lower())
    svc = IDENT_SERVICE.get(key)
    if not svc:
        svc = re.sub(r"(hexcid|guid|uuid|uid|id)$", "", key) or key
    return (svc or "generic"), val.strip()


def ident_label(val, fallback):
    """Un identificativo opaco (UUID, id numerico) non è una buona etichetta."""
    v = str(val or "")
    if not v or OPAQUE_ID.match(v):
        return str(fallback or v)
    return v


def parse_dossier_social(s):
    """'FB 123170275850824 (Khalifa.ashini.5)' -> ('facebook','123170275850824','Khalifa.ashini.5')
       'IG khalifaashini'                      -> ('instagram', None, 'khalifaashini')"""
    t = re.sub(r"\s+", " ", str(s or "")).strip()
    m = re.match(r"^([A-Za-z]+)\s+(.+)$", t)
    if not m:
        return None
    svc = DOSSIER_SOCIAL.get(m.group(1).lower())
    if not svc:
        return None
    rest, note = m.group(2), ""
    mp = re.search(r"\(([^)]*)\)", rest)
    if mp:
        note = mp.group(1).strip()
        rest = (rest[:mp.start()] + rest[mp.end():]).strip()
    rest = rest.strip().lstrip("@").strip()
    if re.fullmatch(r"\d{5,}", rest):                 # id numerico + nick tra parentesi
        user = re.split(r"[–\-—]", note)[0].strip().lstrip("@") or None
        return svc, rest, user, note
    return svc, None, (rest or None), note


def parse_dossier_vehicle(s):
    """'9-50555 Audi R8 (LY)' -> ('9-50555', 'Audi R8', 'LY')"""
    t = re.sub(r"\s+", " ", str(s or "")).strip()
    m = re.match(r"^([A-Z0-9][A-Z0-9\-]{3,11})\s*(.*)$", t, re.I)
    if not m:
        return None
    targa, rest, paese = m.group(1), m.group(2), ""
    mp = re.search(r"\(([^)]*)\)", rest)
    if mp:
        paese = mp.group(1).strip()
        rest = rest[:mp.start()].strip()
    return targa, rest.strip(), paese


def build_graph():
    nodes, edges = {}, {}
    # quando è True, i nodi creati/toccati sono "dati di partenza": provengono
    # dal file iniziale (dossier) del target. Il frontend li borda di rosso.
    _seed = [False]

    def add_node(nid, **attrs):
        seed = bool(_seed[0] or attrs.get("seed"))
        if nid in nodes:
            n = nodes[nid]
            if seed:
                n["seed"] = True            # una volta seed, resta seed (OR)
            for s in attrs.get("sources", []):
                if s and s not in n["sources"]:
                    n["sources"].append(s)
            if attrs.get("record"):
                n["records"].append(attrs["record"])
            for k in ("image", "label", "platform"):
                if not n.get(k) and attrs.get(k):
                    n[k] = attrs[k]
            return
        nodes[nid] = {
            "id": nid,
            "label": attrs.get("label", ""),
            "ntype": attrs.get("ntype", "generic"),
            "platform": attrs.get("platform", "generic"),
            "image": attrs.get("image"),
            "sources": [s for s in attrs.get("sources", []) if s],
            "records": [attrs["record"]] if attrs.get("record") else [],
            "seed": seed,
        }

    def add_edge(x, y, rel=""):
        if not x or not y or x == y:
            return
        key = "-".join(sorted([_hash(x), _hash(y)]))
        if key not in edges:
            edges[key] = {"id": key, "source": x, "target": y, "rel": rel}

    ident_map = {}

    def map_ident(nid, value):
        k = norm_ident(value)
        if k:
            ident_map.setdefault(k, set()).add(nid)

    def map_acct(nid, svc, raw):
        """Chiave di fusione di un account: piattaforma + valore normalizzato,
        tenuti separati da '|'. Il valore deve essere significativo (>= 3 caratteri
        utili): altrimenti la fusione è SALTATA. Evita che account diversi con
        nick vuoto o non-latino collassino tutti sulla stessa chiave (il bug per
        cui 4 utenti TikTok diversi finivano fusi su 'id:tiktok')."""
        svc = re.sub(r"[^a-z0-9]", "", str(svc or "").lower()) or "generic"
        v = re.sub(r"[^a-z0-9@._]", "", str(raw or "").strip().lower()).strip("._@")
        if len(v) < 3:
            return
        ident_map.setdefault(f"acct:{svc}|{v}", set()).add(nid)

    # ---------- costruttori di nodi elementari ----------
    def node_phone(value, record=None, source=""):
        pid = "phone:" + phone_key(value)
        add_node(pid, label=str(value), ntype="phone", platform="phone",
                 sources=[source] if source else [], record=record)
        map_ident(pid, value)
        return pid

    def node_email(value, record=None, source=""):
        eid = "email:" + str(value).strip().lower()
        add_node(eid, label=str(value).strip(), ntype="email", platform="email",
                 sources=[source] if source else [], record=record)
        map_ident(eid, value)
        return eid

    def node_username(value, platform="username", source=""):
        uid = "user:" + str(value).strip().lower()
        add_node(uid, label=str(value).strip(), ntype="username",
                 platform=platform or "username", sources=[source] if source else [])
        map_ident(uid, value)
        return uid

    def node_person_name(value, source=""):
        """Nodo 'nome' ricavato da come un'utenza è registrata nelle rubriche.
        Scarta ciò che non è un nome: numeri, sigle, etichette di servizio."""
        lab = re.sub(r"\s+", " ", str(value or "")).strip(" .,-–—")
        if not lab or len(lab) < 3 or len(lab) > 80:
            return None
        if not WORD_RE.search(lab):                  # nessuna lettera: è un numero
            return None
        if re.sub(r"\D", "", lab) and len(re.sub(r"\D", "", lab)) >= 6:
            return None                              # contiene un numero di telefono
        if lab.lower() in NAME_STOP:
            return None
        nid = person_id(lab)
        add_node(nid, label=lab, ntype="name", platform="name",
                 sources=[source] if source else [])
        return nid

    def node_place(info, source="", scope=""):
        """Nodo luogo ricavato da una scheda: etichetta e/o coordinate.
        Con le coordinate il nodo si apre sulla mappa con Alt+Click.

        Un luogo GENERICO (citta', regione, paese) resta chiuso dentro il suo
        target: l'id porta il prefisso del target, cosi' "Tripoli" citata in
        dieci fascicoli diventa dieci nodi distinti e non crea collegamenti fra
        persone estranee. Solo un RECAPITO (indirizzo o coordinate) e' condiviso
        e quindi puo' unire due schede."""
        lab = (info.get("label") or "").strip()
        lat, lon = info.get("lat"), info.get("lon")
        if not lab and not (lat and lon):
            return None
        chiave = re.sub(r"\s+", " ", lab).casefold() if lab else f"{lat},{lon}"
        recapito = place_is_address(lab, lat, lon, info.get("key"))
        pid = "place:" + chiave if recapito else f"place:{scope}|{chiave}"
        url = ("https://www.google.com/maps/search/?api=1&query="
               + (f"{lat},{lon}" if lat and lon else quote(lab)))
        add_node(pid, label=lab or f"{lat}, {lon}", ntype="place", platform="place",
                 sources=[source] if source else [])
        n = nodes[pid]
        n["url"] = url
        n["address"] = recapito
        if lat and lon:
            n["lat"], n["lon"] = lat, lon
        return pid

    def node_vehicle(targa, label, record=None):
        vid = "vehicle:" + re.sub(r"\s+", "", str(targa)).upper()
        add_node(vid, label=label or str(targa), ntype="vehicle", platform="vehicle",
                 sources=["veicolo"], record=record)
        map_ident(vid, targa)
        return vid

    def search_anchor(fn, tid):
        """Nodo di ricerca a cui appendere un export: l'identificativo nel nome
        del file (email, telefono o utenza). Resta agganciato al target, così la
        gerarchia diventa  target -> identificativo cercato -> risultati trovati,
        invece di collegare tutto direttamente al target.
        Ritorna None se il file non è un export o la query non è interpretabile."""
        q = export_query(fn)
        if not q:
            return None
        if "@" in q and "." in q.split("@")[-1]:
            nid = node_email(q, source="ricerca")
        elif re.fullmatch(r"\+?[0-9][0-9\s().\-]{5,}", q):
            nid = node_phone(q, source="ricerca")
        else:
            nid = node_username(q, source="ricerca")
        add_edge(tid, nid, "target")              # l'identificativo resta appeso al target
        return nid

    # ---------- scheda "normale" (export di un servizio) ----------
    def handle_record(rec, tid, fn, target, on_target=False):
        platform = norm_platform(rec.get("collection"))
        label = rec.get("label") or (rec.get("names") or [""])[0] or platform
        schema = str(rec.get("schema") or "").lower()
        cat = str(rec.get("category_id") or "").lower()
        coll = rec.get("collection") or ""

        images, links = set(), set()
        collect(rec, images, links)
        img = next(iter(sorted(images)), None)
        record = {"collection": coll or ("dossier" if on_target else None),
                  "schema": rec.get("schema"),
                  "category": rec.get("category_id"),
                  "images": sorted(images),
                  "links": sorted(links),
                  "raw": rec}

        phones = [str(p) for p in (rec.get("phones") or []) if p]
        emails = [str(e) for e in (rec.get("emails") or []) if e]
        usernames = [str(u) for u in (rec.get("usernames") or []) if u]
        idents = [str(i) for i in (rec.get("identifiers") or []) if i]

        # --- telefoni: un nodo per numero, i numeri della stessa scheda sono collegati
        phone_ids = [node_phone(p, source=coll) for p in phones]
        for extra in phone_ids[1:]:
            add_edge(phone_ids[0], extra, "phone-link")

        # --- email: le secondarie si collegano alla principale
        email_ids = [node_email(e, source=coll) for e in emails]
        for extra in email_ids[1:]:
            add_edge(email_ids[0], extra, "email-alias")

        # --- username
        user_ids = [node_username(u, platform, coll) for u in usernames]

        # --- nodo/i principale/i della scheda
        primary = []
        if on_target:
            add_node(tid, image=img, sources=[coll or "dossier"], record=record)
            primary = [tid]

        elif idents:
            # UN nodo per SERVIZIO: più identificativi dello stesso social sono
            # lo stesso account (snapchatid:UUID + snapchat:nick), servizi
            # diversi nella stessa scheda (instagram + threads) restano distinti
            groups = {}
            for ident in idents:
                svc, val = parse_identifier(ident)
                groups.setdefault(svc or platform, []).append((ident, val))

            for svc, items in groups.items():
                # id canonico: si preferisce l'identificativo leggibile a quello opaco
                items = sorted(items, key=lambda t: (bool(OPAQUE_ID.match(t[1] or "")), t[0]))
                canon_ident, canon_val = items[0]
                aid = "acct:" + canon_ident.strip().lower()
                # profilo da un'API (Epieos): l'etichetta e' il nome del profilo,
                # l'userid resta l'identita' e sta nella scheda
                lab = str(label) if schema.startswith("epieos:") and label else ident_label(canon_val, label)
                add_node(aid, label=lab, ntype="account",
                         platform=svc or platform, image=img,
                         sources=[coll], record=record)
                # TUTTI gli identificativi del gruppo puntano a questo nodo: schede
                # diverse che ne citano solo uno finiscono comunque sullo stesso nodo
                for ident, val in items:
                    map_acct(aid, svc, val)
                for un in usernames:            # username univoco per piattaforma:
                    map_acct(aid, svc, un)      # id diversi + stesso nick = stesso account
                primary.append(aid)

            for extra in primary[1:]:
                add_edge(primary[0], extra, "alias")

        elif platform in MESSAGING and phones:
            # messaggistica senza identifier: l'account È il numero -> whatsapp-<numero>
            for ph, pid in zip(phones, phone_ids):
                aid = f"acct:{platform}-{phone_key(ph)}"
                lab = str(label) if label and label != ph else f"{platform} {ph}"
                add_node(aid, label=lab, ntype="account", platform=platform,
                         image=img, sources=[coll], record=record)
                add_edge(aid, pid, "phone")
                primary.append(aid)

        elif phones and (schema in PHONE_CARD_SCHEMAS or cat in PHONE_CARD_CATEGORIES
                         or not (emails or usernames)):
            # aggregatore/lookup: la scheda descrive il numero, elenca i servizi trovati
            for pid in phone_ids:
                add_node(pid, sources=[coll], record=record)
            primary = list(phone_ids)
            # i nomi con cui il numero è registrato diventano nodi a sé:
            # ricorrono su più utenze e sono un ottimo punto di aggancio.
            # Se sono in scrittura non latina, add_translit crea da solo il
            # nodo con la forma latina, collegato all'originale.
            for nm in (rec.get("names") or []) + [rec.get("label")]:
                nid = node_person_name(nm, coll)
                if nid:
                    for pid in phone_ids:
                        add_edge(pid, nid, "name")

        elif emails and not usernames:
            for eid in email_ids:
                add_node(eid, sources=[coll], record=record)
            primary = list(email_ids)

        else:
            aid = "acct:" + _hash(target + coll + str(label) + fn + str(rec.get("created_at")))
            add_node(aid, label=str(label), ntype="account", platform=platform,
                     image=img, sources=[coll], record=record)
            primary = [aid]

        # --- luoghi citati nella scheda (città, indirizzi, coordinate)
        place_ids, visti = [], set()
        for info in collect_places(rec):
            pid = node_place(info, coll, tid)
            if pid and pid not in visti:
                visti.add(pid)
                place_ids.append(pid)
            if len(place_ids) >= 12:            # una scheda non ne cita mai di più
                break

        # --- a quale nodo si aggancia la scheda?
        # Il dossier va sul target; un export OSINT va sul NODO DI RICERCA che
        # l'ha generato (l'identificativo nel nome del file), non sul target.
        # Se la query non è interpretabile si ricade sul target (nessun orfano).
        anchor = tid
        if not on_target:
            anchor = search_anchor(fn, tid) or tid

        # --- violazioni di dati (hibp), siti con un account (holehe,
        #     phonechecker), organizzazioni (linkedin): estensioni Epieos
        extra_ids = []
        for br in (rec.get("breaches") or []):
            name = re.sub(r"\s+", " ", str(br)).strip()
            if not name:
                continue
            bid = "breach:" + slug(name)
            add_node(bid, label=name, ntype="breach", platform="breach", sources=[coll],
                     record={"collection": coll, "images": [], "links": [],
                             "raw": {"violazione": name, "fonte": coll}})
            extra_ids.append((bid, "breach"))
        qkey = slug(str(rec.get("query") or target))
        for site in (rec.get("websites") or []):
            site = str(site).strip().lower()
            if not site:
                continue
            svc = re.sub(r"^www\.", "", site)
            svc_key = re.sub(r"\.(com|net|org|it|io|tv|co|app|me)$", "", svc)
            sid = f"acct:{svc_key}:{qkey}"
            add_node(sid, label=svc, ntype="account", platform=norm_platform(svc_key),
                     sources=[coll], record={"collection": coll, "images": [], "links": [],
                                             "raw": {"sito": site, "registrato": str(rec.get("query") or "")}})
            extra_ids.append((sid, "registered"))
        for org in (rec.get("organizations") or []):
            if not isinstance(org, dict) or not str(org.get("name") or "").strip():
                continue
            fields = {"nome": str(org["name"]).strip()}
            oid = "organization:" + onto.ident_of("organization", fields)
            add_node(oid, label=fields["nome"], ntype="organization", platform="organization",
                     sources=[coll], record={"collection": coll, "images": [], "links": [],
                                             "raw": {"Denominazione": fields["nome"],
                                                     "Ruolo": org.get("role") or "", "Periodo": org.get("period") or ""}})
            extra_ids.append((oid, org.get("role") or ("studente" if org.get("kind") == "school" else "organization")))

        # --- collegamenti
        for p in primary:
            add_edge(anchor, p, "target" if anchor == tid else "result")
            for x in phone_ids:
                add_edge(p, x, "phone")
            for x in email_ids:
                add_edge(p, x, "email")
            for x in user_ids:
                add_edge(p, x, "username")
            for x, rel in extra_ids:
                add_edge(p, x, rel)
            for x in place_ids:
                add_edge(p, x, "place")

        # --- blocchi in formato "dossier strutturato" (compatibilità)
        for soc in (rec.get("social") or []):
            if not isinstance(soc, dict):
                continue
            svc = (soc.get("piattaforma") or "").lower() or "generic"
            val = soc.get("identificativo") or soc.get("username")
            if not val:
                continue
            sid = f"acct:{svc}:{str(val).lower()}"
            add_node(sid, label=str(soc.get("username") or val), ntype="account",
                     platform=svc, sources=[svc],
                     record={"collection": svc, "images": [], "links": [], "raw": soc})
            map_acct(sid, svc, val)
            if soc.get("username"):
                map_acct(sid, svc, soc["username"])
            add_edge(primary[0] if primary else anchor, sid, "social")
            if soc.get("username"):
                add_edge(sid, node_username(soc["username"], svc, svc), "username")

        for veh in (rec.get("veicoli") or []):
            if isinstance(veh, dict) and veh.get("targa"):
                lab = f"{veh['targa']} {veh.get('marca','')} {veh.get('modello','')}".strip()
                vid = node_vehicle(veh["targa"], lab,
                                   {"collection": "veicolo", "images": [], "links": [], "raw": veh})
                add_edge(primary[0] if primary else anchor, vid, "vehicle")

    # ---------- dossier investigativo (A22.json e simili) ----------
    def handle_dossier(rec, tid, fn):
        coll = rec.get("collection") or "dossier"
        add_node(tid, sources=[coll],
                 record={"collection": coll, "schema": rec.get("schema"),
                         "category": "dossier", "images": [], "links": [], "raw": rec})

        card = lambda voce: {"collection": coll, "images": [], "links": [],
                             "raw": {"voce": voce, "fonte": fn}}

        utenze = [u for u in (rec.get("utenze") or rec.get("phones") or []) if u]
        phone_ids = [node_phone(u, card(u), coll) for u in utenze]
        for pid in phone_ids:
            add_edge(tid, pid, "phone")

        mails = [e for e in (rec.get("email") or rec.get("emails") or []) if e]
        email_ids = [node_email(e, card(e), coll) for e in mails]
        for eid in email_ids:
            add_edge(tid, eid, "email")
        for extra in email_ids[1:]:
            add_edge(email_ids[0], extra, "email-alias")

        for voce in (rec.get("social") or []):
            if isinstance(voce, dict):
                continue                              # gestito da handle_record
            parsed = parse_dossier_social(voce)
            if not parsed:
                continue
            svc, sid_val, user, note = parsed
            key = (sid_val or user or "").lower()
            if not key:
                continue
            aid = f"acct:{svc}:{key}"
            add_node(aid, label=user or sid_val, ntype="account", platform=svc,
                     sources=[coll], record=card(voce))
            map_acct(aid, svc, key)
            if user:                            # stesso nick sullo stesso social =
                map_acct(aid, svc, user)        # stesso account, anche con id diversi
            add_edge(tid, aid, "target")
            if user:
                add_edge(aid, node_username(user, svc, coll), "username")

        for voce in (rec.get("veicoli") or []):
            if isinstance(voce, dict):
                continue
            parsed = parse_dossier_vehicle(voce)
            if not parsed:
                continue
            targa, descr, paese = parsed
            lab = f"{targa} {descr}".strip() + (f" ({paese})" if paese else "")
            add_edge(tid, node_vehicle(targa, lab, card(voce)), "vehicle")

    # ---------- JSON importati da app terze (database) ----------
    # Ogni file e' agganciato a un nodo (di norma il target, una persona): il
    # nodo stesso lo crea apply_annotations dalla sua voce manuale, qui lo si
    # dichiara solo perche' i collegamenti del file abbiano un estremo.
    n_files = 0
    for imp in store.iter_imports():
        n_files += 1
        tid, fn, dossier = imp["anchor"], imp["filename"], bool(imp["dossier"])
        add_node(tid, label=imp["anchor_label"], ntype=imp["anchor_ntype"],
                 platform=imp["anchor_platform"])
        _seed[0] = dossier                 # i nodi di questo file sono dati di partenza
        recs = parse_records(imp["content"])
        if len(recs) == 1 and epieos.is_epieos(recs[0]):
            recs = epieos.to_records(recs[0])      # risposta dell'API Epieos
        for rec in recs:
            if not isinstance(rec, dict):
                continue
            schema = str(rec.get("schema") or "").lower()
            if dossier and (schema.startswith("soggetto") or rec.get("utenze")
                            or rec.get("alias_varianti")):
                handle_dossier(rec, tid, fn)
            else:
                handle_record(rec, tid, fn, tid, on_target=dossier)
        _seed[0] = False
    logging.info(f"JSON importati: {n_files} file")

    # ---- FUSIONE per identificativo + ROMANIZZAZIONE ----
    return add_translit(merge_nodes(nodes, edges, ident_map))



TYPE_RANK = {"target": 0, "account": 1, "vehicle": 2, "email": 3,
             "phone": 4, "username": 5, "domain": 6, "photo": 8, "generic": 9}


def _flat(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _mixed_case(s):
    s = str(s or "")
    return any(c.isupper() for c in s) and any(c.islower() for c in s)


def merge_nodes(nodes, edges, ident_map):
    """Nodi che condividono lo stesso identificativo diventano UN solo nodo,
    che conserva tutte le schede (record) e le etichette alternative (alias)."""
    parent = {nid: nid for nid in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for ids in ident_map.values():
        ids = [i for i in sorted(ids) if i in parent]
        for other in ids[1:]:
            union(ids[0], other)

    groups = {}
    for nid in nodes:
        groups.setdefault(find(nid), []).append(nid)

    alias = {}
    merged = {}
    for root, ids in groups.items():
        # nodo rappresentante: tipo più informativo, etichetta più ricca,
        # a parità si preferisce quella con maiuscole/minuscole corrette
        canon = sorted(ids, key=lambda i: (
            TYPE_RANK.get(nodes[i]["ntype"], 9),
            -len(_flat(nodes[i]["label"])),
            0 if _mixed_case(nodes[i]["label"]) else 1,
            i))[0]
        base = dict(nodes[canon])
        base["label"] = _flat(base["label"]) or base["label"]
        base["records"] = list(base["records"])
        base["sources"] = list(base["sources"])
        labels = [_flat(base["label"])]
        for i in ids:
            alias[i] = canon
            if i == canon:
                continue
            n = nodes[i]
            base["records"].extend(n["records"])
            for s in n["sources"]:
                if s and s not in base["sources"]:
                    base["sources"].append(s)
            if not base.get("image") and n.get("image"):
                base["image"] = n["image"]
            lab = _flat(n["label"])
            if lab and lab.lower() not in {x.lower() for x in labels}:
                labels.append(lab)
        base["aliases"] = labels[1:]
        base["alias_ids"] = sorted(i for i in ids if i != canon)
        base["seed"] = any(nodes[i].get("seed") for i in ids)   # seed se lo è uno qualsiasi
        base["merged"] = len(ids)
        base["cards"] = len(base["records"])
        merged[canon] = base

    new_edges = {}
    for e in edges.values():
        s, t = alias.get(e["source"]), alias.get(e["target"])
        if not s or not t or s == t:
            continue
        key = "-".join(sorted([_hash(s), _hash(t)]))
        if key not in new_edges:
            new_edges[key] = {"id": key, "source": s, "target": t, "rel": e.get("rel", "")}

    fused = sum(1 for b in merged.values() if b["merged"] > 1)
    logging.info(f"Nodi fusi: {fused} gruppi · {len(nodes)} -> {len(merged)} nodi")
    return {"nodes": list(merged.values()), "edges": list(new_edges.values())}


# ==================== ETICHETTE MODIFICATE A MANO ====================
# Rinominare la scheda non tocca i file di origine: l'etichetta nuova sta in
# annotations.json e viene applicata al grafo a ogni caricamento. Se dopo la
# modifica due schede rappresentano lo stesso identificativo (es. lo stesso
# numero scritto con 00 e con +) vengono fuse in una sola scheda.

# tipi che NON si fondono mai per etichetta: un target resta se stesso anche
# se due fascicoli hanno lo stesso nome
NO_LABEL_MERGE = {"target"}


def _key_text(s):
    """Testo normalizzato per il confronto fra etichette (senza accenti,
    punteggiatura e differenze di maiuscole)."""
    s = unicodedata.normalize("NFKD", str(s or "")).casefold()
    s = unicodedata.normalize("NFC", _LATIN_DIACRITICS.sub("", s))
    s = _rx.sub(r"[^\p{L}\p{M}\p{N}_\s]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def label_merge_key(node):
    """Chiave con cui due schede con la stessa etichetta diventano una sola.
    Telefoni ed email si confrontano sul VALORE normalizzato: '00218...' e
    '+218...' hanno la stessa chiave. Gli altri tipi si confrontano sul testo,
    ma solo fra nodi dello stesso tipo."""
    nt = node.get("ntype") or "generic"
    if nt in NO_LABEL_MERGE:
        return ""
    lab = _flat(node.get("label"))
    if len(lab) < 3:
        return ""
    # un luogo generico non unisce mai due schede (vedi place_is_address)
    if nt == "place" and not place_is_address(lab, node.get("lat"), node.get("lon"),
                                              "address"):
        return ""
    k = norm_ident(lab)
    if k.startswith(("num:", "mail:")):
        return k
    return nt + "|" + (_key_text(lab) or lab.casefold())


def merge_by_label(nodes, edges, renamed):
    """Fonde i gruppi di nodi con la stessa chiave di etichetta, ma solo quelli
    che contengono almeno un nodo rinominato a mano: la fusione e' sempre una
    conseguenza di una scelta dell'utente, mai un effetto collaterale."""
    groups = {}
    for n in nodes:
        k = label_merge_key(n)
        if k:
            groups.setdefault(k, []).append(n)
    fusioni = [g for g in groups.values()
               if len(g) > 1 and any(n["id"] in renamed for n in g)]
    if not fusioni:
        return {"nodes": nodes, "edges": edges}

    alias, fusi = {}, {}
    for g in fusioni:
        # rappresentante: si preferisce la scheda NON rinominata (quella che
        # esisteva gia'), poi il tipo piu' informativo e l'etichetta piu' ricca
        canon = sorted(g, key=lambda n: (n["id"] in renamed,
                                         TYPE_RANK.get(n.get("ntype"), 9),
                                         -len(_flat(n.get("label"))), n["id"]))[0]
        base = dict(canon)
        base["records"] = list(base.get("records") or [])
        base["sources"] = list(base.get("sources") or [])
        base["aliases"] = list(base.get("aliases") or [])
        base["alias_ids"] = list(base.get("alias_ids") or [])
        note = [base["note"]] if base.get("note") else []
        for n in g:
            if n["id"] == canon["id"]:
                continue
            alias[n["id"]] = base["id"]
            base["records"].extend(n.get("records") or [])
            for s in (n.get("sources") or []):
                if s and s not in base["sources"]:
                    base["sources"].append(s)
            noti = {_flat(base["label"]).casefold()}
            noti |= {x.casefold() for x in base["aliases"]}
            for a in [n.get("label")] + list(n.get("aliases") or []):
                a = _flat(a)
                if a and a.casefold() not in noti:
                    base["aliases"].append(a)
            for i in [n["id"]] + list(n.get("alias_ids") or []):
                if i != base["id"] and i not in base["alias_ids"]:
                    base["alias_ids"].append(i)
            for k in ("image", "url", "lat", "lon", "roman", "script", "seed"):
                if not base.get(k) and n.get(k):
                    base[k] = n[k]
            if n.get("note") and n["note"] not in note:
                note.append(n["note"])
            base["merged"] = (base.get("merged") or 1) + (n.get("merged") or 1)
        if note:
            base["note"] = (chr(10) * 2).join(note)
        base["cards"] = len(base["records"])
        base["manual"] = all(n.get("manual") for n in g)
        base["fused_by_label"] = True
        fusi[base["id"]] = base

    out = [fusi.get(n["id"], n) for n in nodes if n["id"] not in alias]

    visti, new_edges = set(), []
    for e in edges:
        s, t = alias.get(e["source"], e["source"]), alias.get(e["target"], e["target"])
        if s == t:
            continue
        key = e.get("id") or "-".join(sorted([_hash(s), _hash(t)]))
        if key in visti:
            continue
        visti.add(key)
        ne = dict(e)
        ne["source"], ne["target"] = s, t
        new_edges.append(ne)
    logging.info(f"Etichette modificate: {len(alias)} schede fuse in {len(fusioni)}")
    return {"nodes": out, "edges": new_edges}


def relabel(graph, labels):
    """Applica le etichette modificate a mano e, se servono, fonde le schede."""
    if not labels:
        return graph
    nodes, renamed = [], set()
    for n in graph["nodes"]:
        ov = _flat((labels.get(n["id"]) or {}).get("label"))
        if ov and ov != _flat(n.get("label")):
            n = dict(n)
            n["label_orig"] = n.get("label")
            n["label"] = ov
            n["renamed"] = True
            renamed.add(n["id"])
        nodes.append(n)
    if not renamed:
        return {"nodes": nodes, "edges": graph["edges"]}
    return merge_by_label(nodes, graph["edges"], renamed)


_cache = {"key": None, "graph": None}


def data_signature():
    """Cambia quando cambiano i dati da cui si costruisce il grafo: i JSON
    importati e il dizionario di traslitterazione (le annotazioni no: si
    applicano a ogni richiesta sopra il grafo in cache)."""
    return (store.current_case(), store.version(), store.version("translit_version"),
            translit_mode())


@app.route("/")
def index():
    # versione = mtime di app.js/style.css: forza il browser a riscaricare i
    # file statici quando cambiano (niente più JS servito dalla cache)
    def _mtime(fn):
        try:
            return int(os.path.getmtime(os.path.join(app.static_folder, fn)))
        except OSError:
            return 0
    ver = max(_mtime("app.js"), _mtime("style.css"), _mtime("i18n.js"))
    return render_template("index.html", asset_ver=ver, fa_icons=fa_icons(),
                           ontology=onto.public(), base_icons=onto.BASE_ICONS,
                           onto_i18n=onto_i18n.table(), ftm_edges=ftm.edges_public())


_FA_DIR = os.path.join(RES_DIR, "static", "vendor", "fa")
_fa_cache = {}


def fa_icons():
    """Icone Font Awesome Free (static/vendor/fa): {nome: svg}. Stanno dentro
    l'app, non su internet. Si inseriscono nella pagina, cosi' sono pronte
    prima che il grafo venga disegnato."""
    if not _fa_cache:
        try:
            for fn in os.listdir(_FA_DIR):
                if fn.endswith(".svg"):
                    with open(os.path.join(_FA_DIR, fn), encoding="utf-8") as f:
                        svg = re.sub(r"<!--.*?-->", "", f.read(), flags=re.S).strip()
                    _fa_cache[fn[:-4]] = svg
        except OSError as e:
            logging.warning(f"Icone non trovate in {_FA_DIR}: {e}")
    return _fa_cache


# ============================== CASI (FASCICOLI) ==============================
# Ogni caso ha il suo database (store.py): nodi, schede, collegamenti, note,
# viste e JSON importati. Dizionario di traslitterazione e indice dei
# documenti sono comuni a tutti i casi.
def _case_name(data, key="name"):
    return re.sub(r"\s+", " ", str(data.get(key) or "")).strip()[:120]


@app.route("/api/cases")
def api_cases():
    return jsonify({"items": store.list_cases(), "current": store.current_case()})


@app.route("/api/cases/add", methods=["POST"])
def api_cases_add():
    data = request.get_json(silent=True) or {}
    name = _case_name(data)
    if not name:
        return jsonify({"error": "nome del caso mancante"}), 400
    c = store.create_case(name, str(data.get("description") or "")[:2000])
    store.open_case(c["id"])
    _cache["key"] = None
    logging.info(f"Nuovo caso: {name} ({c['id']})")
    return jsonify({"ok": True, "case": c})


@app.route("/api/cases/update", methods=["POST"])
def api_cases_update():
    data = request.get_json(silent=True) or {}
    cid = str(data.get("id") or "")
    if not store.get_case(cid):
        return jsonify({"error": "caso non trovato"}), 404
    name = _case_name(data)
    if not name:
        return jsonify({"error": "nome del caso mancante"}), 400
    c = store.update_case(cid, name, str(data.get("description") or "")[:2000])
    return jsonify({"ok": True, "case": c})


@app.route("/api/cases/switch", methods=["POST"])
def api_cases_switch():
    data = request.get_json(silent=True) or {}
    cid = str(data.get("id") or "")
    if not store.case_exists(cid):
        return jsonify({"error": "caso non trovato"}), 404
    store.open_case(cid)
    _cache["key"] = None
    logging.info(f"Caso aperto: {cid}")
    return jsonify({"ok": True, "case": store.get_case(cid)})


@app.route("/api/cases/delete", methods=["POST"])
def api_cases_delete():
    """Elimina il caso e TUTTO il suo contenuto (il suo database)."""
    data = request.get_json(silent=True) or {}
    cid = str(data.get("id") or "")
    if not store.get_case(cid):
        return jsonify({"error": "caso non trovato"}), 404
    was_current = cid == store.current_case()
    store.delete_case(cid)
    if was_current:
        # si passa a un altro caso; se era l'ultimo non ne resta nessuno aperto
        # (l'interfaccia chiede di crearne uno)
        altri = store.list_cases()
        if altri:
            store.open_case(altri[0]["id"])
        _cache["key"] = None
    logging.info(f"Caso eliminato: {cid}")
    return jsonify({"ok": True, "current": store.current_case()})


@app.route("/api/cases/merge", methods=["POST"])
def api_cases_merge():
    """{ids: [...], name, delete_sources: bool} -> nuovo caso con il contenuto
    di tutti; i nodi uguali diventano uno (le differenze come schede in piu')."""
    data = request.get_json(silent=True) or {}
    ids = [str(x) for x in (data.get("ids") or []) if store.get_case(str(x))]
    ids = list(dict.fromkeys(ids))
    if len(ids) < 2:
        return jsonify({"error": "scegli almeno due casi da unire"}), 400
    name = _case_name(data) or " + ".join(store.get_case(i)["name"] for i in ids)[:120]
    c = store.merge_cases(ids, name, str(data.get("description") or "")[:2000])
    store.open_case(c["id"])
    _cache["key"] = None
    if _truthy(data.get("delete_sources")):
        for i in ids:
            store.delete_case(i)
    logging.info(f"Casi uniti in {name}: {ids}")
    return jsonify({"ok": True, "case": c})


@app.route("/api/ontology")
def api_ontology():
    return jsonify(onto.public())


@app.route("/media/<path:relpath>")
def media(relpath):
    """Serve le immagini contenute in DATA_DIR (solo lettura, path controllato)."""
    root = os.path.abspath(DATA_DIR)
    full = os.path.abspath(os.path.join(root, relpath))
    if not full.startswith(root + os.sep) or not os.path.isfile(full):
        abort(404)
    if not full.lower().endswith(PHOTO_EXT):
        abort(403)
    return send_from_directory(os.path.dirname(full), os.path.basename(full),
                               max_age=3600)


# ==================== ARCHIVIO (SQLite) ====================
# Tutto cio' che l'utente crea o importa sta in data/osintgraph.db (vedi
# store.py): nodi aggiunti a mano e schede, collegamenti, note, etichette,
# nodi nascosti, viste salvate, dizionario di traslitterazione, JSON importati
# da app terze e indice dei documenti. Su disco restano solo le immagini
# caricate (data/media) e la configurazione dell'AI (chatbot.conf).
import store
import ftm
import ftm_bundle
import epieos
import ontology as onto
import ontology_i18n as onto_i18n
store.init(DATA_DIR)
logging.info(f"Archivio: {store.path() or 'nessun caso aperto'} (caso {store.current_case()})")


@app.errorhandler(store.NoCaseError)
def _no_case(e):
    """Qualsiasi operazione sul database del caso senza un caso aperto."""
    return jsonify({"error": str(e), "no_case": True}), 409

# Indice delle fonti (documenti indicizzati): nel database, chiave 'sources_index'.
import sources as _src
SOURCES_BLOB = "sources_index"
# cartella fonti predefinita: 'fonti' ACCANTO all'eseguibile (tutto portabile).
# La creo subito così l'utente la trova e ci mette dentro i documenti.
SOURCES_DEFAULT = os.path.join(BASE_DIR, "fonti")
try:
    os.makedirs(SOURCES_DEFAULT, exist_ok=True)
except OSError as _e:
    logging.warning(f"Impossibile creare la cartella fonti {SOURCES_DEFAULT}: {_e}")
_ocr_ok = _src.configure_ocr(BASE_DIR)   # cerca un Tesseract locale (tools/tesseract)
logging.info(f"OCR {'attivo' if _ocr_ok else 'non disponibile'} "
             f"(cerco Tesseract in {os.path.join(BASE_DIR, 'tools', 'tesseract')}; lingue: {_src.OCR_LANG or 'predefinita'})")
_sources_cache = {"idx": None}

# -------- Tesseract scaricabile dall'interfaccia (solo Windows) ----------
# Stesso procedimento di setup_tesseract.py, eseguito in un thread: lo stato
# si legge da /api/ocr/install/status mentre il pannello mostra l'avanzamento.
import setup_tesseract as _tess
_OCR_JOB = {"state": "idle", "stage": "", "percent": 0, "error": ""}
_OCR_LOCK = threading.Lock()


def _ocr_install_worker():
    def progress(done, total):
        _OCR_JOB["percent"] = int(done * 100 / total) if total else 0

    def stage(name):
        _OCR_JOB["stage"] = name

    try:
        dest = os.path.join(BASE_DIR, "tools", "tesseract")
        exe = _tess.setup_windows(_tess.DEFAULT_URL, dest, progress=progress, stage=stage)
        ok = _src.configure_ocr(BASE_DIR)          # attiva l'OCR senza riavviare
        _OCR_JOB.update(state="done" if ok else "error", percent=100,
                        error="" if ok else "tesseract.exe scaricato ma non utilizzabile")
        logging.info(f"Tesseract in {exe}: OCR {'attivo' if ok else 'NON attivo'}")
    except Exception as e:
        logging.error("Installazione di Tesseract fallita", exc_info=True)
        _OCR_JOB.update(state="error", error=str(e))


@app.route("/api/ocr/install", methods=["POST"])
def api_ocr_install():
    """Avvia il download di Tesseract nella cartella tools/tesseract."""
    if os.name != "nt":
        return jsonify({"error": "download automatico disponibile solo su Windows"}), 400
    if _src.OCR_AVAILABLE:
        return jsonify({"ok": True, "state": "done", "already": True})
    if _src.OCR_REASON == "module":
        return jsonify({"error": "manca il modulo Python pytesseract: pip install pytesseract"}), 400
    with _OCR_LOCK:
        if _OCR_JOB["state"] != "running":
            _OCR_JOB.update(state="running", stage="download", percent=0, error="")
            threading.Thread(target=_ocr_install_worker, daemon=True).start()
            logging.info(f"Download di Tesseract da {_tess.DEFAULT_URL}")
    return jsonify({"ok": True, "state": "running", "url": _tess.DEFAULT_URL})


@app.route("/api/ocr/install/status")
def api_ocr_install_status():
    return jsonify(dict(_OCR_JOB, ocr_available=_src.OCR_AVAILABLE))


def sources_index():
    if _sources_cache["idx"] is None:
        try:
            _sources_cache["idx"] = store.get_blob(SOURCES_BLOB)
        except store.NoCaseError:
            return None                           # nessun caso aperto: nessun indice
    return _sources_cache["idx"]


def _save_sources_index(index):
    store.set_blob(SOURCES_BLOB, index)


def _clean_labels(raw):
    """{'labels': {id: {label, orig, at}}} - accetta anche la forma breve
    {id: 'nuova etichetta'} usata dai file scritti a mano."""
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
    """Annotazioni dell'utente, dal database:
    {'added': [...], 'links': [...], 'deleted': [...], 'notes': {id: testo},
     'labels': {id: {...}}, 'edits': {id: {...}}, 'edge_styles': {id: {...}}}.
    Si salvano con save_annotations, che scrive solo le differenze."""
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
    """Nodo del grafo corrispondente a una voce aggiunta a mano."""
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
    # colonne libere di un file importato: nella scheda con il nome della colonna
    extra = a.get("extra") if isinstance(a.get("extra"), dict) else {}
    for k, v in extra.items():
        if v and k not in raw:
            raw[k] = v
    # foto aggiunta a mano: URL servito da /media/
    img = None
    if ntype == "photo" and a.get("value"):
        img = "/media/" + quote(str(a["value"]).replace("\\", "/").lstrip("/"))
    fields = a.get("fields") if isinstance(a.get("fields"), dict) else {}
    if ntype in onto.TYPES and fields:
        raw.update(onto.raw_of(ntype, fields))      # i campi leggibili nella scheda
    if a.get("target"):
        ntype = "target"                  # persona evidenziata come target
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
        node["url"] = a["url"]        # apribile con Alt+Click
    if note:
        node["note"] = note
    if ntype in onto.TYPES:
        node["ficon"] = onto.icon_of(ntype, fields)   # es. cannabis, siringa, passaporto
    return node


EDGE_ARROWS = {"none", "target", "source", "both"}
# tutte le forme di linea di Cytoscape adatte a un collegamento con frecce
# (resta fuori solo 'haystack', che le frecce non le disegna)
EDGE_CURVES = {"bezier", "straight", "unbundled-bezier", "segments",
               "round-segments", "taxi", "round-taxi", "straight-triangle"}
# forme con uno snodo / una curvatura regolabile ('bend', in pixel)
BEND_CURVES = {"unbundled-bezier", "segments", "round-segments"}
DEFAULT_BEND = 40
EDGE_LSTYLES = {"solid", "dashed", "dotted"}


def edge_props(src, prefix=""):
    """Proprieta' grafiche di un collegamento, validate.
    'src' e' la richiesta o una voce di annotations.json; 'prefix' serve per le
    voci 'added', dove le chiavi sono edge_label / edge_color / ... ."""
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
    # relazione Follow the Money: schema-arco + proprieta' (solo quelle previste)
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
    """Scrive le proprieta' in una voce di annotations.json (senza chiavi vuote)."""
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
    """Copia dell'arco con le proprieta' grafiche: solo quelle impostate, cosi'
    lo stile predefinito (o quello del tipo di relazione) resta valido."""
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
    """Imposta (o toglie, con value=None) il valore indicato dal percorso
    'a.b[0].c' usato dalle schede. Se il percorso non si risolve (chiave con
    un punto nel nome, struttura diversa) si lavora sulla chiave di primo
    livello scritta per intero."""
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
    """Valori delle schede modificati a mano (annotations.json -> 'edits').
    I file di origine non si toccano: le modifiche si applicano a una copia.
    Formato: {id: {"fields": {"<n. scheda>|<percorso>": valore o null},
                   "extra": {campo: valore}, "url": "..."}}"""
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
    """Spunta «Evidenzia come target» cambiata a mano nella modifica del nodo:
    True = il nodo diventa un target (qualunque sia il suo tipo), False = non
    lo e' piu' (un target dei dati di origine torna una persona)."""
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
    """Applica note e cancellazioni al grafo in cache, senza ricostruirlo.
    Ritorna una copia: la cache resta il grafo 'puro' dei dati di origine."""
    ann = load_annotations()
    notes, deleted = ann["notes"], deleted_ids(ann)
    labels = ann.get("labels") or {}

    nodes = []
    for n in graph["nodes"]:
        if n["id"] in deleted:
            continue
        # un nodo fuso resta valido se l'id cancellato era solo un suo alias
        if deleted and any(a in deleted for a in (n.get("alias_ids") or [])):
            n = dict(n)
            n["alias_ids"] = [a for a in n["alias_ids"] if a not in deleted]
        note = notes.get(n["id"])
        if note:
            n = dict(n)
            n["note"] = note
        nodes.append(n)

    # nodi aggiunti a mano dalle schede
    by_id = {n["id"]: n for n in nodes}
    pos = {n["id"]: i for i, n in enumerate(nodes)}
    manual_edges = []
    scheda_di = {}                  # id di una scheda aggiunta -> id del suo nodo
    for a in ann.get("added", []):
        nid = str(a.get("id") or "")
        if not nid or nid in deleted:
            continue
        # scheda in piu' di un nodo esistente: id '<id del nodo>~xxxxxx'
        base = nid.split("~")[0] if "~" in nid else nid
        if base in by_id:
            # il nodo c'e' gia' (dai JSON importati o da una voce precedente):
            # la voce diventa una SCHEDA in piu' di quel nodo
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
                # la voce manuale da' nome e tipo al nodo (il nodo "dei dati" con
                # lo stesso id e' l'aggancio di un JSON importato)
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

    # collegamenti creati a mano fra nodi esistenti
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
            # id gia' usato (vecchi collegamenti senza id proprio): suffisso
            # DETERMINISTICO, cosi' l'arco mantiene lo stesso id a ogni lettura
            k = 2
            while f"{eid}_m{k}" in have:
                k += 1
            eid = f"{eid}_m{k}"
            e["id"] = eid
        have.add(eid)
        edges.append(e)
    # etichette rinominate a mano (e fusione delle schede che ne risulta)
    g = relabel({"nodes": nodes, "edges": edges}, labels)
    apply_node_edits(g, ann.get("edits") or {})
    apply_targets(g, ann.get("targets") or {})
    # stesso indirizzo (citta', via, civico) = un nodo; stessa via = tratteggio
    g = merge_places(g)
    # solo nome e cognome ~ stessa persona con la data di nascita: tratteggio
    g = link_persons(g)

    # Traslitterazione dei nodi aggiunti a mano: non passano da build_graph,
    # quindi un nome in alfabeto non latino non avrebbe il suo nodo latino.
    # Offline (solo ICU/dizionario) per essere immediata e senza toccare i
    # file; il raffinamento col chatbot avviene alla ricarica o col pulsante.
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
    """Grafo completo (dati + annotazioni), ricostruito solo se i dati sono cambiati.
    Senza un caso aperto il grafo e' vuoto e lo segnala ('no_case')."""
    if not store.current_case():
        return {"nodes": [], "edges": [], "no_case": True}
    key = data_signature()
    if _cache["key"] != key:
        _cache["graph"] = build_graph()
        _cache["key"] = key
    return apply_annotations(_cache["graph"])


@app.route("/api/graph")
def api_graph():
    try:
        g = dict(current_graph())
        g["translit_mode"] = translit_mode()
        return jsonify(g)
    except Exception as e:
        logging.error("Errore in /api/graph", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/reload", methods=["POST"])
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


@app.route("/api/brand-icons")
def api_brand_icons():
    """Sigle dei marchi che hanno l'icona in static/vendor/icons/.
    Il front-end la usa per non chiedere file inesistenti: le icone stanno
    DENTRO l'eseguibile, non su internet, e non tutti i marchi ce l'hanno
    (per quelli che mancano resta il badge con l'iniziale)."""
    cartella = os.path.join(RES_DIR, "static", "vendor", "icons")
    try:
        nomi = [f[:-4] for f in os.listdir(cartella) if f.lower().endswith(".svg")]
    except OSError:
        nomi = []
    return jsonify(sorted(nomi))


@app.route("/api/translit/status")
def api_translit_status():
    """Quante parole restano da traslitterare e se il chatbot e' utilizzabile."""
    wdict = load_word_dict()
    todo = parole_da_traslitterare(current_graph(), wdict)
    return jsonify({
        "enabled": chatbot_ready(), "auto": bool(CHATBOT["auto"]),
        "model": CHATBOT["model"], "endpoint": CHATBOT["endpoint"],
        "engine": TRANSLIT_ENGINE or "", "todo": len(todo),
        "done": sum(1 for v in wdict.values() if str(v or "").strip()),
        "total": len(wdict),
        "down": bool(time.time() < _bot["down_until"]),
        "reason": _bot["reason"],
        "mode": translit_mode(),
    })


@app.route("/api/translit/mode", methods=["GET", "POST"])
def api_translit_mode():
    """Dove va la forma latina: 'attribute' (nel nodo) o 'nodes' (gemelli)."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        mode = str(data.get("mode") or "").strip()
        if mode not in TRANSLIT_MODES:
            return jsonify({"error": "modalita' non valida"}), 400
        store.set_gmeta("translit_mode", mode)
        _cache["key"] = None                   # il grafo va ricostruito
        logging.info(f"Traslitterazione: modalita' {mode}")
    return jsonify({"ok": True, "mode": translit_mode()})


@app.route("/api/translit/ai", methods=["POST"])
def api_translit_ai():
    """Fa traslitterare al chatbot tutte le parole ancora scoperte.
    Se il chatbot non risponde lo dice e non cambia niente."""
    if not chatbot_ready():
        return jsonify({"error": "AI disattivata o endpoint non impostato "
                                 "(pannello Intelligenza artificiale)"}), 400
    wdict = load_word_dict()
    todo = parole_da_traslitterare(current_graph(), wdict)
    if not todo:
        return jsonify({"ok": True, "tradotte": 0, "restano": 0, "errore": ""})
    stat = ai_fill_translit(todo, force=True,
                            budget=max(CHATBOT["budget"], 120),
                            max_words=max(CHATBOT["max_words"], len(todo)))
    if not stat["tradotte"] and stat["errore"]:
        return jsonify({"error": stat["errore"]}), 502
    if stat["tradotte"]:
        _cache["key"] = None                  # le etichette latine vanno rifatte
    stat["ok"] = True
    return jsonify(stat)


# ==================== DIZIONARIO DI TRASLITTERAZIONE (a mano) ====================
# La finestra "Dizionario" del pannello: elenco delle parole non latine viste
# nel grafo (in sospeso, tradotte a mano, tradotte dall'AI), modifica in riga,
# import/export CSV. Un valore scritto a mano vince sempre sul motore
# automatico e sull'AI (store.translit_set); vuoto = torna "da tradurre".
# Ogni modifica incrementa translit_version: il grafo si ricostruisce da solo.

@app.route("/api/translit/words")
def api_translit_words():
    """Pagina del dizionario. Parametri: q (filtro su parola o valore),
    source (pending | manual | ai | vuoto = tutte), limit, offset."""
    q = str(request.args.get("q") or "").strip()[:80]
    source = str(request.args.get("source") or "").strip()
    if source not in ("", "pending", "manual", "ai"):
        source = ""
    try:
        limit = max(1, min(int(request.args.get("limit", 200)), 2000))
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        limit, offset = 200, 0
    rows = store.translit_rows(source or None, q, limit + 1, offset)
    more = len(rows) > limit
    rows = rows[:limit]
    for r in rows:
        # proposta del motore automatico, mostrata come suggerimento
        r["auto"] = _auto(r["word"]) if not str(r.get("value") or "").strip() else ""
    return jsonify({"rows": rows, "more": more, "offset": offset,
                    "counts": store.translit_counts(),
                    "engine": TRANSLIT_ENGINE or ""})


@app.route("/api/translit/set", methods=["POST"])
def api_translit_set():
    """Scrive (o svuota) la traslitterazione di una parola: {word, value}."""
    data = request.get_json(silent=True) or {}
    word = re.sub(r"\s+", " ", str(data.get("word") or "")).strip()[:120]
    value = re.sub(r"\s+", " ", str(data.get("value") or "")).strip()[:120]
    if not word:
        return jsonify({"error": "parola mancante"}), 400
    if not script_of(word):
        return jsonify({"error": "la parola e' gia' in caratteri latini"}), 400
    if value and script_of(value):
        return jsonify({"error": "la traslitterazione deve essere in caratteri latini"}), 400
    store.translit_set(word, value)
    logging.info(f"Dizionario: {word!r} -> {value!r}" if value else f"Dizionario: {word!r} da tradurre")
    return jsonify({"ok": True, "word": word, "value": value,
                    "source": "manual" if value else "pending"})


@app.route("/api/translit/delete", methods=["POST"])
def api_translit_delete():
    """Toglie la parola dal dizionario: tornera' in sospeso se ricompare."""
    data = request.get_json(silent=True) or {}
    word = str(data.get("word") or "").strip()
    if not word:
        return jsonify({"error": "parola mancante"}), 400
    n = store.translit_delete(word)
    return jsonify({"ok": True, "deleted": n})


@app.route("/api/translit/collect", methods=["POST"])
def api_translit_collect():
    """Mette in sospeso TUTTE le parole non latine presenti nel grafo (non solo
    quelle delle scritture ambigue), cosi' si possono correggere a mano anche
    le romanizzazioni automatiche (cinese, cirillico...)."""
    words = set()
    for n in current_graph().get("nodes", []):
        if n.get("ntype") == "latin":
            continue
        for lab in [n.get("label")] + list(n.get("aliases") or []):
            for w in WORD_RE.findall(str(lab or "")):
                if script_of(w):
                    words.add(w)
    added = write_pending(words)
    return jsonify({"ok": True, "added": added, "total": len(words)})


@app.route("/api/translit/import", methods=["POST"])
def api_translit_import():
    """Importa un CSV 'parola;traslitterazione' (anche , o tab; con o senza
    intestazione). Le righe diventano voci MANUALI; una riga con il valore
    vuoto rimette la parola in sospeso. Corpo: {text} oppure {data: base64}."""
    import csv
    import io
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "")
    if not text and data.get("data"):
        try:
            text = _decode_upload(data).decode("utf-8-sig")
        except (NodeError, UnicodeDecodeError) as e:
            return jsonify({"error": f"file illeggibile: {e}"}), 400
    text = text.lstrip("\ufeff")
    if not text.strip():
        return jsonify({"error": "file vuoto"}), 400
    sample = text[:3000]
    delim = max(";,\t|", key=sample.count) if any(d in sample for d in ";,\t|") else ";"
    done, skipped, errors = 0, 0, []
    for i, cells in enumerate(csv.reader(io.StringIO(text), delimiter=delim), 1):
        if not cells or not str(cells[0]).strip():
            continue
        word = str(cells[0]).strip()
        value = str(cells[1]).strip() if len(cells) > 1 else ""
        if i == 1 and word.lower() in ("parola", "word", "originale", "original"):
            continue                                    # intestazione
        if not script_of(word) or (value and script_of(value)):
            skipped += 1
            if len(errors) < 10:
                errors.append(f"riga {i}: {word} -> {value}")
            continue
        store.translit_set(word, value)
        done += 1
    logging.info(f"Dizionario: importate {done} voci, {skipped} scartate")
    return jsonify({"ok": True, "imported": done, "skipped": skipped, "errors": errors})


@app.route("/api/translit/export")
def api_translit_export():
    """Scarica tutto il dizionario come CSV (parola;traslitterazione;origine;scrittura)."""
    import csv
    import io
    from flask import Response
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow(["parola", "traslitterazione", "origine", "scrittura", "aggiornata"])
    for r in store.translit_rows(limit=200000):
        w.writerow([r["word"], r["value"], r["source"], r["script"], r["updated_at"]])
    data = "\ufeff" + out.getvalue()                  # BOM: Excel apre l'UTF-8 correttamente
    return Response(data, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=traslitterazioni.csv"})


@app.route("/api/note", methods=["POST"])
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


@app.route("/api/node/label", methods=["POST"])
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


@app.route("/api/node/delete", methods=["POST"])
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


class NodeError(ValueError):
    """Valore non valido per il tipo di nodo richiesto (messaggio per l'utente)."""


def _json_obj(v):
    if isinstance(v, dict):
        return v
    try:
        d = json.loads(v) if v else {}
        return d if isinstance(d, dict) else {}
    except (TypeError, ValueError):
        return {}


def onto_fields(ntype, data):
    """Campi di un elemento ontologico dalla richiesta: oggetto 'fields' (modulo,
    AI) oppure il solo 'value', che va nel campo principale del tipo."""
    fields = onto.clean_fields(ntype, _json_obj(data.get("fields")))
    main = onto.TYPES[ntype]["value"]
    value = re.sub(r"\s+", " ", str(data.get("value") or "")).strip()
    if value and not fields.get(main):
        fields.update(onto.clean_fields(ntype, {main: value}))
    return fields


def _resolve_onto(ntype, data, value):
    """Arma, stupefacente, assegno, documento... Con i campi identificativi
    compilati (matricola, numero, IBAN...) l'oggetto e' univoco: reinserirlo
    aggiunge una scheda allo stesso nodo. Senza, ogni inserimento e' un
    reperto a se' (nodo nuovo)."""
    fields = onto_fields(ntype, data)
    if not fields:
        raise NodeError("compila almeno un campo")
    ident = onto.ident_of(ntype, fields)
    nid = f"{ntype}:{ident}" if ident else f"{ntype}:#{uuid.uuid4().hex[:10]}"
    label = str(data.get("label") or "").strip() or onto.label_of(ntype, fields)
    value = fields.get(onto.TYPES[ntype]["value"]) or label
    return nid, label, ntype, ntype, str(value)


def resolve_node(data, parent=""):
    """Da tipo + valore (+ campi facoltativi) ricava l'identita' del nodo con
    le STESSE regole del grafo, cosi' un valore gia' presente non crea un
    doppione. Ritorna (nid, label, platform, ntype, value); NodeError se il
    valore non e' valido. 'parent' serve solo alle localita' generiche, che
    restano legate al nodo da cui sono state aggiunte."""
    ntype = str(data.get("ntype") or "").strip().lower()
    value = str(data.get("value") or "").strip()
    platform = str(data.get("platform") or "").strip().lower()
    if ntype in ("name", "target", "person"):
        # persona: cognome e nome (o il nome intero in 'value') + nascita
        cognome = re.sub(r"\s+", " ", str(data.get("cognome") or "")).strip()
        nome = re.sub(r"\s+", " ", str(data.get("nome") or "")).strip()
        value = f"{cognome} {nome}".strip() or value
        ntype = "name"
    if ntype in onto.TYPES:
        return _resolve_onto(ntype, data, value)
    if not value and ntype != "text":
        raise NodeError("valore mancante")
    if ntype == "phone":
        digits = re.sub(r"\D", "", value)
        if len(digits) < 6:
            raise NodeError("numero di telefono non valido")
        nid, label, platform = "phone:" + digits, value, "phone"
    elif ntype == "email":
        if "@" not in value or "." not in value.split("@")[-1]:
            raise NodeError("indirizzo email non valido")
        nid, label, platform = "email:" + value.lower(), value, "email"
    elif ntype == "username":
        value = value.lstrip("@")
        nid, label = "user:" + value.lower(), value
        platform = platform or "username"
    elif ntype == "name":
        if len(value) < 2 or not person_key(value):
            raise NodeError("nome troppo corto")
        nascita = parse_birth(data.get("nascita"))
        nid, label, platform = person_id(value, nascita), person_label(value, nascita), "name"
    elif ntype == "place":
        # località: città (obbligatoria) + via, civico e coordinate facoltativi
        citta = value
        street, civico = _via_civico(data)
        via = f"{street} {civico}".strip()
        lat = str(data.get("lat") or "").strip().replace(",", ".")
        lon = str(data.get("lon") or "").strip().replace(",", ".")
        for c, nome in ((lat, "latitudine"), (lon, "longitudine")):
            if c and not re.fullmatch(r"-?\d{1,3}(\.\d+)?", c):
                raise NodeError(f"{nome} non valida")
        if (lat and not lon) or (lon and not lat):
            raise NodeError("servono sia latitudine sia longitudine")
        if lat and not (-90 <= float(lat) <= 90):
            raise NodeError("latitudine fuori intervallo (-90..90)")
        if lon and not (-180 <= float(lon) <= 180):
            raise NodeError("longitudine fuori intervallo (-180..180)")
        chiave = re.sub(r"\s+", " ", f"{citta} {via}".strip().casefold()).strip()
        # come nel grafo: una citta' generica resta legata alla scheda di
        # partenza, solo un recapito (indirizzo o coordinate) puo' essere
        # condiviso fra schede diverse
        if not parent or place_is_address(f"{citta} {via}".strip(), lat, lon,
                                          "address" if via else ""):
            nid = "place:" + chiave
        else:
            nid = f"place:{parent}|{chiave}"
        label = str(data.get("label") or "").strip() or \
            (f"{citta} — {via}" if via else citta)
        platform = "place"
    elif ntype == "vehicle":
        targa = re.sub(r"\s+", "", value).upper()
        if len(targa) < 3:
            raise NodeError("targa non valida")
        nid = "vehicle:" + targa
        value = targa                       # 'ab 123 cd' -> 'AB123CD'
        label = str(data.get("label") or "").strip() or value
        platform = "vehicle"
    elif ntype == "text":
        # appunto libero: l'etichetta è il titolo, il corpo sta nella scheda
        titolo = str(data.get("label") or value).strip()
        if not titolo:
            raise NodeError("titolo mancante")
        nid = "text:" + re.sub(r"[^a-z0-9]+", "-", titolo.lower()).strip("-")[:60]
        label, platform, value = titolo, "text", value or titolo
    elif ntype == "photo":
        # 'value' è il percorso relativo restituito da /api/upload
        rel = value.replace("\\", "/").lstrip("/")
        if not rel.lower().startswith("media/") or not rel.lower().endswith(PHOTO_EXT):
            raise NodeError("immagine non valida")
        if not os.path.isfile(os.path.join(DATA_DIR, *rel.split("/"))):
            raise NodeError("immagine non trovata sul server")
        nid = "photo:" + rel.lower()
        label = str(data.get("label") or "").strip() or photo_label(os.path.basename(rel))
        platform = "photo"
    elif ntype == "link":
        # collegamento generico: un URL qualsiasi con un'etichetta a scelta
        if not re.match(r"^https?://\S+$", value, re.I):
            raise NodeError("indirizzo non valido (serve http:// o https://)")
        nid = "link:" + value.rstrip("/").lower()
        label = str(data.get("label") or "").strip() or value
        platform = "link"
    elif ntype == "account":
        if not platform:
            raise NodeError("piattaforma non riconosciuta")
        value = value.lstrip("@")
        nid, label = f"acct:{platform}:{value.lower()}", value
    else:
        raise NodeError(f"tipo non supportato: {ntype}")
    return nid, label, platform, ntype, value


def same_place_id(g, city, data):
    """Id di un luogo gia' nel grafo con la stessa citta', via e civico
    (confronto normalizzato), altrimenti None."""
    street, civ = _via_civico(data)
    key = (norm_city(city), norm_street(street), norm_civico(civ))
    if not all(key):
        return None
    luoghi = [(n["id"], place_parts(n)) for n in g["nodes"] if n.get("ntype") == "place"]
    luoghi = [(i, p) for i, p in luoghi if p and p[0] and p[1]]
    # stesse regole di merge_places: iniziali sciolte se la via completa e' unica
    canon = canon_streets({(c, s) for _, (c, s, _v) in luoghi} | {key[:2]})
    ck = (key[0], canon[key[:2]], key[2])
    return next((i for i, (c, s, v) in luoghi if (c, canon[(c, s)], v) == ck), None)


def maps_url(city, street="", civico=""):
    """Ricerca Google Maps: 'Via Santo Stefano 55, Brescia'."""
    via = f"{street} {civico}".strip()
    q = ", ".join(p for p in (via, str(city or "").strip()) if p)
    return "https://www.google.com/maps/search/?api=1&query=" + quote(q)


def _via_civico(data):
    """(via, civico) di una richiesta: il civico dal suo campo o, se manca,
    staccato dal fondo dell'indirizzo ('Via Roma 12' -> 'Via Roma', '12')."""
    addr = re.sub(r"\s+", " ", str(data.get("address") or "")).strip(" ,")
    civ = re.sub(r"\s+", "", str(data.get("civico") or ""))
    civ = re.sub(r"^(?:n|nr|no|num|numero|civico)\.?", "", civ, flags=re.I)
    street, c2 = split_civico(addr)
    if civ and c2 and norm_civico(civ) != norm_civico(c2):
        street = addr                       # il numero nell'indirizzo non e' il civico
    # tipo di via scelto dalla tendina: si antepone, se il nome non ne ha gia' uno
    tipo = re.sub(r"\s+", " ", str(data.get("toponimo") or "")).strip()
    if tipo and street and not _TYPE_HEAD.match(_fold(street)) \
            and _fold(tipo) in STREET_TYPES:
        street = f"{tipo} {street}"
    return street, civ or c2


def _truthy(v):
    return v is True or str(v or "").strip().lower() in ("1", "true", "si", "sì", "yes", "on", "x")


def new_added_entry(nid, label, platform, ntype, value, data, parent, now):
    """Voce di annotations.json per un nodo creato a mano."""
    entry = {
        "id": nid, "label": str(data.get("label") or label)[:300], "ntype": ntype,
        "platform": platform, "parent": parent, "value": value,
        "url": str(data.get("url") or "")[:500], "rel": "manuale", "at": now,
    }
    if data.get("text"):
        entry["text"] = str(data["text"])[:20000]
    if data.get("note") and ntype != "text":
        entry["note"] = str(data["note"])[:4000]
    extra = data.get("extra") if isinstance(data.get("extra"), dict) else {}
    extra = {str(k).strip()[:120]: str(v).strip()[:20000] for k, v in extra.items()
             if str(k).strip() and str(v).strip()}
    if extra:
        entry["extra"] = extra                     # colonne libere del file importato
    if ntype in onto.TYPES:
        entry["fields"] = onto_fields(ntype, data)
    if ntype == "vehicle":
        colore = re.sub(r"\s+", " ", str(data.get("colore") or "")).strip()[:40]
        if colore:
            entry["colore"] = colore[:1].upper() + colore[1:]    # solo nella scheda
    if ntype == "name":
        for k in ("cognome", "nome"):
            v = re.sub(r"\s+", " ", str(data.get(k) or "")).strip()[:120]
            if v:
                entry[k] = v
        nascita = parse_birth(data.get("nascita"))
        if nascita:
            entry["nascita"] = nascita
        if _truthy(data.get("target")):
            entry["target"] = True           # evidenziato come target
    if ntype == "place":
        entry["citta"] = value
        street, civico = _via_civico(data)
        if street:
            entry["indirizzo"] = street[:300]
        if civico:
            entry["civico"] = civico[:20]
        if data.get("lat") and data.get("lon"):
            entry["lat"] = str(data["lat"]).replace(",", ".")
            entry["lon"] = str(data["lon"]).replace(",", ".")
            # con le coordinate il nodo si apre direttamente sulla mappa
            entry["url"] = ("https://www.google.com/maps/search/?api=1&query="
                            f"{entry['lat']},{entry['lon']}")
        elif not entry.get("url"):
            entry["url"] = maps_url(value, street, civico)
    return entry


def _translit_new_labels(labels):
    """Traslitterazione: se un'etichetta e' in alfabeto non latino il nodo avra'
    il suo nodo latino (creato da apply_annotations). Con l'AI attiva si fanno
    tradurre SUBITO le parole nuove, prima di rispondere al client: cosi' il
    nodo latino nasce gia' con la forma dell'AI e non con quella del motore
    locale (se l'AI non risponde si ripiega su quello). Ritorna il primo
    alfabeto non latino trovato."""
    labels = [str(l or "") for l in labels]
    scr = next((s for s in map(script_of, labels) if s), "") or ""
    if scr and chatbot_ready():
        nuove = parole_da_traslitterare({"nodes": [{"label": l} for l in labels]})
        if nuove:
            ai_fill_translit(nuove)
    return scr


@app.route("/api/node/add", methods=["POST"])
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


# ======================= IMPORTAZIONE MASSIVA (CSV / EXCEL) =======================
# Ogni riga descrive un nodo, oppure due nodi e il collegamento fra loro:
#   nome1, tipo1, collegamento, nome2, tipo2  (+ colonne facoltative)
# Le intestazioni si riconoscono in italiano e in inglese; senza intestazione
# si usano le prime cinque colonne in quest'ordine.

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
    """Da un URL di profilo ricava (piattaforma, handle); None se non e' un social."""
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


# intestazioni riconosciute (normalizzate: minuscole, senza accenti né spazi)
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
    "fields": {"campi", "fields", "dati"},            # JSON dei campi di un tipo ontologico
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
    """Mappa le intestazioni: {indice colonna: chiave}. Chiavi come 'name1',
    'type2', 'url1', 'rel', 'arrow'. None se la riga non sembra un'intestazione."""
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
            # colonna senza numero: vale per il primo nodo se non e' gia' preso
            side = "1" if f"{key}1" not in out.values() else "2"
        out[i] = f"{key}{side}"
    # «da / from / source» e «a / to / destination» valgono come nome del nodo
    # solo se quel lato non ha gia' una colonna nome: altrimenti (es. una colonna
    # "Source" con la provenienza del dato) restano da assegnare a mano
    for i, k in sides.items():
        if k not in out.values():
            out[i] = k
    # la stessa chiave su due colonne: vale la prima, l'altra resta libera
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
    """Dati di un lato della riga -> richiesta per resolve_node (o None)."""
    g = lambda k: str(row.get(f"{k}{side}") or "").strip()
    name, url = g("name"), g("url")
    if not name and not url:
        return None
    t = _norm(g("type"))
    plat = _norm(g("platform"))
    if t in SOCIAL_PLATFORMS:                     # tipo = nome del social
        ntype, plat = "account", t
    else:
        ntype = next((k for k, al in _TYPE_ALIASES.items() if t in al), None) if t else None
        if t and ntype is None:
            ntype = onto.type_of(g("type"))         # arma, stupefacente, assegno...
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


def plan_rows(rows):
    """Interpreta righe gia' "a dizionario" ({'name1', 'type1', 'rel', ...}):
    per ognuna i due nodi (id, etichetta, tipo) e il collegamento. Non scrive
    niente: serve all'anteprima e all'importazione (da file o dall'AI).
    Un lato puo' indicare direttamente un nodo esistente con 'id1' / 'id2'."""
    g = current_graph()
    have = {n["id"]: n for n in g["nodes"]}
    plan = []
    for row in rows:
        item = {"row": int(row.get("_row") or len(plan) + 1), "raw": row,
                "nodes": [], "error": ""}
        try:
            for side in ("1", "2"):
                fixed = str(row.get(f"id{side}") or "").strip()
                if fixed:                              # nodo gia' nel grafo
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


# colonne che l'utente puo' assegnare nella procedura guidata (oltre a
# "extra1:<nome>" / "extra2:<nome>", che finiscono nella scheda del nodo)
IMPORT_NODE_KEYS = ("name", "type", "label", "url", "platform", "text", "cognome", "nascita",
                    "colore", "flag", "address", "civico", "lat", "lon", "note")
IMPORT_EDGE_KEYS = ("rel", "arrow", "curve", "color", "lstyle", "width", "ftm", "ftm_props")


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


def plan_import(table, mapping=None, has_header=None, defaults=None):
    """Righe lette da un file (liste di celle) -> piano di importazione.
    Senza 'mapping' le colonne si riconoscono dalle intestazioni (o, senza
    intestazione, nell'ordine fisso nome1, tipo1, collegamento, nome2, tipo2);
    con 'mapping' ({indice colonna: chiave}) vale la scelta dell'utente."""
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
        if not header:                      # senza intestazione: ordine fisso
            header = dict(enumerate(["name1", "type1", "rel", "name2", "type2"]))
    if "name1" not in header.values():
        raise NodeError("serve una colonna con il nome (o il valore) del nodo 1")
    first = 2 if has_header else 1          # numero della prima riga di dati
    body = table[1:] if has_header else table
    if len(body) > IMPORT_MAX_ROWS:
        raise NodeError(f"troppe righe (massimo {IMPORT_MAX_ROWS})")
    rows = []
    for i, cells in enumerate(body):
        row = {}
        for c, k in header.items():
            v = cells[c] if c < len(cells) else ""
            if k.startswith(("extra1:", "extra2:")):          # campo della scheda
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
    """Re-import: aggiorna la voce esistente di un nodo (campi, colonne libere,
    etichetta) invece di aggiungere una scheda."""
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
    """Id Follow the Money di una riga importata, se c'e'."""
    f = spec.get("fields") if isinstance(spec.get("fields"), dict) else {}
    if f.get("ftmId"):
        return str(f["ftmId"])
    ex = spec.get("extra") if isinstance(spec.get("extra"), dict) else {}
    return str(ex.get("FtM id") or "")


def _ftm_schema_of(spec, ntype):
    """Schema FtM di una riga importata: dal tipo nativo o dalla scheda."""
    sc = ftm.FTM_SCHEMA_OF.get(ntype)
    if sc:
        return sc
    ex = spec.get("extra") if isinstance(spec.get("extra"), dict) else {}
    return str(ex.get("Schema FtM") or "")


def commit_plan(plan, skip=(), update=False, ftm_dataset=None):
    """Scrive in annotations.json i nodi e i collegamenti del piano. Righe gia'
    importate non creano doppioni (stesso nodo = stesso id; stesso collegamento
    con lo stesso nome fra gli stessi nodi = saltato).
    update=True (re-import Follow the Money): un nodo gia' presente viene
    AGGIORNATO (campi, colonne libere, etichetta) invece di ricevere una scheda
    in piu'; ftm_dataset: nome del dataset registrato con gli id FtM."""
    ann = load_annotations()
    by_id = {str(x.get("id")): x for x in ann["added"]}
    updated, ftm_pairs = 0, []
    known = store.ftm_map() if update else {}       # id FtM gia' nel caso -> nodo
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    g0 = current_graph()
    have = {n["id"] for n in g0["nodes"]}
    added_ids = {str(x.get("id")) for x in ann["added"]}
    in_commit, remap = set(), {}            # luoghi gia' trattati in questo import
    link_keys = {(str(l.get("a")), str(l.get("b")), str(l.get("label") or ""))
                 for l in ann["links"]}
    # anche i collegamenti nati con un nodo aggiunto a mano (voce 'added' con
    # 'parent'): altrimenti un re-import li creerebbe una seconda volta
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
                    remap[nid] = known[fid]          # stessa entita' FtM, nodo gia' nel caso
                    nid = known[fid]
            # stessa riga ripetuta (l'AI cita lo stesso nodo in piu' collegamenti):
            # conta una volta sola; dati diversi (due righe con la stessa targa)
            # sono schede diverse
            firma = (nid, json.dumps(spec, sort_keys=True, ensure_ascii=False) if spec else "")
            if (n["ntype"] in ("place", "vehicle") or n["ntype"] in onto.TYPES)                     and spec and firma not in in_commit:
                in_commit.add(firma)
                same = (same_place_id(g0, spec["value"], spec) if n["ntype"] == "place" else None)                     or remap.get(nid) or (nid if nid in have else None)
                if same and update and same in by_id:
                    # re-import: stesso nodo, dati aggiornati, nessuna scheda in piu'
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
                    # luogo / veicolo gia' presente: una scheda in piu' nel nodo
                    # esistente (voce con id proprio '<id>~xxxxxx')
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
    if made_nodes:                               # importazione e nodi proposti dall'AI
        _translit_new_labels([x.get("label") for x in ann["added"]
                              if str(x.get("id")) in set(touched)])
    return {"ok": True, "nodes": made_nodes, "links": made_links, "updated": updated,
            "same_links": same_links, "errors": errors,
            "ids": list(dict.fromkeys(touched))}


def _plan_json(plan):
    """Piano per il client (senza i dati grezzi interni)."""
    return [{k: v for k, v in it.items() if k != "raw"} for it in plan]


def _decode_upload(data):
    import base64
    raw = str(data.get("data") or "")
    m = re.match(r"^data:[^;,]*(;base64)?,(.*)$", raw, re.S)
    try:
        blob = base64.b64decode(m.group(2)) if m else base64.b64decode(raw)
    except Exception:
        raise NodeError("file illeggibile")
    if len(blob) > 20 * 1024 * 1024:
        raise NodeError("file troppo grande (max 20 MB)")
    return blob


# ================= IMPORTAZIONE DI JSON DA APP TERZE (export OSINT) =================
# Il file si aggancia a un nodo (di norma il target): i record diventano nodi e
# collegamenti con le stesse regole di sempre (build_graph). Il contenuto sta
# nel database, nessun file o cartella su disco.
IMPORT_MAX_MB = 25


@app.route("/api/imports")
def api_imports_list():
    return jsonify({"items": store.list_imports(str(request.args.get("anchor") or "") or None)})


@app.route("/api/imports/add", methods=["POST"])
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


@app.route("/api/imports/delete", methods=["POST"])
def api_imports_delete():
    data = request.get_json(silent=True) or {}
    try:
        iid = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"error": "id mancante"}), 400
    if not store.delete_import(iid):
        return jsonify({"error": "import non trovato"}), 404
    return jsonify({"ok": True, "id": iid})


@app.route("/api/import/columns", methods=["POST"])
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


@app.route("/api/import/preview", methods=["POST"])
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


@app.route("/api/import/commit", methods=["POST"])
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


# ======================= IMPORTAZIONE FOLLOW THE MONEY =======================
# File di entita' FtM anche grandi (dataset interi): niente anteprima riga per
# riga, ma conteggi per schema (ispezione), filtri, e importazione in un thread
# a lotti con avanzamento. Gli id FtM finiscono nella tabella ftm_ids del caso:
# un re-import aggiorna i nodi invece di duplicarli.
FTM_MAX_MB = 200
FTM_BATCH = 2000
_ftm_job = {"running": False, "finished": False, "error": "", "done": 0, "total": 0,
            "nodes": 0, "links": 0, "updated": 0, "same_links": 0, "errors": 0, "stage": ""}
_ftm_lock = threading.Lock()


def _ftm_blob(data):
    blob = _decode_upload(data)
    if len(blob) > FTM_MAX_MB * 1024 * 1024:
        raise NodeError(f"file troppo grande (max {FTM_MAX_MB} MB)")
    return blob


def _ftm_source(data):
    """What an FtM import reads: ("bundle", path|bytes) for a Cognitor bundle, or
    ("blob", bytes) for a file of entities. {path} reads a file of this computer
    (the program runs locally), without the 20 MB limit of the upload: a bundle with
    photos is larger. {data} is the upload as before."""
    path = str(data.get("path") or "").strip().strip('"')
    if path:
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isfile(path):
            raise NodeError(f"file non trovato: {path}")
        if ftm_bundle.is_bundle(path):
            return "bundle", path
        if os.path.getsize(path) > FTM_MAX_MB * 1024 * 1024:
            raise NodeError(f"file troppo grande (max {FTM_MAX_MB} MB)")
        with open(path, "rb") as f:
            return "blob", f.read()
    blob = _decode_upload(data)
    if blob[:2] == b"PK" and ftm_bundle.is_bundle(blob):
        return "bundle", blob
    if len(blob) > FTM_MAX_MB * 1024 * 1024:
        raise NodeError(f"file troppo grande (max {FTM_MAX_MB} MB)")
    return "blob", blob


def _sources_folder():
    """The folder of the sources the search reads now (default: 'fonti')."""
    idx = sources_index()
    return _src.resolved_folder(idx, BASE_DIR, SOURCES_DEFAULT) if idx else SOURCES_DEFAULT


def _ftm_mapping(header):
    """Mappatura delle colonne prodotte da ftm.rows_from_entities: quelle
    riconosciute dall'intestazione, le altre come campi liberi del nodo 1 o 2."""
    auto = map_header(header) or {}
    out = {}
    for i, name in enumerate(header):
        k = auto.get(i)
        if k:
            out[i] = k
            continue
        name = str(name)
        side = "2" if name.endswith("2") else "1"
        # la chiave della scheda e' il nome senza il suffisso del lato, cosi' lo
        # stesso valore ha la stessa chiave da nodo 1 o da nodo 2 (re-import stabile)
        out[i] = f"extra{side}:{name[:-1] if name[-1:] in '12' else name}"
    return out


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
        logging.error(f"Bundle FtM illeggibile: {e}")
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
            raise NodeError("nessuna entita' corrisponde ai filtri")
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
        logging.info(f"Importazione FtM: {_ftm_job['nodes']} nodi, {_ftm_job['links']} collegamenti, "
                     f"{_ftm_job['updated']} aggiornati")
    except Exception as e:
        logging.error(f"Importazione FtM fallita: {e}", exc_info=not isinstance(e, NodeError))
        _ftm_job["error"] = str(e)
    finally:
        _ftm_job["running"] = False
        _ftm_job["finished"] = True


@app.route("/api/ftm/inspect", methods=["POST"])
def api_ftm_inspect():
    """Conteggi per schema e dataset di un file FtM. Corpo: {filename, data}."""
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


@app.route("/api/ftm/import", methods=["POST"])
def api_ftm_import():
    """Avvia l'importazione in un thread. Corpo: {data, schemas: [...], text,
    max_entities, connected_only, dataset}. Avanzamento: /api/ftm/progress."""
    data = request.get_json(silent=True) or {}
    try:
        kind, src = _ftm_source(data)
        if kind == "bundle":
            with ftm_bundle.Bundle(src):          # verified before the thread starts
                pass
    except (NodeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    if not store.current_case():
        return jsonify({"error": "nessun caso aperto"}), 400
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
            return jsonify({"error": "importazione gia' in corso", "running": True}), 409
        _ftm_job.update({"running": True, "finished": False, "error": "", "done": 0, "total": 0,
                         "nodes": 0, "links": 0, "updated": 0, "same_links": 0, "errors": 0,
                         "stage": "parse", "images": 0, "images_refused": 0, "transcripts": 0,
                         "sources_scan": False})
    target = _run_bundle_import if kind == "bundle" else _run_ftm_import
    threading.Thread(target=target, args=(src, opts), daemon=True).start()
    return jsonify({"started": True})


@app.route("/api/ftm/progress")
def api_ftm_progress():
    return jsonify(dict(_ftm_job))


@app.route("/api/ftm/export", methods=["GET", "POST"])
def api_ftm_export():
    """Il caso (o i nodi indicati in {ids}) come entita' Follow the Money, in
    righe JSON leggibili da Aleph, OpenSanctions e dalla CLI ftm.
    ?summary=1 ritorna solo il riepilogo (quanti nodi, quanti senza schema)."""
    from flask import Response
    data = request.get_json(silent=True) or {} if request.method == "POST" else {}
    only = {str(x) for x in (data.get("ids") or [])} or None
    g = current_graph()
    if g.get("no_case"):
        return jsonify({"error": "nessun caso aperto"}), 400
    ann = load_annotations()
    entries = {str(x.get("id")): x for x in ann["added"]}
    ents, summary = ftm.export_entities(g, entries, store.ftm_by_node(), only)
    new_ids = summary.pop("new_ids", [])
    if request.args.get("summary") or data.get("summary"):
        return jsonify(dict(summary, ok=True))
    if new_ids:                                     # il re-import dell'export ricade sugli stessi nodi
        store.ftm_set((f, n, sc, "export") for f, n, sc in new_ids)
    body = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in ents)
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", (store.get_case(store.current_case()) or {}).get("name") or "caso")
    logging.info(f"Esportazione FtM: {summary['nodes']} nodi, {summary['links']} collegamenti")
    return Response(body, mimetype="application/json; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename={name}.ftm.json",
                             "X-Ftm-Summary": json.dumps(summary)})


# ======================= VIDEO TRANSCRIPTION (1.6.0) =======================
# The modules of Cognitor in audio/ (GPL, optional packages of requirements-audio.txt):
# faster-whisper, diarization, translation. A transcribed video becomes the same
# Follow the Money entities as a Cognitor bundle (transcripts.py) and goes through the
# same import: a second transcription of the same file updates the same nodes.
# Everything runs on this computer; the models download once, on first use.
import audio as _audio
import transcripts as _transcripts

TRANSCRIPTS_DIRNAME = "transcripts"
WHISPER_MODELS = ("tiny", "base", "small", "medium", "large-v3")
_tr_job = {"running": False, "finished": False, "error": "", "stage": "", "done": 0, "total": 0,
           "log": [], "result": None, "file": ""}
_tr_lock = threading.Lock()
_tr_stop = threading.Event()


def _tr_log(msg):
    """Log of the transcription job: the last 200 lines, and the progress lines
    '[transcribe|diarize|translate] N/M' of the modules become the bar."""
    msg = str(msg)
    lines = _tr_job["log"]
    lines.append(msg)
    del lines[:-200]
    m = re.match(r"\[(transcribe|diarize|translate)\] (\d+)/(\d+)", msg)
    if m:
        _tr_job["stage"], _tr_job["done"], _tr_job["total"] = m.group(1), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"\[(diarize|translate)\]", msg)
        if m and _tr_job["stage"] != m.group(1):
            _tr_job.update(stage=m.group(1), done=0, total=0)
    logging.info(msg)


@app.route("/api/transcribe/status")
def api_transcribe_status():
    ok, why = _audio.available()
    out = {"available": ok, "reason": why, "missing": _audio.missing_packages(),
           "models": list(WHISPER_MODELS), "running": _tr_job["running"],
           "install": "requirements-audio.txt"}
    if ok:
        try:
            from audio import diarize as _dia
            out["diarize_models_cached"] = _dia.models_cached()
            out["models_dir"] = str(_dia.models_dir())
        except Exception as e:                       # noqa: BLE001 - status only
            out["diarize_models_cached"] = False
            out["models_error"] = str(e)
    return jsonify(out)


@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    """Starts the transcription of a video (or audio) file of this computer.
    Body: {path, model_size, diarize, speakers, translate: ["en", "it"]}.
    Progress: /api/transcribe/progress; stop: /api/transcribe/stop."""
    data = request.get_json(silent=True) or {}
    ok, why = _audio.available()
    if not ok:
        return jsonify({"error": "trascrizione non installata: pip install -r requirements-audio.txt",
                        "reason": why}), 503
    path = str(data.get("path") or "").strip().strip('"')
    path = os.path.abspath(os.path.expanduser(path)) if path else ""
    if not path or not os.path.isfile(path):
        return jsonify({"error": f"file non trovato: {path}"}), 400
    case_id = store.current_case()
    if not case_id:
        return jsonify({"error": "nessun caso aperto"}), 400
    model = str(data.get("model_size") or "small")
    if model not in WHISPER_MODELS:
        return jsonify({"error": f"modello sconosciuto: {model}"}), 400
    try:
        speakers = max(0, min(20, int(data.get("speakers") or 0)))
    except (TypeError, ValueError):
        speakers = 0
    opts = {"model_size": model, "diarize": _truthy(data.get("diarize", True)), "speakers": speakers,
            "translate": [x for x in (data.get("translate") or []) if x in ("en", "it")]}
    with _tr_lock:
        if _tr_job["running"]:
            return jsonify({"error": "trascrizione gia' in corso", "running": True}), 409
        _tr_stop.clear()
        _tr_job.update({"running": True, "finished": False, "error": "", "stage": "hash", "done": 0,
                        "total": 0, "log": [], "result": None, "file": os.path.basename(path)})
    threading.Thread(target=_run_transcribe, args=(path, opts, case_id), daemon=True).start()
    return jsonify({"started": True})


@app.route("/api/transcribe/progress")
def api_transcribe_progress():
    out = dict(_tr_job)
    out["log"] = list(_tr_job["log"][-60:])
    return jsonify(out)


@app.route("/api/transcribe/stop", methods=["POST"])
def api_transcribe_stop():
    _tr_stop.set()
    return jsonify({"ok": True, "running": _tr_job["running"]})


def _run_transcribe(path, opts, case_id):
    try:
        from audio.transcribe import transcribe_video
        sha = _transcripts.sha256_file(path)
        out = os.path.join(DATA_DIR, TRANSCRIPTS_DIRNAME, case_id, sha[:16])
        _tr_job["stage"] = "transcribe"
        _tr_log(f"[transcribe] {os.path.basename(path)} -> {out}")
        res = transcribe_video(path, out, model_size=opts["model_size"], diarize=opts["diarize"],
                               num_speakers=opts["speakers"], translate=tuple(opts["translate"]),
                               cancel=_tr_stop.is_set, log=_tr_log)
        if store.current_case() != case_id:
            raise NodeError(f"il caso aperto e' cambiato durante la trascrizione: il trascritto resta in {out}")
        _tr_job.update(stage="import", done=0, total=0)
        ents, names, body = _transcripts.entities(res, path, case_id, sha)
        table = ftm.rows_from_entities({e["id"]: e for e in ents}, native_types=onto.TYPES,
                                       reserved=ftm_reserved)
        plan, _ = plan_import(table, mapping=_ftm_mapping(table[0]), has_header=True)
        r = commit_plan(plan, update=True, ftm_dataset="quaesitor:transcribe")
        _cache["key"] = None
        # the transcript in the sources folder, where the search finds it
        folder = os.path.join(_sources_folder(), TRANSCRIPTS_DIRNAME, re.sub(r"[^A-Za-z0-9_-]+", "_", case_id))
        os.makedirs(folder, exist_ok=True)
        stem = re.sub(r"[^\w.-]+", "_", os.path.splitext(os.path.basename(path))[0])[:60] + "_" + sha[:8]
        files = []
        if body:
            fp = os.path.join(folder, stem + ".txt")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(f"{os.path.basename(path)}\n\n{body}\n")
            files.append(fp)
        for lg in res.get("translations") or []:
            fp = os.path.join(folder, f"{stem}.{lg}.txt")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(f"{os.path.basename(path)} ({lg})\n\n{_transcripts.text_of(res.get('segments') or [], names, lang=lg)}\n")
            files.append(fp)
        scan = False
        if files:
            sfolder = _sources_folder()
            with _scan_lock:
                if not _scan["running"] and os.path.isdir(sfolder):
                    _scan.update({"running": True, "done": 0, "total": 0, "name": "",
                                  "finished": False, "error": "", "summary": None})
                    _threading.Thread(target=_run_scan, args=(sfolder,), daemon=True).start()
                    scan = True
        node = next((i for i in r.get("ids") or [] if i.split(":", 1)[0] in ("video", "audio")), "")
        _tr_job["result"] = {"node": node, "output": out, "segments": len(res.get("segments") or []),
                             "speakers": len(names), "languages": res.get("languages") or [],
                             "translations": res.get("translations") or [], "partial": bool(res.get("partial")),
                             "nodes": r.get("nodes", 0), "links": r.get("links", 0),
                             "updated": r.get("updated", 0), "sources": files, "sources_scan": scan}
        _tr_log(f"[import] {r.get('nodes', 0)} nodes, {r.get('links', 0)} links, {r.get('updated', 0)} updated")
    except Exception as e:
        logging.error(f"Trascrizione fallita: {e}", exc_info=not isinstance(e, NodeError))
        _tr_job["error"] = str(e)
    finally:
        _tr_job["running"] = False
        _tr_job["finished"] = True


# ======================= OPENSANCTIONS (ricerca online) =======================
# Ricerca di persone e societa' su OpenSanctions (API yente: api.opensanctions.org
# con chiave, oppure un'istanza propria) e importazione delle corrispondenze
# come entita' Follow the Money, con le relazioni annidate.
# E' l'UNICA funzione, insieme all'AI, che manda dati fuori dal computer:
# spenta per impostazione predefinita (services.conf), e i nomi cercati sono
# gli unici dati inviati.
SERVICES_CONF = os.path.join(BASE_DIR, "services.conf")
SERVICES_DEFAULTS = {
    "opensanctions_enabled": "false",
    "opensanctions_endpoint": "https://api.opensanctions.org",
    "opensanctions_api_key": "",
    "opensanctions_dataset": "default",
    "opensanctions_timeout": "20",
    "epieos_enabled": "false",
    "epieos_endpoint": "https://api.epieos.com",
    "epieos_api_key": "",
    "epieos_pack": "osinter",
    "epieos_timeout": "120",
}
OSA_KEYS = ("enabled", "endpoint", "api_key", "dataset", "timeout")
EP_KEYS = ("enabled", "endpoint", "api_key", "pack", "timeout")


def _load_kv_conf(path, defaults, env_prefix):
    """File 'chiave = valore' (commenti con #) + variabili d'ambiente."""
    conf = dict(defaults)
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for riga in f:
                riga = riga.strip()
                if not riga or riga.startswith("#"):
                    continue
                k, sep, v = riga.partition("=")
                if sep:
                    conf[k.strip().lower()] = v.strip()
    except FileNotFoundError:
        pass
    except Exception as e:
        logging.error(f"{os.path.basename(path)} illeggibile: {e}")
    for k in list(conf):
        env = os.environ.get(env_prefix + k.upper())
        if env is not None:
            conf[k] = env
    return conf


def _save_kv_conf(path, updates, header):
    """Aggiorna un file 'chiave = valore' conservando commenti e ordine."""
    eol = "\n"
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            testo = f.read()
        if "\r\n" in testo:
            eol = "\r\n"
        lines = testo.splitlines()
    except FileNotFoundError:
        lines = [header]
    todo = dict(updates)
    for i, riga in enumerate(lines):
        s = riga.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k = s.partition("=")[0].strip().lower()
        if k in todo:
            lines[i] = f"{k} = {todo.pop(k)}"
    for k, v in todo.items():
        lines.append(f"{k} = {v}")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(eol.join(lines) + eol)


def _load_services_conf():
    conf = _load_kv_conf(SERVICES_CONF, SERVICES_DEFAULTS, "SERVICES_")
    conf["opensanctions_enabled"] = str(conf["opensanctions_enabled"]).strip().lower() in ("1", "true", "si", "yes", "on")
    conf["opensanctions_endpoint"] = str(conf["opensanctions_endpoint"]).strip().rstrip("/")
    try:
        conf["opensanctions_timeout"] = max(3, min(120, int(float(conf["opensanctions_timeout"]))))
    except (TypeError, ValueError):
        conf["opensanctions_timeout"] = 20
    conf["opensanctions_dataset"] = re.sub(r"[^a-z0-9_\-]", "", str(conf["opensanctions_dataset"]).lower()) or "default"
    conf["epieos_enabled"] = str(conf["epieos_enabled"]).strip().lower() in ("1", "true", "si", "yes", "on")
    conf["epieos_endpoint"] = str(conf["epieos_endpoint"]).strip().rstrip("/")
    try:
        conf["epieos_timeout"] = max(10, min(300, int(float(conf["epieos_timeout"]))))
    except (TypeError, ValueError):
        conf["epieos_timeout"] = 120
    conf["epieos_pack"] = re.sub(r"[^a-z0-9_\-]", "", str(conf["epieos_pack"]).lower()) or "osinter"
    return conf


SERVICES = _load_services_conf()


def osa_ready():
    return bool(SERVICES["opensanctions_enabled"] and SERVICES["opensanctions_endpoint"])


def _osa_public():
    k = SERVICES.get("opensanctions_api_key") or ""
    return {"enabled": bool(SERVICES["opensanctions_enabled"]), "endpoint": SERVICES["opensanctions_endpoint"],
            "has_key": bool(k), "key_hint": ("…" + k[-4:]) if len(k) > 8 else ("•" * len(k)),
            "dataset": SERVICES["opensanctions_dataset"], "timeout": SERVICES["opensanctions_timeout"],
            "ready": osa_ready()}


def _http_json(url, payload=None, headers=None, timeout=20):
    """GET (payload None) o POST JSON. Ritorna (dati, errore)."""
    data, err, _, _ = _http_json_full(url, payload, headers, timeout)
    return data, err


def _http_json_full(url, payload=None, headers=None, timeout=20, explain=None):
    """Come _http_json ma ritorna (dati, errore, header di risposta, codice HTTP).
    'explain' traduce i codici HTTP del servizio in messaggi chiari; il corpo
    dell'errore (JSON {statusCode, error, message} o testo) e' allegato."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, method="POST" if body is not None else "GET")
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace")), None, dict(r.headers), r.status
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace").strip()[:300]
            try:
                j = json.loads(detail)
                if isinstance(j, dict):
                    detail = str(j.get("message") or j.get("error") or detail)[:160]
            except ValueError:
                detail = detail[:160]
        except Exception:
            pass
        hdrs = dict(e.headers or {})
        text = (explain or {}).get(e.code) or ({401: "chiave API mancante o non valida",
                                                403: "chiave API mancante o non valida"}.get(e.code, ""))
        if text:
            detail = text + (f" - {detail}" if detail else "")
        return None, f"HTTP {e.code} {e.reason}" + (f" - {detail}" if detail else ""), hdrs, e.code
    except urllib.error.URLError as e:
        return None, f"{e.reason}", {}, 0
    except Exception as e:
        return None, f"{type(e).__name__}: {e}", {}, 0


def _osa_call(path, payload=None, query=None):
    if not osa_ready():
        return None, "OpenSanctions disattivato (pannello OpenSanctions)"
    url = SERVICES["opensanctions_endpoint"] + path
    if query:
        url += "?" + "&".join(f"{k}={quote(str(v))}" for k, v in query.items() if v not in (None, ""))
    headers = {}
    if SERVICES.get("opensanctions_api_key"):
        headers["Authorization"] = "ApiKey " + SERVICES["opensanctions_api_key"]
    return _http_json(url, payload, headers, SERVICES["opensanctions_timeout"])


def _osa_brief(e):
    """Un risultato ridotto all'essenziale per l'elenco."""
    p = e.get("properties") or {}
    return {"id": e.get("id"), "schema": e.get("schema"), "caption": e.get("caption") or (p.get("name") or [""])[0],
            "countries": (p.get("country") or p.get("nationality") or p.get("jurisdiction") or [])[:4],
            "topics": (p.get("topics") or [])[:4], "datasets": (e.get("datasets") or [])[:4],
            "birth": (p.get("birthDate") or p.get("incorporationDate") or [""])[0],
            "score": e.get("score"), "match": e.get("match")}


def _osa_flatten(e, out):
    """Entita' con proprieta' annidate (?nested=true) -> {id: entita'} piatto:
    le entita' annidate diventano voci proprie, al loro posto resta l'id."""
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


@app.route("/api/osa/config", methods=["GET", "POST"])
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
            return jsonify({"error": "endpoint non valido (serve http:// o https://)"}), 400
        if k == "timeout":
            try:
                v = str(max(3, min(120, int(float(v)))))
            except ValueError:
                return jsonify({"error": "timeout non valido"}), 400
        up["opensanctions_" + k] = v
    try:
        _save_kv_conf(SERVICES_CONF, up, "# services.conf - servizi online facoltativi (OpenSanctions). Non pubblicare: contiene la chiave API.")
    except OSError as e:
        return jsonify({"error": f"impossibile scrivere services.conf: {e}"}), 500
    SERVICES.clear()
    SERVICES.update(_load_services_conf())
    logging.info(f"Configurazione OpenSanctions aggiornata: {sorted(up)}")
    return jsonify(_osa_public())


@app.route("/api/osa/test", methods=["POST"])
def api_osa_test():
    """Prova di collegamento: /healthz dell'istanza, poi una ricerca minima."""
    data, err = _osa_call("/healthz")
    if err:
        return jsonify({"ok": False, "error": err}), 502
    data, err = _osa_call(f"/search/{SERVICES['opensanctions_dataset']}", query={"q": "test", "limit": 1})
    if err:
        return jsonify({"ok": False, "error": err}), 502
    return jsonify({"ok": True, "total": (data.get("total") or {}).get("value") if isinstance(data, dict) else None})


@app.route("/api/osa/search")
def api_osa_search():
    """Ricerca per testo: ?q=&schema=&limit= -> elenco ridotto."""
    q = str(request.args.get("q") or "").strip()[:200]
    if len(q) < 2:
        return jsonify({"error": "termine troppo corto"}), 400
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


@app.route("/api/osa/match", methods=["POST"])
def api_osa_match():
    """Confronto strutturato (nome + data di nascita / paese / numero):
    {schema, properties: {...}} -> corrispondenze con punteggio."""
    data = request.get_json(silent=True) or {}
    schema = str(data.get("schema") or "Person").strip()
    props = {k: ([v] if not isinstance(v, list) else v) for k, v in (data.get("properties") or {}).items() if v}
    if not props.get("name"):
        return jsonify({"error": "serve almeno il nome"}), 400
    body = {"queries": {"q1": {"schema": schema, "properties": props}}}
    out, err = _osa_call(f"/match/{SERVICES['opensanctions_dataset']}", payload=body, query={"limit": 10})
    if err:
        return jsonify({"error": err}), 502
    res = ((out.get("responses") or {}).get("q1") or {}).get("results") or []
    return jsonify({"ok": True, "results": [_osa_brief(e) for e in res]})


@app.route("/api/osa/import", methods=["POST"])
def api_osa_import():
    """Porta nel caso le entita' indicate ({ids: [...]}) con le loro relazioni
    annidate, come un file FtM (stesso motore: id conservati, aggiornamenti)."""
    data = request.get_json(silent=True) or {}
    ids = [str(x) for x in (data.get("ids") or []) if str(x).strip()][:50]
    if not ids:
        return jsonify({"error": "nessuna entita' indicata"}), 400
    if not store.current_case():
        return jsonify({"error": "nessun caso aperto"}), 400
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
        return jsonify({"error": "; ".join(errors) or "nessuna entita' ricevuta"}), 502
    table = ftm.rows_from_entities(ents, native_types=onto.TYPES, reserved=ftm_reserved)
    header, body = table[0], table[1:]
    totals = {"nodes": 0, "links": 0, "updated": 0, "same_links": 0}
    for i in range(0, len(body), FTM_BATCH):
        plan, _ = plan_import([header] + body[i:i + FTM_BATCH], mapping=_ftm_mapping(header), has_header=True)
        res = commit_plan(plan, update=True, ftm_dataset=",".join(sorted(datasets))[:120] or "opensanctions")
        for k in totals:
            totals[k] += res.get(k, 0)
    _cache["key"] = None
    logging.info(f"OpenSanctions: importate {len(ents)} entita' -> {totals['nodes']} nodi, {totals['links']} collegamenti")
    return jsonify(dict(totals, ok=True, entities=len(ents), errors=errors))


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


@app.route("/api/epieos/config", methods=["GET", "POST"])
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


@app.route("/api/epieos/schema", methods=["POST"])
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


@app.route("/api/epieos/search", methods=["POST"])
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


@app.route("/api/epieos/import", methods=["POST"])
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


@app.route("/api/epieos/searches")
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


# ======================= AI: DAL TESTO LIBERO AI NODI =======================
# L'utente incolla un testo libero; il chatbot ne estrae entita' e relazioni in
# JSON. La risposta del modello e' un DATO, mai un comando: se ne prendono solo
# i campi previsti, validati dalle stesse regole dell'importazione da file.

AI_MAX_TEXT = 12000
AI_MAX_NODES = 60
AI_MAX_LINKS = 120
AI_TIMEOUT_MIN = 90            # l'estrazione e' piu' lunga di una traslitterazione

AI_NODES_PROMPT = """You extract entities for an OSINT link-analysis graph from the TEXT below.
Reply with ONE JSON object only (no markdown, no comments), exactly in this shape:
{{"nodes":[{{"key":"n1","type":"person","value":"...","birth":"","address":"","brand":"","model":"","color":"","fields":{{}},"label":"","url":"","platform":"","note":""}}],
 "links":[{{"from":"n1","to":"n2","label":"...","direction":"forward"}}]}}
Rules:
- type is one of: person, phone, email, username, social, link, place, vehicle, text,
  {onto_types}.
- value is the identifier exactly as written in the text: full name, phone number, e-mail,
  username without @, profile URL, web address (with http/https), city, licence plate.
- person: value = the full name with capitalised words (e.g. "Mario Rossi");
  birth = the date of birth if the TEXT states it, as YYYY-MM-DD (e.g. "nato il 12/03/1980"
  -> "1980-03-12"), otherwise "". "birth" is used only for person nodes.
- place: ONE node per location, with the CITY and the STREET ADDRESS TOGETHER in the same node:
  value = the city/town only (e.g. "Brescia"); address = street type (if written),
  street name and house number in the usual form (e.g. "Via Papa Leone 13"; "nr."/"n."
  dropped), otherwise "". The street type (via, viale, piazza, corso, largo, strada...)
  is optional: "abita in Giacomo Leopardi 5 a Brescia" -> value "Brescia",
  address "Giacomo Leopardi 5". Never put the street type or the street in value,
  never put the city in address.
  NEVER create a separate node for the city and another for the street of the same location.
  If only a city is mentioned, address = "". "address" is used only for place nodes.
  Link the person/organization to the place (label e.g. "residenza", "sede", "domicilio").
- Place of birth ("nato a", "nata a", "born in"): ALWAYS a SEPARATE place node with the
  birth city only (address = ""), even when it is the same city as the residence, linked
  from the person with label exactly "città di nascita". Never put it only in a note.
  Example: "Mario Rossi che abita a Brescia in via papa leone nr. 13" ->
  nodes: {{"key":"n1","type":"person","value":"Mario Rossi"}},
         {{"key":"n2","type":"place","value":"Brescia","address":"Via Papa Leone 13"}};
  links: {{"from":"n1","to":"n2","label":"residenza","direction":"forward"}}.
  Example: "Giulia Verdi, nata a Roma, vive a Milano in corso Buenos Aires 45" ->
  nodes: {{"key":"n1","type":"person","value":"Giulia Verdi"}},
         {{"key":"n2","type":"place","value":"Roma","address":""}},
         {{"key":"n3","type":"place","value":"Milano","address":"Corso Buenos Aires 45"}};
  links: {{"from":"n1","to":"n2","label":"città di nascita","direction":"forward"}},
         {{"from":"n1","to":"n3","label":"residenza","direction":"forward"}}.
- vehicle: value = the licence plate ONLY (e.g. "AB123CD"), never the make or model;
  brand = the make (e.g. "Fiat"), model = the model (e.g. "Panda"), color = the colour
  (e.g. "Bianco"), each "" if not stated. "brand", "model", "color" are used only for vehicles.
  The TEXT may be a table (CSV, ";" or tab separated, with a header row such as
  marca;modello;targa;colore): then EVERY data row is one vehicle, read each value from
  its column, and do not create nodes for the header. A vehicle linked to nobody gets no link.
  Example: "marca;modello;targa;colore\nFiat;Panda;AB123CD;Bianco" ->
  nodes: {{"key":"n1","type":"vehicle","value":"AB123CD","brand":"Fiat","model":"Panda","color":"Bianco"}}.
- Investigative items (weapons, drugs, money, documents, devices, organizations, events,
  real estate): put the details in "fields" (an object with the keys listed below; only
  keys that the TEXT states, use the exact option text when one fits) and set value to the
  main detail. One node per distinct item (e.g. each seized drug with its own quantity).
{onto_rules}
- social: value = the profile URL if present, otherwise the username; always set platform
  (instagram, facebook, tiktok, x, telegram, whatsapp, linkedin, youtube, vk, snapchat, github...).
- label: optional short display name (e.g. the owner's name for a social profile), otherwise "".
- note: optional short context taken from the text (max 200 characters), otherwise "".
- text: only for a relevant free-text fact; value = short title, note = the content.
- links: relationships stated or clearly implied by the text. label = a short relationship
  written in the language of the TEXT (e.g. "fratello", "socio", "utenza", "profilo", "residenza").
  direction: "forward" (from -> to), "backward", "both" or "none".
{root}- Never invent data that is not in the TEXT. One node per distinct identifier. Max {max_nodes} nodes.
TEXT:
<<<
{text}
>>>"""

AI_ROOT_RULE = ('- The TEXT is about an EXISTING node with key "ROOT": "{label}" (type {ntype}). '
                'Do NOT add it to "nodes"; use "ROOT" in links. '
                'Connect every new node to ROOT or to another node.\n')

_AI_TYPES = {"person": "persona", "organization": "organization", "organisation": "organization",
             "company": "organization", "phone": "telefono", "email": "email",
             "username": "username", "social": "social", "link": "link", "url": "link",
             "website": "link", "place": "luogo", "address": "luogo", "location": "luogo",
             "vehicle": "veicolo", "car": "veicolo", "text": "testo", "note": "testo"}
_AI_TYPES.update({t: t for t in onto.TYPES})     # arma, stupefacente, assegno...
_AI_DIR = {"forward": "->", "backward": "<-", "both": "<->", "none": ""}


def ai_ready():
    """L'AI e' utilizzabile: interruttore acceso ed endpoint impostato."""
    return chatbot_ready()


def _ai_str(v, n=300):
    v = re.sub(r"\s+", " ", str(v if v is not None else "")).strip()
    return "".join(c for c in v if c.isprintable())[:n]


# inizio tipico di un indirizzo (via, piazza, street...) o numero civico
_STREET_RE = re.compile(
    r"^(via|viale|v\.le|piazza|p\.za|piazzale|corso|c\.so|largo|vicolo|strada|"
    r"contrada|localita|località|loc\.|frazione|borgo|lungomare|lungo\w+|"
    r"calle|avenida|rue|street|st\.|road|rd\.|avenue|ave\.)\b|\d", re.I)


def _is_street(v):
    return bool(_STREET_RE.search(str(v or "").strip()))


BIRTH_LABEL = "città di nascita"
_BIRTH_RE = re.compile(r"nascit|nato|nata\b|natal|birth|born", re.I)


def _norm_street(v):
    """'via papa leone nr. 13' -> 'Via papa leone 13'."""
    v = re.sub(r"\b(nr|n|num|numero|civico)\.?\s*(?=\d)", "", str(v or ""), flags=re.I)
    v = re.sub(r"\s+", " ", v).strip(" ,")
    return v[:1].upper() + v[1:]


def _ai_merge_places(nodes, links):
    """Citta' e indirizzo della stessa localita' devono stare in UN nodo luogo.
    Se il modello li ha separati (un luogo 'Brescia' e un luogo 'Via Papa
    Leone 13'), la via confluisce nella citta' collegata: a lei stessa, oppure
    allo stesso nodo (es. la persona che ci abita). Ritorna i link aggiornati."""
    luoghi = [k for k, n in nodes.items() if n["type"] == "luogo"]
    nascita = set()                        # citta' di nascita: sempre un nodo a se'
    for l in links:
        if _BIRTH_RE.search(_ai_str(l.get("label"), 120)):
            l["label"] = BIRTH_LABEL
            nascita.update(k for k in (_ai_str(l.get("from"), 40), _ai_str(l.get("to"), 40))
                           if k in luoghi)
    for k in luoghi:                       # un luogo con solo la via nel valore
        n = nodes[k]
        if not n["address"] and _is_street(n["value"]):
            n["address"], n["value"] = n["value"], ""
    vie = [k for k in luoghi if nodes[k]["address"] and not nodes[k]["value"]]
    citta = [k for k in luoghi if nodes[k]["value"] and not nodes[k]["address"]
             and k not in nascita]

    def vicini(k):
        out = set()
        for l in links:
            a, b = _ai_str(l.get("from"), 40), _ai_str(l.get("to"), 40)
            if a == k:
                out.add(b)
            elif b == k:
                out.add(a)
        return out

    rinomina = {}
    for v in vie:
        nv = vicini(v)
        # prima una citta' collegata direttamente, poi una che condivide un vicino,
        # infine l'unica citta' del testo
        cand = [c for c in citta if c in nv] or \
               [c for c in citta if vicini(c) & nv] or \
               (citta if len(citta) == 1 and len(vie) == 1 else [])
        if not cand:
            continue
        c = cand[0]
        citta.remove(c)
        nodes[v]["value"] = nodes[c]["value"]
        nodes[v]["note"] = nodes[v]["note"] or nodes[c]["note"]
        rinomina[c] = v
        del nodes[c]
    for k in luoghi:
        if k not in nodes:
            continue
        nodes[k]["address"] = _norm_street(nodes[k]["address"])
        if not nodes[k]["value"]:          # via senza citta': resta la via come valore
            nodes[k]["value"], nodes[k]["address"] = nodes[k]["address"], ""
    if not rinomina:
        return links
    out, visti = [], set()
    for l in links:
        a = rinomina.get(_ai_str(l.get("from"), 40), _ai_str(l.get("from"), 40))
        b = rinomina.get(_ai_str(l.get("to"), 40), _ai_str(l.get("to"), 40))
        lab = _ai_str(l.get("label"), 120).casefold()
        if a == b or (a, b, lab) in visti or (b, a, lab) in visti:
            continue                       # l'arco citta'-via o un doppione
        visti.add((a, b, lab))
        out.append(dict(l, **{"from": a, "to": b}))
    return out


def _ai_vehicle(node, raw):
    """Veicolo proposto dal modello: l'identificativo e' la TARGA; marca e
    modello (se ci sono) vanno nell'etichetta, il colore nella nota.
    'AB 123 CD' + Fiat Panda bianca -> 'AB123CD Fiat Panda', colore 'Bianco' (va
    solo nella scheda, non nelle note)."""
    targa = re.sub(r"[\s.-]+", "", node["value"]).upper()
    marca = _ai_str(raw.get("brand"), 60)
    modello = _ai_str(raw.get("model"), 60)
    colore = _ai_str(raw.get("color"), 40)
    node["value"] = targa
    node["label"] = " ".join(p for p in (targa, marca, modello) if p)
    node["colore"] = colore[:1].upper() + colore[1:] if colore else ""


def _safe_birth(v):
    """Data di nascita proposta dal modello: se non e' valida si ignora."""
    try:
        return parse_birth(_ai_str(v, 20))
    except NodeError:
        return ""


def ai_rows_from_json(d, parent=None):
    """JSON del modello -> righe per plan_rows(). Si tengono solo i campi
    previsti, ripuliti e limitati: il resto della risposta si ignora."""
    raw_nodes = d.get("nodes") if isinstance(d.get("nodes"), list) else []
    raw_links = d.get("links") if isinstance(d.get("links"), list) else []
    nodes = {}
    for n in raw_nodes[:AI_MAX_NODES]:
        if not isinstance(n, dict):
            continue
        key = _ai_str(n.get("key"), 40) or f"n{len(nodes) + 1}"
        value = _ai_str(n.get("value"), 500)
        typ = _AI_TYPES.get(_ai_str(n.get("type"), 30).lower(), "")             or onto.type_of(_ai_str(n.get("type"), 30)) or ""
        raw_f = dict(n.get("fields") or {}) if isinstance(n.get("fields"), dict) else {}
        if typ in onto.TYPES:
            # il modello a volte mette marca/modello nei campi dei veicoli
            for k_ai, k_f in (("brand", "marca"), ("model", "modello")):
                if n.get(k_ai) and not raw_f.get(k_f):
                    raw_f[k_f] = n.get(k_ai)
        fields = onto.clean_fields(typ, raw_f) if typ in onto.TYPES else {}
        if typ in onto.TYPES and not value:
            value = fields.get(onto.TYPES[typ]["value"]) or onto.label_of(typ, fields) if fields else ""
        if not value or key == "ROOT" or key in nodes:
            continue
        plat = _norm(n.get("platform"))
        url = _ai_str(n.get("url"), 500)
        if not re.match(r"^https?://", url, re.I):
            url = ""
        if typ == "social" and re.match(r"^https?://", value, re.I) and not url:
            url = value
        nodes[key] = {"type": typ, "value": value, "label": _ai_str(n.get("label"), 200),
                      "url": url, "platform": plat if plat in SOCIAL_PLATFORMS else "",
                      "note": _ai_str(n.get("note"), 400),
                      "address": _ai_str(n.get("address"), 300) if typ == "luogo" else "",
                      "birth": _safe_birth(n.get("birth")) if typ == "persona" else ""}
        if typ == "veicolo":
            _ai_vehicle(nodes[key], n)
        nodes[key]["fields"] = fields
    raw_links = _ai_merge_places(nodes, [l for l in raw_links[:AI_MAX_LINKS]
                                         if isinstance(l, dict)])

    def side(key, s, row):
        if key == "ROOT" and parent:
            row[f"id{s}"] = parent
            return True
        n = nodes.get(key)
        if not n:
            return False
        row.update({f"name{s}": n["value"], f"type{s}": n["type"], f"url{s}": n["url"],
                    f"label{s}": n["label"], f"platform{s}": n["platform"],
                    f"note{s}": n["note"], f"address{s}": n["address"],
                    f"nascita{s}": n["birth"], f"colore{s}": n.get("colore", ""),
                    f"fields{s}": json.dumps(n.get("fields") or {}, ensure_ascii=False)})
        if n["type"] == "testo":
            row[f"text{s}"] = n["note"]
        return True

    rows, used = [], set()
    for l in raw_links[:AI_MAX_LINKS]:
        if not isinstance(l, dict):
            continue
        a, b = _ai_str(l.get("from"), 40), _ai_str(l.get("to"), 40)
        if a == b:
            continue
        row = {"rel": _ai_str(l.get("label"), 120),
               "arrow": _AI_DIR.get(_ai_str(l.get("direction"), 10).lower(), "")}
        if side(a, "1", row) and side(b, "2", row):
            rows.append(row)
            used.update((a, b))
    if parent and rows and not any(r.get("id1") == parent or r.get("id2") == parent
                                   for r in rows):
        # dalla scheda di un nodo ma il modello non lo ha mai citato: il nodo
        # principale del testo (quello con piu' collegamenti) si aggancia a lui
        deg = {}
        for l in raw_links[:AI_MAX_LINKS]:
            if isinstance(l, dict):
                for k in (_ai_str(l.get("from"), 40), _ai_str(l.get("to"), 40)):
                    if k in nodes:
                        deg[k] = deg.get(k, 0) + 1
        main = max(nodes, key=lambda k: (deg.get(k, 0), -list(nodes).index(k)))
        row = {}
        side("ROOT", "1", row)
        side(main, "2", row)
        rows.insert(0, row)
    for key in nodes:                     # nodi rimasti senza collegamenti
        if key in used:
            continue
        row = {}
        if parent:                        # dalla scheda di un nodo: si collegano a lui
            side("ROOT", "1", row)
            side(key, "2", row)
        else:
            side(key, "1", row)
        rows.append(row)
    for i, r in enumerate(rows):
        r["_row"] = i + 1
    return rows


@app.route("/api/ai/nodes", methods=["POST"])
def api_ai_nodes():
    """Testo libero -> proposta di nodi e collegamenti (niente viene scritto:
    l'utente conferma poi con /api/ai/commit)."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()
    parent = str(data.get("parent") or "").strip()
    if not ai_ready():
        return jsonify({"error": "AI disattivata o non configurata", "config": True}), 400
    if len(text) < 3:
        return jsonify({"error": "testo mancante"}), 400
    text = text[:AI_MAX_TEXT]
    root = ""
    if parent:
        p = next((n for n in current_graph()["nodes"] if n["id"] == parent), None)
        if p is None:
            return jsonify({"error": "nodo di partenza non trovato"}), 404
        root = AI_ROOT_RULE.format(label=_ai_str(p.get("label"), 120).replace('"', "'"),
                                   ntype=p.get("ntype") or "")
    ok, why = chatbot_probe()                  # sonda rapida: niente attese inutili
    if not ok:
        return jsonify({"error": f"il chatbot non risponde ({CHATBOT['endpoint']}): {why}"}), 502
    prompt = AI_NODES_PROMPT.format(root=root, text=text, max_nodes=AI_MAX_NODES,
                                    onto_types=", ".join(onto.TYPES), onto_rules=onto.ai_rules())
    old = CHATBOT["timeout"]
    CHATBOT["timeout"] = max(old, AI_TIMEOUT_MIN)
    try:
        answer = chatbot_ask(prompt, force=True, json_mode=True)
    finally:
        CHATBOT["timeout"] = old
    if answer is None:
        return jsonify({"error": "il chatbot non risponde: " + (_bot["reason"] or "nessuna risposta")}), 502
    rows = ai_rows_from_json(_estrai_json(answer), parent or None)
    if not rows:
        return jsonify({"error": "l'AI non ha trovato entita' nel testo"}), 422
    plan = plan_rows(rows)
    logging.info(f"AI: proposti {len(rows)} elementi dal testo ({len(text)} caratteri)")
    return jsonify({"ok": True, "rows": _plan_json(plan), "items": rows,
                    "model": CHATBOT["model"]})


@app.route("/api/ai/commit", methods=["POST"])
def api_ai_commit():
    """Crea i nodi e i collegamenti proposti dall'AI e confermati dall'utente.
    Le righe passano di nuovo per le stesse validazioni dell'importazione."""
    data = request.get_json(silent=True) or {}
    items = [r for r in (data.get("items") or []) if isinstance(r, dict)][:AI_MAX_NODES + AI_MAX_LINKS]
    rows = [{str(k): str(v)[:2000] for k, v in r.items()} for r in items]
    skip = {int(x) for x in (data.get("skip") or []) if str(x).isdigit()}
    try:
        res = commit_plan(plan_rows(rows), skip)
    except NodeError as e:
        return jsonify({"error": str(e)}), 400
    logging.info(f"AI: creati {res['nodes']} nodi e {res['links']} collegamenti")
    return jsonify(res)


# ---------------- pannello di configurazione dell'AI (chatbot.conf) ----------------
AI_CONF_KEYS = ("enabled", "endpoint", "api_key", "model", "api", "timeout",
                "auth_header", "auth_prefix", "auto")


def _conf_public():
    k = CHATBOT.get("api_key") or ""
    return {"enabled": bool(CHATBOT["enabled"]), "endpoint": CHATBOT["endpoint"],
            "has_key": bool(k), "key_hint": ("…" + k[-4:]) if len(k) > 8 else ("•" * len(k)),
            "model": CHATBOT["model"], "api": CHATBOT["api"], "timeout": CHATBOT["timeout"],
            "auth_header": CHATBOT["auth_header"], "auth_prefix": CHATBOT["auth_prefix"],
            "auto": bool(CHATBOT["auto"]), "ready": ai_ready(),
            "down": _bot["reason"] or ""}


def save_chatbot_conf(updates):
    """Aggiorna chatbot.conf conservando commenti e ordine delle righe; le voci
    che mancano si aggiungono in fondo."""
    eol = "\n"
    try:
        # newline="": si legge il file com'e', per riscriverlo con le stesse
        # fine riga (su Windows la modalita' testo le convertirebbe in CRLF)
        with open(CHATBOT_CONF, "r", encoding="utf-8-sig", newline="") as f:
            testo = f.read()
        if "\r\n" in testo:
            eol = "\r\n"
        lines = testo.splitlines()
    except FileNotFoundError:
        lines = ["# chatbot.conf - configurazione del chatbot (AI)."]
    todo = dict(updates)
    for i, riga in enumerate(lines):
        s = riga.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k = s.partition("=")[0].strip().lower()
        if k in todo:
            lines[i] = f"{k} = {todo.pop(k)}"
    for k, v in todo.items():
        lines.append(f"{k} = {v}")
    with open(CHATBOT_CONF, "w", encoding="utf-8", newline="") as f:
        f.write(eol.join(lines) + eol)


def reload_chatbot_conf():
    CHATBOT.clear()
    CHATBOT.update(_load_chatbot_conf())
    _bot.update({"api": None, "down_until": 0.0, "reason": "", "ok_at": 0.0})


@app.route("/api/ai/config", methods=["GET", "POST"])
def api_ai_config():
    """Legge / salva la configurazione dell'AI. La chiave non viene mai
    restituita per intero: si manda solo se la si vuole cambiare."""
    if request.method == "GET":
        return jsonify(_conf_public())
    data = request.get_json(silent=True) or {}
    up = {}
    for k in AI_CONF_KEYS:
        if k not in data:
            continue
        v = data[k]
        if k in ("enabled", "auto"):
            up[k] = "true" if v in (True, "true", "1", 1, "on") else "false"
            continue
        v = re.sub(r"[\r\n]+", " ", str(v if v is not None else "")).strip()[:500]
        if k == "api_key" and not v and not data.get("clear_key"):
            continue                              # vuota = lascia quella che c'e'
        if k == "endpoint" and v and not re.match(r"^https?://[^\s]+$", v, re.I):
            return jsonify({"error": "endpoint non valido (serve http:// o https://)"}), 400
        if k == "api" and v not in ("auto", "ollama", "openai"):
            return jsonify({"error": "formato API non valido"}), 400
        if k == "timeout":
            try:
                v = str(max(1, min(600, int(float(v)))))
            except ValueError:
                return jsonify({"error": "timeout non valido"}), 400
        up[k] = v
    try:
        save_chatbot_conf(up)
    except OSError as e:
        return jsonify({"error": f"impossibile scrivere chatbot.conf: {e}"}), 500
    reload_chatbot_conf()
    logging.info(f"Configurazione AI aggiornata: {sorted(up)}")
    return jsonify(_conf_public())


@app.route("/api/ai/test", methods=["POST"])
def api_ai_test():
    """Prova di collegamento: una domanda banale al modello configurato."""
    if not CHATBOT["endpoint"]:
        return jsonify({"ok": False, "error": "endpoint non impostato"})
    t0 = time.time()
    ok, why = chatbot_probe()
    if not ok:
        return jsonify({"ok": False, "error": f"server irraggiungibile: {why}",
                        "ms": int((time.time() - t0) * 1000)})
    answer = chatbot_ask('Reply with the single word: OK', force=True, ignore_switch=True)
    ms = int((time.time() - t0) * 1000)
    if answer is None:
        return jsonify({"ok": False, "error": _bot["reason"] or "nessuna risposta", "ms": ms})
    return jsonify({"ok": True, "answer": _ai_str(answer, 80), "ms": ms,
                    "api": _bot["api"], "model": CHATBOT["model"]})


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


@app.route("/api/upload", methods=["POST"])
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


@app.route("/api/link/add", methods=["POST"])
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


@app.route("/api/link/delete", methods=["POST"])
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


@app.route("/api/link/update", methods=["POST"])
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


@app.route("/api/node/edit", methods=["POST"])
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


@app.route("/api/node/target", methods=["POST"])
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


@app.route("/api/manual")
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


@app.route("/api/node/remove_manual", methods=["POST"])
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


@app.route("/api/deleted")
def api_deleted():
    """Elenco dei nodi cancellati, dal più recente."""
    ann = load_annotations()
    items = sorted(ann["deleted"], key=lambda x: x.get("at") or "", reverse=True)
    return jsonify({"items": items, "count": len(items)})


@app.route("/api/node/restore", methods=["POST"])
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


@app.route("/api/views")
def api_views_list():
    """Elenco delle viste salvate (senza il payload pesante), dalla più recente."""
    if not store.current_case():
        return jsonify({"items": [], "count": 0})
    views = sorted(store.load_views(), key=lambda x: x.get("at") or "", reverse=True)
    out = [{"id": v["id"], "name": v.get("name") or v["id"],
            "at": v.get("at") or "", "count": v.get("count") or 0} for v in views]
    return jsonify({"items": out, "count": len(out)})


@app.route("/api/views/save", methods=["POST"])
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


@app.route("/api/views/load", methods=["POST"])
def api_views_load():
    """Restituisce il payload completo di una vista ({'id': ...})."""
    data = request.get_json(silent=True) or {}
    vid = str(data.get("id") or "").strip()
    v = store.get_view(vid)
    if not v:
        return jsonify({"error": "vista non trovata"}), 404
    return jsonify({"ok": True, "id": v["id"], "name": v.get("name") or v["id"],
                    "view": v.get("view") or {}})


@app.route("/api/views/delete", methods=["POST"])
def api_views_delete():
    """Elimina una vista salvata ({'id': ...})."""
    data = request.get_json(silent=True) or {}
    vid = str(data.get("id") or "").strip()
    if not store.delete_view(vid):
        return jsonify({"error": "vista non trovata"}), 404
    logging.info(f"Vista eliminata: {vid}")
    return jsonify({"ok": True, "id": vid})


@app.route("/api/sources/status")
def api_sources_status():
    """Stato dell'indice delle fonti: cartella, quanti file, OCR disponibile."""
    idx = sources_index()
    st = _src.index_summary(idx) if idx else {}
    if idx:
        # cartella da cui si legge DAVVERO ora (di norma 'fonti' accanto
        # all'eseguibile): così l'utente vede dove sta pescando i documenti
        cartella = _src.resolved_folder(idx, BASE_DIR, SOURCES_DEFAULT)
        st["folder"] = cartella
        # se la cartella risolta sta accanto al programma il tutto è portabile:
        # lo si dichiara qui, non in base a com'era l'indice al momento della
        # scansione (poteva essere una cartella assoluta di un altro PC)
        rel = _src._rel_to_base(cartella, BASE_DIR)
        st["portable"] = bool(rel)
        st["folder_rel"] = rel
    st["ocr_available"] = _src.OCR_AVAILABLE
    st["ocr_langs"] = _src.OCR_LANG                 # es. "ita+eng" ("" = predefinita)
    st["ocr_reason"] = _src.OCR_REASON             # "module" | "binary" | ""
    # download automatico solo su Windows e solo se manca il binario (se manca
    # il modulo Python pytesseract, scaricare Tesseract non servirebbe)
    st["ocr_can_install"] = os.name == "nt" and _src.OCR_REASON != "module"
    st["ocr_install"] = _OCR_JOB["state"]
    st["ocr_url"] = _tess.DEFAULT_URL
    st["indexed"] = bool(idx)
    st["default_folder"] = SOURCES_DEFAULT
    return jsonify(st)


@app.route("/api/sources/pick", methods=["POST"])
def api_sources_pick():
    """Apre il selezionatore cartelle nativo del sistema (l'app gira in locale)
    e ritorna il percorso scelto. Se non c'è un ambiente grafico, il client
    ripiega sull'inserimento manuale del percorso."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        start = request.get_json(silent=True) or {}
        folder = filedialog.askdirectory(
            title="Scegli la cartella delle fonti",
            initialdir=start.get("start") or os.path.expanduser("~"))
        root.destroy()
        return jsonify({"folder": folder or ""})
    except Exception as e:
        logging.warning(f"Dialog cartella non disponibile: {e}")
        return jsonify({"error": "dialog non disponibile", "detail": str(e)}), 501


import threading as _threading

# stato della scansione in corso, aggiornato dal thread di lavoro e letto dal
# client tramite /api/sources/progress (polling: robusto anche da eseguibile).
_scan = {"running": False, "done": 0, "total": 0, "name": "",
         "finished": False, "error": "", "summary": None}
_scan_lock = _threading.Lock()


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


@app.route("/api/sources/scan", methods=["POST"])
def api_sources_scan():
    """Avvia l'indicizzazione della cartella in un thread di lavoro e ritorna
    subito. L'avanzamento si legge con /api/sources/progress. Corpo: {folder}."""
    data = request.get_json(silent=True) or {}
    folder = str(data.get("folder") or "").strip().strip('"')
    if not folder:
        folder = SOURCES_DEFAULT          # 'fonti' accanto all'eseguibile
    if not os.path.isdir(folder):
        return jsonify({"error": f"cartella non trovata: {folder}"}), 404
    with _scan_lock:
        if _scan["running"]:
            return jsonify({"error": "scansione già in corso", "running": True}), 409
        _scan.update({"running": True, "done": 0, "total": 0, "name": "",
                      "finished": False, "error": "", "summary": None})
    _threading.Thread(target=_run_scan, args=(folder,), daemon=True).start()
    return jsonify({"started": True})


@app.route("/api/sources/progress")
def api_sources_progress():
    """Stato dell'indicizzazione in corso (per la barra 'file n di n')."""
    return jsonify(dict(_scan))


@app.route("/api/sources/search", methods=["POST"])
def api_sources_search():
    """Cerca un termine nelle fonti indicizzate. Corpo: {q, mode:'partial'|'total'}."""
    data = request.get_json(silent=True) or {}
    q = str(data.get("q") or "").strip()
    mode = "total" if data.get("mode") == "total" else "partial"
    if len(q) < 2:
        return jsonify({"error": "termine troppo corto"}), 400
    idx = sources_index()
    if not idx:
        return jsonify({"error": "nessuna cartella fonti indicizzata"}), 400
    return jsonify(_src.search_index(idx, q, mode))


@app.route("/api/sources/multi", methods=["POST"])
def api_sources_multi():
    """Cerca più termini insieme (le parole della chiave scheda). Corpo:
    {terms:[...], mode}. Ritorna i termini positivi (con conteggio) e i file,
    ciascuno con i termini che vi corrispondono."""
    data = request.get_json(silent=True) or {}
    terms = data.get("terms") or []
    mode = "total" if data.get("mode") == "total" else "partial"
    idx = sources_index()
    if not idx:
        return jsonify({"error": "nessuna cartella fonti indicizzata"}), 400
    return jsonify(_src.search_multi(idx, terms, mode))


@app.route("/api/sources/file/<fid>")
def api_sources_file(fid):
    """Serve un file indicizzato (per l'anteprima), validando che appartenga
    all'indice e stia dentro la cartella scansionata."""
    idx = sources_index()
    if not idx:
        abort(404)
    f = _src.find_file(idx, fid)
    if not f:
        abort(404)
    # risolve il percorso ORA, cercando PRIMA nella cartella 'fonti' accanto
    # all'eseguibile: è quella la posizione dei documenti, e l'unica che resta
    # valida portando il programma su un altro PC (l'indice conserva il
    # percorso assoluto della macchina che ha fatto la scansione).
    path, folder = _src.locate_file(idx, f.get("rel"), BASE_DIR, SOURCES_DEFAULT)
    if not path:
        logging.warning(
            f"Fonte non trovata: {f.get('rel')!r}. Cercata in: "
            + " | ".join(_src.folder_candidates(idx, BASE_DIR, SOURCES_DEFAULT)))
        abort(404)
    return send_from_directory(os.path.dirname(path), os.path.basename(path))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    frozen = getattr(sys, "frozen", False)
    if frozen:
        # eseguibile finito: apre il browser da solo e non usa il reloader
        # (che rilancerebbe un secondo processo)
        import threading
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
        logging.info(f"Quaesitor avviato su http://127.0.0.1:{port}")
        logging.info(f"Dati letti da: {DATA_DIR}")
        if not os.path.isdir(DATA_DIR):
            logging.warning("La cartella 'data' non è accanto all'eseguibile: "
                            "il grafo sarà vuoto finché non la copi qui.")
    app.run(debug=not frozen, port=port, use_reloader=not frozen)