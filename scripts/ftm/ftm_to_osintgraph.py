# -*- coding: utf-8 -*-
"""Reads the Follow the Money YAML schemata (followthemoney package) and
projects them onto the OsintGraph ontology (ontology.py: TYPES).

Usage: python ftm_to_osintgraph.py <ftm schema dir> [--emit out.py]

Without --emit it prints the analysis: concrete schemata, which match types already
present in OsintGraph, which become new types, which are relations
(Interval) and therefore links, how many properties cannot be represented.
With --emit it writes a Python module with an FTM_TYPES dict in the same format
as ontology.TYPES, to be merged with TYPES.update(FTM_TYPES)."""
# "Similis simili gaudet." (medieval proverb)
# Like takes pleasure in like.
import sys, os, re, json, yaml

SCHEMA_DIR = sys.argv[1]
EMIT = sys.argv[sys.argv.index("--emit") + 1] if "--emit" in sys.argv else None
OWN = "--own" in sys.argv   # only the schema's own fields + featured

raw = {}
for fn in sorted(os.listdir(SCHEMA_DIR)):
    if fn.endswith(".yaml"):
        with open(os.path.join(SCHEMA_DIR, fn), encoding="utf-8") as f:
            raw.update(yaml.safe_load(f))

def ancestors(name, seen=None):
    seen = seen or []
    for p in raw[name].get("extends", []) or []:
        if p not in seen:
            seen.append(p); ancestors(p, seen)
    return seen

def all_props(name):
    """own + inherited properties (the own ones win)."""
    out = {}
    for a in reversed(ancestors(name)):
        out.update(raw[a].get("properties", {}) or {})
    out.update(raw[name].get("properties", {}) or {})
    return out

def is_a(name, anc):
    return name == anc or anc in ancestors(name)

concrete = [n for n, s in raw.items() if not s.get("abstract")]
things = [n for n in concrete if not raw[n].get("edge")]
intervals = [n for n in concrete if raw[n].get("edge")]   # edges: they have source/target
docs = [n for n in things if is_a(n, "Document")]

# ---- matches with the types OsintGraph already has (built-in or ontology.py)
EXISTING = {
    "Person": "name/target (built-in)", "Address": "place (built-in)",
    "Vehicle": "vehicle (built-in)", "Email": "email (built-in)",
    "UserAccount": "account/username (built-in)", "Image": "photo (built-in)",
    "Note": "text (built-in)", "HyperText": "link (built-in)",
    "Company": "organization", "Organization": "organization", "PublicBody": "organization",
    "LegalEntity": "organization", "BankAccount": "bankaccount", "CryptoWallet": "crypto",
    "Passport": "document", "Identification": "document", "RealEstate": "property",
    "Event": "event", "Contract": "findoc", "Payment": "findoc", "CourtCase": "legaldoc",
    "Security": "valuable", "Asset": "valuable", "Vessel": "vehicle (built-in)",
    "Airplane": "vehicle (built-in)",
}
# FtM types that for OsintGraph are document containers (sources), not nodes
SOURCES_LAYER = {"Document", "Folder", "Package", "Pages", "Page", "PlainText", "Table",
                 "Workbook", "Audio", "Video", "Article", "Message", "Documentation",
                 "Mention", "Analyzable", "Similar"}

TYPE_MAP = {"string": "text", "text": "text", "name": "text", "date": "date",
            "number": "number", "identifier": "text", "country": "text", "phone": "text",
            "email": "text", "url": "text", "address": "text", "ip": "text",
            "iban": "text", "checksum": "text", "mimetype": "text", "language": "text",
            "gender": "select", "topic": "select", "json": None, "html": None,
            "entity": None}

def cat(n):
    if n in intervals: return "relation -> collegamento"
    if n in SOURCES_LAYER: return "fonte documentale (sources.py), non nodo"
    if n in EXISTING: return f"esiste: {EXISTING[n]}"
    return "NUOVO tipo per ontology.py"

rows, new_types, entity_props, unrepresentable = [], {}, 0, 0
for n in sorted(concrete):
    props = all_props(n)
    ent = [k for k, p in props.items() if (p or {}).get("type") == "entity"]
    entity_props += len(ent)
    bad = [k for k, p in props.items() if TYPE_MAP.get((p or {}).get("type", "string"), "x") is None
           and (p or {}).get("type") != "entity"]
    unrepresentable += len(bad)
    rows.append((n, raw[n].get("label", n), len(props), len(ent), cat(n)))
    if cat(n).startswith("NUOVO"):
        new_types[n] = (props, ent)

print(f"schemi totali {len(raw)}, concreti {len(concrete)}; nodi {len(things)}, "
      f"di cui documenti {len(docs)}; Interval (relazioni) {len(intervals)}")
print(f"proprieta' di tipo entity (= archi) {entity_props}; non rappresentabili (json/html) {unrepresentable}")
print()
print(f"{'schema':22}{'label':30}{'prop':>5}{'ent':>4}  categoria")
for n, lab, np_, ne, c in rows:
    print(f"{n:22}{lab:30}{np_:5}{ne:4}  {c}")

ICONS = {"Sanction": "gavel", "Position": "building-columns", "License": "file-contract",
         "Debt": "file-invoice-dollar", "Trip": "location-dot", "Project": "file-lines",
         "Call": "phone", "Risk": "burst", "Territory": "globe", "TaxRoll": "receipt",
         "CallForTenders": "file-contract", "ContractAward": "file-contract",
         "EconomicActivity": "building", "Interest": "link", "Value": "money-bill-wave",
         "CourtCaseParty": "scale-balanced"}

if EMIT:
    out = {}
    for n, (props, ent) in new_types.items():
        s = raw[n]
        fields = []
        own = set((s.get("properties") or {}).keys()) | set(s.get("featured") or [])
        for k, p in props.items():
            if OWN and k not in own:
                continue
            p = p or {}
            t = p.get("type", "string")
            if t == "entity" or TYPE_MAP.get(t, "x") is None or p.get("hidden") or p.get("deprecated"):
                continue
            kind = TYPE_MAP[t]
            opts = []
            if kind == "select":
                kind = "text"          # the gender/topic options are in followthemoney/types
            fields.append({"key": k, "label": p.get("label", k), "en": p.get("label", k),
                           "type": kind, "options": opts, "ph": p.get("description", "")[:60]})
        # FtM's "featured" fields first (the ones FtM considers salient)
        feat = s.get("featured") or []
        fields.sort(key=lambda f: (f["key"] not in feat, feat.index(f["key"]) if f["key"] in feat else 0))
        caption = [c for c in (s.get("caption") or []) if c in props] or [fields[0]["key"]]
        out[n.lower()] = {
            "label": s.get("label", n), "en": s.get("label", n), "group": "FtM",
            "icon": ICONS.get(n, "circle-question"), "color": "#0f766e",
            "fields": fields,
            "ident": [k for k in ("registrationNumber", "number", "idNumber", "sourceUrl")
                      if k in props][:1] or caption[:1],
            "label_fmt": caption[:3], "value": caption[0],
            "ai": f"{n.lower()}: {s.get('description', '').strip()[:160]} fields: "
                  + ", ".join(f["key"] for f in fields[:8]) + ".",
            "ftm_schema": n, "ftm_entity_props": ent,
        }
    with open(EMIT, "w", encoding="utf-8") as f:
        f.write("# generato da ftm_to_osintgraph.py - tipi Follow the Money assenti in OsintGraph\n")
        f.write("FTM_TYPES = " + json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"\nscritto {EMIT}: {len(out)} tipi nuovi, {sum(len(v['fields']) for v in out.values())} campi")
