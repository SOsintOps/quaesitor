# -*- coding: utf-8 -*-
"""Converts Follow the Money entities (JSON lines: id, schema, properties) into the
two-nodes-per-row CSV that the OsintGraph guided import already reads
(nome1, tipo1, collegamento, nome2, tipo2 + free columns -> record fields).

Usage: python ftm_to_csv.py <schema dir> <entities.jsonl> <out.csv>

No change to OsintGraph: the FtM properties that have no native column
end up in the free columns (extra), the FtM types are translated into
OsintGraph types; the edge schemata (edge: source/target) become
links with the edge label and their properties (e.g. percentage)
in the link name."""
# "Pares cum paribus facillime congregantur." (Cicero, De Senectute)
# Like gathers most easily with like.
import sys, os, csv, json, yaml

SCHEMA_DIR, INP, OUT = sys.argv[1:4]
raw = {}
for fn in os.listdir(SCHEMA_DIR):
    if fn.endswith(".yaml"):
        raw.update(yaml.safe_load(open(os.path.join(SCHEMA_DIR, fn), encoding="utf-8")))

def ancestors(n, seen=None):
    seen = seen or []
    for p in raw[n].get("extends", []) or []:
        if p not in seen: seen.append(p); ancestors(p, seen)
    return seen

# FtM schema -> OsintGraph type (aliases recognised by the import: ontology.ALIASES and base types)
TYPE = {"Person": "person", "Company": "organization", "Organization": "organization",
        "PublicBody": "organization", "LegalEntity": "organization", "Address": "place",
        "Vehicle": "vehicle", "Airplane": "vehicle", "Vessel": "vehicle", "Email": "email",
        "UserAccount": "social", "BankAccount": "bankaccount", "CryptoWallet": "crypto",
        "Passport": "document", "Identification": "document", "RealEstate": "property",
        "Event": "event", "Contract": "findoc", "CourtCase": "legaldoc", "Note": "text",
        "HyperText": "link", "Image": "photo", "Security": "valuable", "Asset": "valuable"}
# for the schemata without an equivalent (Sanction, License, Position...) 'text' is used
# with the fields in the free columns: it stays readable in the record

def otype(schema):
    for s in [schema] + ancestors(schema):
        if s in TYPE: return TYPE[s]
    return "text"

ents = {}
for line in open(INP, encoding="utf-8"):
    if line.strip():
        e = json.loads(line); ents[e["id"]] = e

def caption(e):
    s = raw[e["schema"]]
    for k in (s.get("caption") or ["name"]) + ["name", "full", "iban", "number"]:
        v = e["properties"].get(k)
        if v: return v[0]
    return e["id"]

def props_of(e):
    """scalar properties (not entity) -> free columns"""
    out = {}
    allp = {}
    for a in reversed(ancestors(e["schema"])): allp.update(raw[a].get("properties", {}) or {})
    allp.update(raw[e["schema"]].get("properties", {}) or {})
    for k, vals in e["properties"].items():
        if (allp.get(k) or {}).get("type") == "entity": continue
        out[k] = "; ".join(vals)
    return out

rows, extra_cols = [], set()
edges = [e for e in ents.values() if raw[e["schema"]].get("edge")]
linked = set()
for e in edges:
    ed = raw[e["schema"]]["edge"]
    src = e["properties"].get(ed["source"], [None])[0]
    dst = e["properties"].get(ed["target"], [None])[0]
    if not (src in ents and dst in ents): continue
    a, b = ents[src], ents[dst]
    label = ed.get("label") or raw[e["schema"]]["label"]
    detail = ", ".join(f"{k} {v[0]}" for k, v in e["properties"].items()
                       if k not in (ed["source"], ed["target"]) and v)
    r = {"name1": caption(a), "type1": otype(a["schema"]), "relation": label + (f" ({detail})" if detail else ""),
         "arrow": "->" if ed.get("directed", True) else "<->",
         "name2": caption(b), "type2": otype(b["schema"])}
    for k, v in props_of(a).items(): r[f"{k}1"] = v; extra_cols.add(f"{k}1")
    for k, v in props_of(b).items(): r[f"{k}2"] = v; extra_cols.add(f"{k}2")
    r["ftm_schema1"] = a["schema"]; r["ftm_schema2"] = b["schema"]; r["ftm_edge"] = e["schema"]
    rows.append(r); linked.update((src, dst))
# node entities not touched by edges: a row with node 1 only; the properties
# of type entity (e.g. Passport.holder, Sanction.entity) become links
for e in ents.values():
    if raw[e["schema"]].get("edge"): continue
    r = {"name1": caption(e), "type1": otype(e["schema"]), "ftm_schema1": e["schema"]}
    for k, v in props_of(e).items(): r[f"{k}1"] = v; extra_cols.add(f"{k}1")
    allp = {}
    for a in reversed(ancestors(e["schema"])): allp.update(raw[a].get("properties", {}) or {})
    allp.update(raw[e["schema"]].get("properties", {}) or {})
    targets = [(k, t) for k, vals in e["properties"].items() if (allp.get(k) or {}).get("type") == "entity"
               for t in vals if t in ents]
    if targets:
        for k, t in targets:
            rr = dict(r); rr.update({"relation": k, "arrow": "->", "name2": caption(ents[t]),
                                     "type2": otype(ents[t]["schema"]), "ftm_schema2": ents[t]["schema"]})
            rows.append(rr)
    elif e["id"] not in linked:
        rows.append(r)

cols = ["name1", "type1", "relation", "arrow", "name2", "type2", "ftm_schema1", "ftm_schema2", "ftm_edge"] + sorted(extra_cols)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(f"{len(ents)} entita' FtM -> {len(rows)} righe CSV, {len(cols)} colonne ({len(extra_cols)} libere)")
