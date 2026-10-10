# -*- coding: utf-8 -*-
# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Importazione di entita' Follow the Money (Aleph, OpenSanctions, ftm CLI).

Legge un file di entita' FtM - JSON lines (una entita' per riga), un array
JSON, oppure {"entities": [...]} - e lo trasforma nella TABELLA che
l'importazione guidata gia' capisce (nome1, tipo1, collegamento, nome2, tipo2
+ colonne): cosi' il file passa dagli stessi tre passi (colonne, anteprima,
importazione) di un CSV, senza una procedura a parte.

    schemi-arco (Ownership, Directorship, Family, Payment...)
        -> una riga per arco: i due nodi e il collegamento con l'etichetta
           dell'arco e le sue proprieta' ("owns (percentage 60)")
    proprieta' di tipo entity (Passport.holder, Sanction.entity...)
        -> una riga per collegamento, con il nome della proprieta'
    entita' restanti  -> una riga con il solo nodo 1
    schemi con un tipo nativo (ontology_ftm.py: sanction, license...)
        -> tipo nativo + colonna 'campi' (JSON) con le proprieta' scalari
    altre proprieta' scalari -> colonne libere, che diventano campi della scheda

Lo schema FtM sta in ftm_schema.json (generato da tools/ftm/make_ftm_types.py):
nessuna dipendenza dal pacchetto followthemoney a runtime."""
# "Cui prodest scelus, is fecit." (Seneca, Medea)
# He who profits from the crime committed it.
import json
import os
import re

_SCHEMA = None
_HERE = os.path.dirname(os.path.abspath(__file__))

# schema FtM -> tipo OsintGraph (valori riconosciuti dall'importazione:
# tipi base e alias di ontology.py). Gli schemi con un tipo nativo generato
# (ontology_ftm) vincono su questa tabella.
TYPE = {"Person": "person", "Address": "place", "Vehicle": "vehicle", "Email": "email",
        "UserAccount": "social", "Note": "text", "HyperText": "link", "Image": "photo"}
# tutti gli altri schemi-nodo hanno un tipo nativo generato (ontology_ftm.py)
try:
    from ontology_ftm import FTM_TYPE_OF, FTM_SCHEMA_OF
except ImportError:                       # ontologia non generata: solo i built-in
    FTM_TYPE_OF, FTM_SCHEMA_OF = {}, {}
# proprieta' FtM con una colonna nativa dell'importazione
NATIVE_COLS = {"birthDate": "nascita", "sourceUrl": "url", "website": "url",
               "notes": "nota", "summary": "nota"}
# proprieta' gia' usate come nome del nodo: niente colonna doppia
SKIP_FREE = {"name"}

# Tipi di ontology.py gia' esistenti: campo OsintGraph <- proprieta' FtM, in
# ordine di preferenza (la prima presente vince). Le proprieta' non mappate
# restano come colonne libere della scheda, nulla va perso.
FIELD_MAP = {
    "organization": [("nome", ["name"]), ("piva", ["vatCode", "taxNumber", "registrationNumber"]),
                     ("sede", ["address", "mainAddress"]), ("tipo", ["legalForm"])],
    "bankaccount": [("iban", ["iban", "accountNumber"]), ("banca", ["bankName", "bank"]),
                    ("bic", ["bic"]), ("intestatario", ["accountHolder", "holder"])],
    "document": [("numero", ["number", "passportNumber"]), ("paese", ["country"]),
                 ("rilascio", ["startDate", "issueDate"]), ("scadenza", ["endDate", "expiryDate"])],
    "property": [("indirizzo", ["address"]), ("catasto", ["registrationNumber"]),
                 ("descrizione", ["description", "summary", "name"])],
    "event": [("data", ["date", "startDate"]), ("luogo", ["location", "address"]),
              ("descrizione", ["description", "summary", "name"])],
    "findoc": [("numero", ["contractNumber", "transactionNumber", "sequenceNumber"]),
               ("data", ["date", "contractDate", "startDate"]), ("importo", ["amount", "amountEur"]),
               ("valuta", ["currency"]), ("descrizione", ["purpose", "summary", "title", "name", "description"])],
    "legaldoc": [("numero", ["fileNumber", "caseNumber", "number"]), ("data", ["fileDate", "date", "startDate"]),
                 ("autorita", ["court", "authority"]), ("descrizione", ["summary", "title", "name", "description"])],
    "crypto": [("indirizzo", ["publicKey"]), ("blockchain", ["currency"])],
    "valuable": [("descrizione", ["name", "summary", "description"]), ("valore", ["amount", "amountEur"]),
                 ("valuta", ["currency"]), ("seriale", ["isin", "ticker", "serialNumber"])],
}
# valore fisso di un campo a seconda dello schema FtM di partenza
CONST_FIELDS = {("Passport", "document", "tipo"): "Passaporto",
                ("Contract", "findoc", "tipo"): "Contratto",
                ("Payment", "findoc", "tipo"): "Bonifico / disposizione di pagamento",
                ("CourtCase", "legaldoc", "tipo"): "Sentenza"}


def schema():
    global _SCHEMA
    if _SCHEMA is None:
        with open(os.path.join(_HERE, "ftm_schema.json"), encoding="utf-8") as f:
            _SCHEMA = json.load(f)
    return _SCHEMA


def is_ftm(filename, blob):
    """E' un file di entita' FtM? Dall'estensione o dal primo byte utile."""
    name = (filename or "").lower()
    head = blob[:200].lstrip(b"\xef\xbb\xbf \t\r\n")
    if name.endswith((".jsonl", ".ftm", ".ndjson")):
        return True
    if name.endswith(".json") or head[:1] in (b"{", b"["):
        return b'"schema"' in blob[:200000]
    return False


def iter_entities(blob):
    """Entita' una alla volta: JSON lines (una per riga, letto riga per riga),
    array JSON, oppure un oggetto con 'entities' o 'results' (export di Aleph).
    Le righe che non sono entita' FtM (senza 'schema' noto) vengono saltate."""
    def ok(e):
        return isinstance(e, dict) and e.get("schema") in schema() and isinstance(e.get("properties"), dict)
    head = blob[:4096].decode("utf-8-sig", errors="replace").lstrip()
    if not head:
        raise ValueError("file vuoto")
    first = head[0]
    if first == "[" or (first == "{" and "\n" not in head.strip()):
        # array o oggetto unico: va letto tutto
        text = blob.decode("utf-8-sig", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            data = data.get("entities") or data.get("results") or [data]
        if isinstance(data, list):
            for e in data:
                if ok(e):
                    yield e
            return
        if first == "[":
            raise ValueError("JSON illeggibile")
    if first != "{":
        raise ValueError("non e' un file JSON")
    # JSON lines: riga per riga, senza tenere tutto il testo in memoria due volte
    bad = 0
    for line in blob.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line.decode("utf-8-sig", errors="replace"))
        except json.JSONDecodeError:
            bad += 1
            if bad > 50:
                raise ValueError("JSON illeggibile (troppe righe non valide)")
            continue
        if ok(e):
            yield e


def parse_entities(blob):
    return list(iter_entities(blob))


def inspect(blob):
    """Cosa c'e' nel file: conteggi per schema (nodi e archi separati),
    dataset dichiarati, qualche didascalia di esempio. Niente righe complete."""
    schemas, edges, datasets, sample, n = {}, {}, {}, [], 0
    for e in iter_entities(blob):
        n += 1
        sc = e["schema"]
        (edges if schema()[sc].get("edge") else schemas)[sc] = (edges if schema()[sc].get("edge") else schemas).get(sc, 0) + 1
        for d in (e.get("datasets") or ([e["dataset"]] if e.get("dataset") else [])):
            datasets[str(d)] = datasets.get(str(d), 0) + 1
        if len(sample) < 20 and not schema()[sc].get("edge"):
            sample.append({"schema": sc, "caption": caption(e)[:80]})
    if not n:
        raise ValueError("nessuna entita' Follow the Money nel file")
    labels = {sc: schema()[sc]["label"] for sc in list(schemas) + list(edges)}
    return {"entities": n, "nodes": sum(schemas.values()), "edges": sum(edges.values()),
            "schemas": schemas, "edge_schemas": edges, "labels": labels,
            "datasets": datasets, "sample": sample}


def _matches(e, needle):
    if not needle:
        return True
    for vals in e["properties"].values():
        if isinstance(vals, list) and any(needle in str(v).casefold() for v in vals):
            return True
    return needle in str(e.get("caption") or "").casefold()


def _entity_refs(e):
    """id delle entita' a cui questa punta (archi e proprieta' entity)."""
    props = all_props(e["schema"])
    out = []
    for k, vals in e["properties"].items():
        if props.get(k, {}).get("type") == "entity" and isinstance(vals, list):
            out.extend(str(v) for v in vals)
    return out


def filter_entities(blob, schemas=None, text="", max_entities=0, connected_only=False):
    """Seleziona le entita' da importare. schemas: schemi-nodo ammessi (vuoto =
    tutti); text: sottostringa in una proprieta' (case-insensitive);
    connected_only: oltre a quelle che corrispondono al testo, anche quelle
    collegate ad esse da un arco o da una proprieta' entity; max_entities:
    al massimo N entita'-nodo (0 = senza limite). Gli archi restano solo se
    entrambi gli estremi restano. Ritorna {id: entita'}."""
    want = set(schemas or [])
    needle = str(text or "").strip().casefold()
    nodes, edges = {}, {}
    for e in iter_entities(blob):
        eid = e.get("id")
        if not eid:
            continue
        if schema()[e["schema"]].get("edge"):
            edges[eid] = e
        elif not want or e["schema"] in want:
            nodes[eid] = e
    if needle:
        hit = {i for i, e in nodes.items() if _matches(e, needle)}
        if connected_only:
            # vicini: tramite archi e proprieta' entity, un salto
            near = set()
            for e in edges.values():
                refs = set(_entity_refs(e))
                if refs & hit:
                    near |= refs
            for i, e in nodes.items():
                refs = set(_entity_refs(e))
                if i in hit:
                    near |= refs
                elif refs & hit:
                    near.add(i)
            hit |= near
        nodes = {i: e for i, e in nodes.items() if i in hit}
    if max_entities and len(nodes) > max_entities:
        nodes = dict(list(nodes.items())[:max_entities])
    keep = dict(nodes)
    for i, e in edges.items():
        refs = _entity_refs(e)
        if refs and all(r in nodes for r in refs[:2]):
            keep[i] = e
    return keep


def ancestors(n, seen=None):
    seen = seen or []
    for p in schema()[n].get("extends", []):
        if p not in seen and p in schema():
            seen.append(p)
            ancestors(p, seen)
    return seen


def all_props(n):
    out = {}
    for a in reversed(ancestors(n)):
        out.update(schema()[a]["properties"])
    out.update(schema()[n]["properties"])
    return out


def otype(name, native):
    """Tipo OsintGraph di uno schema FtM: il tipo nativo generato se c'e' ed e'
    caricato, altrimenti il built-in corrispondente (anche ereditato), altrimenti
    un nodo di testo."""
    for s in [name] + ancestors(name):
        t = FTM_TYPE_OF.get(s)
        if t and t in native:
            return t
        if s in TYPE:
            return TYPE[s]
    return "text"


def caption(e):
    s = schema()[e["schema"]]
    for k in list(s.get("caption") or []) + ["name", "full", "iban", "number", "title"]:
        v = e["properties"].get(k)
        if v:
            return str(v[0])
    return str(e.get("id") or "")


def _scalars(e):
    props = all_props(e["schema"])
    out = {}
    for k, vals in e["properties"].items():
        if not isinstance(vals, list) or not vals:
            continue
        if props.get(k, {}).get("type") == "entity":
            continue
        out[k] = "; ".join(str(v) for v in vals if str(v).strip())
    return out


# ------------------------------------------------ relazioni tipizzate ---
# proprieta' ereditate che non hanno senso come campi di un collegamento
EDGE_GENERIC_SKIP = {"sourceUrl", "publisher", "publisherUrl", "modifiedAt", "retrievedAt",
                     "createdAt", "recordId", "proof", "indexText", "alias", "previousName",
                     "weakAlias", "keywords", "topics", "notes", "program", "wikidataId",
                     "wikipediaUrl", "summary", "description"}
# etichette italiane degli schemi-arco e delle loro proprieta' (FtM non ha l'italiano)
IT_EDGE = {
    "Associate": "Associazione", "ContractAward": "Aggiudicazione", "Control": "Controllo",
    "CourtCaseParty": "Parte processuale", "Debt": "Debito", "Directorship": "Carica direttiva",
    "Documentation": "Documentazione", "Employment": "Impiego", "Family": "Parentela",
    "Membership": "Appartenenza", "Occupancy": "Mandato", "Ownership": "Proprietà",
    "Payment": "Pagamento", "ProjectParticipant": "Partecipazione a progetto",
    "Representation": "Rappresentanza", "Succession": "Successione", "UnknownLink": "Altro legame",
    "associated with": "associato a", "awarded to": "aggiudicato a", "controls": "controlla",
    "involved in": "coinvolto in", "owes": "deve a", "directs": "dirige", "documents": "documenta",
    "works for": "lavora per", "related to": "parente di", "belongs to": "appartiene a",
    "holds": "ricopre", "owns": "possiede", "paid": "ha pagato", "participates in": "partecipa a",
    "represents": "rappresenta", "preceeds": "precede", "linked to": "legato a",
    "Relationship": "Relazione", "Role": "Ruolo", "Start date": "Data di inizio", "End date": "Data di fine",
    "Date": "Data", "Status": "Stato", "Percentage": "Percentuale", "Amount": "Importo", "Currency": "Valuta",
    "Purpose": "Causale", "Legal basis": "Base giuridica", "Ownership type": "Tipo di proprietà",
    "Shares count": "Numero di azioni", "Shares value": "Valore delle azioni",
    "Shares currency": "Valuta delle azioni", "Shares type": "Tipo di azioni", "Control type": "Tipo di controllo",
    "Secretary": "Segretario", "Lot number": "Numero del lotto", "Document number": "Numero del documento",
    "Document type": "Tipo di documento", "Decision reason": "Motivazione", "CPV code": "Codice CPV",
    "NUTS code": "Codice NUTS", "Amended": "Modificato", "Declaration date": "Data della dichiarazione",
    "Election date": "Data dell'elezione", "Period start": "Inizio del periodo", "Period end": "Fine del periodo",
    "Constituency": "Collegio", "Political group": "Gruppo politico", "Sequence number": "Numero progressivo",
    "Transaction number": "Numero della transazione", "Programme": "Programma", "Amount in EUR": "Importo in EUR",
    "Amount in USD": "Importo in USD", "Amount of tax paid": "Imposte pagate",
}


def edge_schemas():
    return [n for n, v in schema().items() if v.get("edge")]


def edge_fields(name):
    """Campi (proprieta' scalari) di uno schema-arco, in ordine: didascalia,
    proprie, poi le ereditate utili. [{key, label, labels, type}]"""
    v = schema().get(name) or {}
    if not v.get("edge"):
        return []
    props = all_props(name)
    own = set(v["properties"])
    cap = list(v["edge"].get("caption") or []) + list(v.get("caption") or [])
    keys = []
    for k in cap + list(own) + list(props):
        p = props.get(k)
        if not p or p["type"] in ("entity", "json", "html") or p.get("hidden"):
            continue
        if k in EDGE_GENERIC_SKIP or k in (v["edge"]["source"], v["edge"]["target"]):
            continue
        if k not in keys:
            keys.append(k)
    out = []
    for k in keys:
        p = props[k]
        out.append({"key": k, "label": p["label"], "type": "date" if p["type"] == "date" else "text",
                    "labels": dict(p.get("labels") or {}, it=IT_EDGE.get(p["label"], p["label"]))})
    return out


def edges_public():
    """Schemi-arco per il client: etichette, verbo dell'arco, campi."""
    out = {}
    for n in edge_schemas():
        v = schema()[n]
        out[n] = {"label": v["label"], "labels": dict(v.get("labels") or {}, it=IT_EDGE.get(n, v["label"])),
                  "verb": v["edge"].get("label") or v["label"],
                  "verb_it": IT_EDGE.get(v["edge"].get("label") or "", v["edge"].get("label") or v["label"]),
                  "directed": bool(v["edge"].get("directed", True)),
                  "caption": list(v["edge"].get("caption") or []),
                  "fields": edge_fields(n)}
    return out


def edge_auto_label(name, props):
    """Etichetta di un collegamento tipizzato senza nome: verbo FtM piu' le
    proprieta' di didascalia (es. "owns (60)"). In inglese: e' il dato, non
    l'interfaccia; il client traduce il verbo quando mostra la scheda."""
    v = schema().get(name) or {}
    if not v.get("edge"):
        return ""
    verb = v["edge"].get("label") or v["label"]
    vals = [str(props.get(k)) for k in (v["edge"].get("caption") or []) if props.get(k)]
    return verb + (f" ({', '.join(vals)[:120]})" if vals else "")


def entities_to_rows(blob, native_types=()):
    """File FtM -> tabella (prima riga = intestazione) per plan_import."""
    ents = {e["id"]: e for e in iter_entities(blob) if e.get("id")}
    if not ents:
        raise ValueError("nessuna entita' Follow the Money nel file")
    return rows_from_entities(ents, native_types)


def rows_from_entities(ents, native_types=()):
    """{id: entita'} -> tabella (prima riga = intestazione) per plan_import."""
    native = {str(t).lower() for t in native_types}

    rows, free = [], set()

    def side(e, s):
        r = {}
        sc = e["schema"]
        t = otype(sc, native)
        r[f"name{s}"] = caption(e)
        r[f"type{s}"] = t
        r[f"Schema FtM{s}"] = sc
        scal = _scalars(e)
        if t in FTM_SCHEMA_OF:
            # tipo generato da FtM: le chiavi dei campi SONO le proprieta' FtM;
            # l'id FtM entra nel campo nascosto ftmId (identita' del nodo)
            scal["ftmId"] = str(e.get("id") or "")
            r[f"campi{s}"] = json.dumps(scal, ensure_ascii=False)
            scal = {}
        elif e.get("id"):
            r[f"FtM id{s}"] = str(e["id"])                # built-in: id nella scheda
        elif t in FIELD_MAP:
            fields, used = {}, set()
            for fkey, cands in FIELD_MAP[t]:
                for k in cands:
                    if scal.get(k):
                        fields[fkey] = scal[k]
                        used.add(k)
                        break
            for (sch, typ, fkey), val in CONST_FIELDS.items():
                if sch == sc and typ == t and fkey not in fields:
                    fields[fkey] = val
            if fields:
                r[f"campi{s}"] = json.dumps(fields, ensure_ascii=False)
            scal = {k: v for k, v in scal.items() if k not in used}
        if True:
            for k, v in scal.items():
                if k in SKIP_FREE:
                    continue
                col = NATIVE_COLS.get(k)
                if col == "nascita" and s == "1":
                    r["nascita1"] = v
                elif col:
                    r[f"{col}{s}"] = v
                else:
                    r[f"{k}{s}"] = v
                    free.add(f"{k}{s}")
        return r

    linked = set()
    for e in ents.values():
        ed = schema()[e["schema"]].get("edge")
        if not ed:
            continue
        src = (e["properties"].get(ed["source"]) or [None])[0]
        dst = (e["properties"].get(ed["target"]) or [None])[0]
        if src not in ents or dst not in ents:
            continue
        # relazione tipizzata: schema-arco e sue proprieta'; l'etichetta la
        # compone il server (edge_auto_label) se resta vuota. UnknownLink e' il
        # legame generico: torna un collegamento semplice con il suo 'role'
        allowed = {f["key"] for f in edge_fields(e["schema"])}
        eprops = {k: "; ".join(str(x) for x in v if str(x).strip())
                  for k, v in e["properties"].items()
                  if k in allowed and isinstance(v, list) and v}
        if e["schema"] == "UnknownLink":
            r = {"relation": eprops.get("role") or eprops.get("summary") or "", "ftm_edge": "",
                 "ftm_props": "", "arrow": "->" if ed.get("directed", True) else "<->"}
        else:
            r = {"relation": "", "ftm_edge": e["schema"],
                 "ftm_props": json.dumps(eprops, ensure_ascii=False) if eprops else "",
                 "arrow": "->" if ed.get("directed", True) else "<->"}
        r.update(side(ents[src], "1"))
        r.update(side(ents[dst], "2"))
        rows.append(r)
        linked.update((src, dst))

    for e in ents.values():
        if schema()[e["schema"]].get("edge"):
            continue
        props = all_props(e["schema"])
        targets = [(k, t) for k, vals in e["properties"].items()
                   if props.get(k, {}).get("type") == "entity" and isinstance(vals, list)
                   for t in vals if t in ents]
        base = side(e, "1")
        if targets:
            for k, t in targets:
                r = dict(base)
                r.update({"relation": k, "arrow": "->"})
                r.update(side(ents[t], "2"))
                rows.append(r)
                linked.add(t)
        elif e["id"] not in linked:
            rows.append(base)

    fixed = ["name1", "type1", "relation", "arrow", "ftm_edge", "ftm_props", "name2", "type2", "campi1", "campi2",
             "nascita1", "nascita2", "url1", "url2", "nota1", "nota2",
             "Schema FtM1", "Schema FtM2", "FtM id1", "FtM id2"]
    used = {k for r in rows for k in r}
    cols = [c for c in fixed if c in used] + sorted(free)
    return [cols] + [[r.get(c, "") for c in cols] for r in rows]


# ------------------------------------------------------------- export ---
import hashlib

# tipi italiani di ontology.py -> schema FtM e mappa dei campi (inversa di FIELD_MAP)
EXPORT_IT = {
    "organization": ("Company", {"nome": "name", "piva": "vatCode", "sede": "address", "tipo": "legalForm"}),
    "bankaccount": ("BankAccount", {"iban": "iban", "banca": "bankName", "bic": "bic", "intestatario": "accountHolder"}),
    "document": ("Passport", {"numero": "number", "paese": "country", "rilascio": "startDate", "scadenza": "endDate"}),
    "property": ("RealEstate", {"indirizzo": "address", "catasto": "registrationNumber", "descrizione": "description",
                                "comune": "city", "tipo": "propertyType"}),
    "event": ("Event", {"data": "date", "luogo": "location", "descrizione": "description", "tipo": "name",
                        "procedimento": "recordId"}),
    "findoc": ("Contract", {"numero": "contractNumber", "data": "date", "importo": "amount", "valuta": "currency",
                            "descrizione": "description", "tipo": "name", "emittente": "summary"}),
    "legaldoc": ("CourtCase", {"numero": "fileNumber", "data": "fileDate", "autorita": "court",
                               "descrizione": "description", "tipo": "name", "procedimento": "caseNumber"}),
    "crypto": ("CryptoWallet", {"indirizzo": "publicKey", "blockchain": "currency"}),
    "valuable": ("Asset", {"descrizione": "name", "valore": "amount", "valuta": "currency", "seriale": "serialNumber"}),
    "card": ("BankAccount", {"numero": "accountNumber", "banca": "bankName", "intestatario": "accountHolder"}),
    "device": ("Asset", {"imei": "serialNumber", "marca": "name", "modello": "description"}),
}
# built-in di OsintGraph -> schema FtM
INTERNAL_RELS = {"", "target", "result", "phone", "email", "username", "name", "place", "alias", "phone-link",
                 "email-alias", "translit", "pname", "photo", "manuale", "breach", "registered", "organization"}
EXPORT_BUILTIN = {"name": "Person", "target": "Person", "place": "Address", "vehicle": "Vehicle",
                  "account": "UserAccount", "username": "UserAccount", "link": "HyperText", "text": "Note",
                  "domain": "HyperText"}
# nodi che non hanno uno schema FtM: diventano proprieta' dei vicini
PROPERTY_NODES = {"phone": "phone", "email": "email"}


def _og_id(node_id):
    return "og-" + hashlib.sha1(str(node_id).encode("utf-8")).hexdigest()[:16]


def _add(props, k, v):
    v = str(v or "").strip()
    if not v or not k:
        return
    props.setdefault(k, [])
    if v not in props[k]:
        props[k].append(v)


def _valid_props(sc, props):
    """Tiene solo le proprieta' previste dallo schema (e dai suoi antenati)."""
    allowed = all_props(sc)
    return {k: v for k, v in props.items() if k in allowed and v}


def export_entities(graph, entries, ftm_ids, only=None):
    """Nodi e collegamenti del caso -> entita' FtM (lista di dict).
    graph: current_graph(); entries: {id nodo: voce 'added'} (campi dei nodi
    manuali); ftm_ids: {id nodo: (id FtM, schema, dataset)}; only: insieme di
    id nodo da esportare (None = tutti). Ritorna (entita', riepilogo)."""
    ents, summary = {}, {"nodes": 0, "links": 0, "skipped": {}, "as_property": 0}
    nodes = {n["id"]: n for n in graph.get("nodes", []) if n.get("ntype") != "latin"}
    if only is not None:
        nodes = {i: n for i, n in nodes.items() if i in only}

    def fid(nid):
        return (ftm_ids.get(nid) or (None,))[0] or _og_id(nid)

    def node_entity(nid, n):
        nt = n.get("ntype") or "generic"
        entry = entries.get(nid) or {}
        fields = dict(entry.get("fields") or {})
        extra = dict(entry.get("extra") or {})
        props = {}
        if nt in FTM_SCHEMA_OF:
            sc = FTM_SCHEMA_OF[nt]
            for k, v in fields.items():
                if k != "ftmId":
                    _add(props, k, v)
        elif nt in EXPORT_IT:
            sc, fmap = EXPORT_IT[nt]
            for k, v in fields.items():
                if v is True:
                    continue
                _add(props, fmap.get(k), v)
            if not props:
                # nodo nato da un import (es. organizzazione trovata da Epieos),
                # senza campi manuali: l'etichetta e' il nome
                _add(props, "name", n.get("label"))
            if nt == "document" and str(fields.get("tipo") or "").lower().find("passaport") < 0:
                sc = "Identification"
        elif nt in EXPORT_BUILTIN:
            sc = EXPORT_BUILTIN[nt]
            if sc == "Person":
                _add(props, "name", n.get("label_orig") or entry.get("value") or n.get("label"))
                if entry.get("cognome"):
                    _add(props, "lastName", entry["cognome"])
                if entry.get("nome"):
                    _add(props, "firstName", entry["nome"])
                _add(props, "birthDate", entry.get("nascita"))
                for a in n.get("aliases") or []:
                    _add(props, "alias", a)
            elif sc == "Address":
                _add(props, "full", n.get("label"))
                if entry.get("citta") and entry["citta"] != n.get("label"):
                    _add(props, "city", entry["citta"])
                _add(props, "street", entry.get("indirizzo"))
                _add(props, "latitude", entry.get("lat") or n.get("lat"))
                _add(props, "longitude", entry.get("lon") or n.get("lon"))
            elif sc == "Vehicle":
                _add(props, "registrationNumber", entry.get("value") or n.get("label"))
                _add(props, "name", n.get("label"))
            elif sc == "UserAccount":
                # profilo: userid univoco, nick, nome, URL, data di creazione
                # dalle schede (chiavi profile_* dell'adattatore Epieos o le
                # chiavi comuni degli export OSINT), altrimenti l'etichetta
                raws = [r.get("raw") or {} for r in (n.get("records") or []) if isinstance(r, dict)]
                def _raw(*keys):
                    for r in raws:
                        for k in keys:
                            v = r.get(k)
                            if isinstance(v, (str, int)) and str(v).strip():
                                return str(v).strip()
                    return ""
                uname = _raw("profile_username", "username", "login", "handle", "screen_name") or \
                    (entry.get("value") if nt == "username" else "")
                pname = _raw("profile_name", "name", "full_name", "display_name")
                lab = str(n.get("label") or "")
                if not uname and not pname and nt == "username":
                    uname = lab
                elif not uname and not pname and not _raw("sito") and "." not in lab and " " not in lab:
                    uname = lab                                  # etichetta = nick (export OSINT)
                _add(props, "username", uname)
                _add(props, "name", pname or (lab if lab != uname else ""))
                _add(props, "service", n.get("platform"))
                _add(props, "sourceUrl", n.get("url") or entry.get("url") or _raw("profile_url", "profile", "url"))
                _add(props, "createdAt", _raw("profile_created", "created_at", "creation_date"))
                pid = _raw("profile_id")
                if pid:
                    _add(props, "notes", f"userid: {pid}")
            elif sc == "HyperText":
                _add(props, "title", n.get("label"))
                _add(props, "sourceUrl", n.get("url") or entry.get("value"))
            else:                                               # Note
                _add(props, "name", n.get("label"))
                _add(props, "description", entry.get("text"))
        elif nt == "breach":
            # violazione di dati: nessuno schema FtM, una nota con la fonte
            sc = "Note"
            _add(props, "name", f"[breach] {n.get('label')}")
            srcs = ", ".join(s for s in (n.get("sources") or []) if s)
            _add(props, "description", f"data breach: {n.get('label')}" + (f" (fonte: {srcs})" if srcs else ""))
        elif nt in PROPERTY_NODES:
            return None
        else:
            # tipi senza equivalente (armi, stupefacenti, avvistamenti...): una
            # nota con il tipo nel titolo e i campi nel testo. Perdita dichiarata.
            sc = "Note"
            _add(props, "name", f"[{nt}] {n.get('label') or nid}")
            body = "; ".join(f"{k}: {v}" for k, v in fields.items() if v not in (None, "", False))
            _add(props, "description", body)
            summary["skipped"][nt] = summary["skipped"].get(nt, 0) + 1
        if n.get("note"):
            _add(props, "notes", n["note"])
        if n.get("roman") and n.get("roman") != n.get("label"):
            _add(props, "alias", n["roman"])
        for k, v in extra.items():
            if k in ("FtM id", "Schema FtM"):
                continue
            if k in all_props(sc):
                _add(props, k, v)
            else:
                _add(props, "notes", f"{k}: {v}")
        return {"id": fid(nid), "schema": sc, "properties": _valid_props(sc, props), "_node": nid}

    for nid, n in nodes.items():
        e = node_entity(nid, n)
        if e:
            ents[nid] = e
            summary["nodes"] += 1
    # telefoni ed email: proprieta' dei vicini che possono averle
    adj = {}
    for e in graph.get("edges", []):
        adj.setdefault(e["source"], []).append(e["target"])
        adj.setdefault(e["target"], []).append(e["source"])
    for nid, n in nodes.items():
        prop = PROPERTY_NODES.get(n.get("ntype"))
        if not prop:
            continue
        placed = False
        for other in adj.get(nid, []):
            if other in ents and prop in all_props(ents[other]["schema"]):
                _add(ents[other]["properties"], prop, n.get("label"))
                placed = True
        if placed:
            summary["as_property"] += 1
        else:
            summary["skipped"][n["ntype"]] = summary["skipped"].get(n["ntype"], 0) + 1

    links = []
    for e in graph.get("edges", []):
        a, b = e.get("source"), e.get("target")
        if a not in ents or b not in ents or e.get("rel") in ("translit", "pname"):
            continue
        sc = e.get("ftm") if e.get("ftm") in schema() else "UnknownLink"
        ed = schema()[sc]["edge"]
        props = {ed["source"]: [ents[a]["id"]], ed["target"]: [ents[b]["id"]]}
        for k, v in (e.get("ftm_props") or {}).items():
            _add(props, k, v)
        if sc == "UnknownLink":
            # 'rel' e' di solito un tipo interno (phone, target...), non un nome;
            # un ruolo trovato da una fonte (es. 'CEO' da LinkedIn) invece lo e'
            _add(props, "role", e.get("label") or (e.get("rel") if e.get("rel") not in INTERNAL_RELS else ""))
        elif e.get("label") and e["label"] != edge_auto_label(sc, e.get("ftm_props") or {}):
            _add(props, "summary", e["label"])
        links.append({"id": _og_id(e.get("id")), "schema": sc, "properties": _valid_props(sc, props)})
        summary["links"] += 1
    # id generati per i nodi senza id FtM: li ritorna a parte, cosi' il server
    # li registra e un re-import dell'export ricade sugli stessi nodi
    new_ids = [(e["id"], nid, e["schema"]) for nid, e in ents.items() if nid not in ftm_ids]
    out = []
    for e in list(ents.values()) + links:
        e = dict(e)
        e.pop("_node", None)
        out.append(e)
    summary["new_ids"] = new_ids
    return out, summary
