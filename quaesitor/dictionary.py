# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""The hand-made transliteration dictionary and the node helpers it shares with
the importers."""
# "Usus magister est optimus." (proverb)
# Practice is the best teacher.
from urllib.parse import quote
import os
import re
import uuid

from . import ontology as onto
from .core import _json_obj, _truthy, DATA_DIR, NodeError, PHOTO_EXT
from .chatbot import chatbot_ready
from .transliteration import ai_fill_translit, parole_da_traslitterare, script_of
from .normalize import (
    _fold, _TYPE_HEAD, canon_streets, norm_city, norm_civico, norm_street, parse_birth,
    person_id, person_key, person_label, place_is_address, place_parts, split_civico,
    STREET_TYPES,
)
from .records import photo_label


def onto_fields(ntype, data):
    """Fields of an ontology item from the request: a 'fields' object (form,
    AI) or just 'value', which goes into the main field of the type."""
    fields = onto.clean_fields(ntype, _json_obj(data.get("fields")))
    main = onto.TYPES[ntype]["value"]
    value = re.sub(r"\s+", " ", str(data.get("value") or "")).strip()
    if value and not fields.get(main):
        fields.update(onto.clean_fields(ntype, {main: value}))
    return fields


def _resolve_onto(ntype, data, value):
    """Weapon, drug, cheque, document... With the identifying fields filled in
    (serial number, number, IBAN...) the object is unique: entering it again
    adds a card to the same node. Without them, every entry is a separate
    exhibit (new node)."""
    fields = onto_fields(ntype, data)
    if not fields:
        raise NodeError("compila almeno un campo")
    ident = onto.ident_of(ntype, fields)
    nid = f"{ntype}:{ident}" if ident else f"{ntype}:#{uuid.uuid4().hex[:10]}"
    label = str(data.get("label") or "").strip() or onto.label_of(ntype, fields)
    value = fields.get(onto.TYPES[ntype]["value"]) or label
    return nid, label, ntype, ntype, str(value)


def resolve_node(data, parent=""):
    """From type + value (+ optional fields) derive the node identity with
    the SAME rules as the graph, so a value already present does not create
    a duplicate. Returns (nid, label, platform, ntype, value); NodeError if
    the value is not valid. 'parent' is used only by generic places, which
    stay tied to the node they were added from."""
    ntype = str(data.get("ntype") or "").strip().lower()
    value = str(data.get("value") or "").strip()
    platform = str(data.get("platform") or "").strip().lower()
    if ntype in ("name", "target", "person"):
        # person: surname and first name (or the full name in 'value') + birth
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
        # place: city (required) + optional street, house number and coordinates
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
        # as in the graph: a generic city stays tied to the card it started
        # from; only a location (address or coordinates) can be shared
        # between different cards
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
        # free note: the label is the title, the body goes in the card
        titolo = str(data.get("label") or value).strip()
        if not titolo:
            raise NodeError("titolo mancante")
        nid = "text:" + re.sub(r"[^a-z0-9]+", "-", titolo.lower()).strip("-")[:60]
        label, platform, value = titolo, "text", value or titolo
    elif ntype == "photo":
        # 'value' is the relative path returned by /api/upload
        rel = value.replace("\\", "/").lstrip("/")
        if not rel.lower().startswith("media/") or not rel.lower().endswith(PHOTO_EXT):
            raise NodeError("immagine non valida")
        if not os.path.isfile(os.path.join(DATA_DIR, *rel.split("/"))):
            raise NodeError("immagine non trovata sul server")
        nid = "photo:" + rel.lower()
        label = str(data.get("label") or "").strip() or photo_label(os.path.basename(rel))
        platform = "photo"
    elif ntype == "link":
        # generic link: any URL with a label of choice
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
    """Id of a place already in the graph with the same city, street and house
    number (normalised comparison), otherwise None."""
    street, civ = _via_civico(data)
    key = (norm_city(city), norm_street(street), norm_civico(civ))
    if not all(key):
        return None
    luoghi = [(n["id"], place_parts(n)) for n in g["nodes"] if n.get("ntype") == "place"]
    luoghi = [(i, p) for i, p in luoghi if p and p[0] and p[1]]
    # same rules as merge_places: initials expanded if the full street is unique
    canon = canon_streets({(c, s) for _, (c, s, _v) in luoghi} | {key[:2]})
    ck = (key[0], canon[key[:2]], key[2])
    return next((i for i, (c, s, v) in luoghi if (c, canon[(c, s)], v) == ck), None)


def maps_url(city, street="", civico=""):
    """Google Maps search: 'Via Santo Stefano 55, Brescia'."""
    via = f"{street} {civico}".strip()
    q = ", ".join(p for p in (via, str(city or "").strip()) if p)
    return "https://www.google.com/maps/search/?api=1&query=" + quote(q)


def _via_civico(data):
    """(street, house number) of a request: the number from its own field or,
    if missing, split off the end of the address ('Via Roma 12' -> 'Via Roma', '12')."""
    addr = re.sub(r"\s+", " ", str(data.get("address") or "")).strip(" ,")
    civ = re.sub(r"\s+", "", str(data.get("civico") or ""))
    civ = re.sub(r"^(?:n|nr|no|num|numero|civico)\.?", "", civ, flags=re.I)
    street, c2 = split_civico(addr)
    if civ and c2 and norm_civico(civ) != norm_civico(c2):
        street = addr                       # the number in the address is not the house number
    # street type chosen from the drop-down: prepended if the name has none already
    tipo = re.sub(r"\s+", " ", str(data.get("toponimo") or "")).strip()
    if tipo and street and not _TYPE_HEAD.match(_fold(street)) \
            and _fold(tipo) in STREET_TYPES:
        street = f"{tipo} {street}"
    return street, civ or c2


def new_added_entry(nid, label, platform, ntype, value, data, parent, now):
    """annotations.json entry for a manually created node."""
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
        entry["extra"] = extra                     # free columns of the imported file
    if ntype in onto.TYPES:
        entry["fields"] = onto_fields(ntype, data)
    if ntype == "vehicle":
        colore = re.sub(r"\s+", " ", str(data.get("colore") or "")).strip()[:40]
        if colore:
            entry["colore"] = colore[:1].upper() + colore[1:]    # in the card only
    if ntype == "name":
        for k in ("cognome", "nome"):
            v = re.sub(r"\s+", " ", str(data.get(k) or "")).strip()[:120]
            if v:
                entry[k] = v
        nascita = parse_birth(data.get("nascita"))
        if nascita:
            entry["nascita"] = nascita
        if _truthy(data.get("target")):
            entry["target"] = True           # highlighted as target
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
            # with coordinates the node opens directly on the map
            entry["url"] = ("https://www.google.com/maps/search/?api=1&query="
                            f"{entry['lat']},{entry['lon']}")
        elif not entry.get("url"):
            entry["url"] = maps_url(value, street, civico)
    return entry


def _translit_new_labels(labels):
    """Transliteration: if a label is in a non-Latin alphabet the node will get
    its Latin node (created by apply_annotations). With the AI enabled the new
    words are translated RIGHT AWAY, before replying to the client: so the
    Latin node is born with the AI's form and not the local engine's (if the
    AI does not answer, it falls back to the local engine). Returns the first
    non-Latin alphabet found."""
    labels = [str(l or "") for l in labels]
    scr = next((s for s in map(script_of, labels) if s), "") or ""
    if scr and chatbot_ready():
        nuove = parole_da_traslitterare({"nodes": [{"label": l} for l in labels]})
        if nuove:
            ai_fill_translit(nuove)
    return scr
