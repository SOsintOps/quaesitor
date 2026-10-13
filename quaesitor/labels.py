# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Labels edited by hand and the relabelling of the graph."""
# "Mutatis mutandis." (legal phrase)
# The necessary changes having been made.
import logging
import re
import unicodedata

import regex as _rx

from . import store
from .core import _flat, _hash
from .transliteration import translit_mode
from .normalize import _LATIN_DIACRITICS, place_is_address
from .records import norm_ident
from .identifiers import TYPE_RANK


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
