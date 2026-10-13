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
