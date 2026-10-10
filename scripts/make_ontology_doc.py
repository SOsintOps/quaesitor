# -*- coding: utf-8 -*-
"""Generates docs/ontology.md: every node type of the graph with its fields,
identity rule and Follow the Money equivalent, plus the typed relations.
English output, from the English labels carried by the ontology itself
(ontology.py, ontology_ftm.py, ftm.py). Run from the program folder:

    python scripts/make_ontology_doc.py
"""
# "Nemo sine vitio est." (Seneca the Elder, Controversiae)
# No one is without fault.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ontology as o
import ontology_i18n as i18n
import ftm

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "ontology.md")
EN = i18n.table()["en"]          # Italian display text -> English, for select values

# Group names: the Italian ontology groups and their English names (the FtM
# groups are not translated by ontology_i18n, the others only partly).
GROUPS = {
    "Armi": "Weapons", "Stupefacenti": "Drugs", "Valori": "Valuables", "Finanza": "Finance",
    "Documenti": "Documents", "Dispositivi": "Devices", "Soggetti": "Subjects", "Fatti": "Events",
    "Beni": "Assets", "Volo": "Flight",
    "FtM · Soggetti": "FtM · Subjects", "FtM · Finanza": "FtM · Finance",
    "FtM · Documenti d'identità": "FtM · Identity documents", "FtM · Beni e mezzi": "FtM · Assets and vehicles",
    "FtM · Procedimenti": "FtM · Proceedings", "FtM · Documenti": "FtM · Documents",
}

# ---- 1. core types (upstream): not in ontology.TYPES, the rules live in app.py
CORE = [
    ("target", "Target (subject of the case)", "person", "`target:<id>`: the dossier; label = name", "name, date of birth, photo, sources; every card of the dossier", "Person"),
    ("name", "Person name", "person", "`name:<normalised surname and name>[|birth]` (word order ignored, diacritics removed; same name + same birth date = same node)", "name, surname, birth date, aliases, Latin form (`roman`) when not Latin", "Person"),
    ("phone", "Phone", "identifier", "`phone:<digits only>`", "number, carrier and country from the cards, services using it (checker cards)", "`phone` property of the neighbours (Person, Company, UserAccount)"),
    ("email", "E-mail", "identifier", "`email:<lower-case address>`", "address, checker cards (hibp, holehe, adobe, protonmail, samsung…)", "`email` property of the neighbours"),
    ("username", "Nickname / handle", "identifier", "`user:<lower-case nick>`", "nick, platform", "UserAccount (`username`)"),
    ("account", "Social account / profile", "identifier", "`acct:<service>id:<id>` or `acct:<service>:<nick>` (several identifiers of the same service = one node; `snapchat:nick` + `snapchatid:123` merge)", "platform, nick, display name, photo, profile link, every field of the service (`raw`), dates", "UserAccount (`username`, `service`, `sourceUrl`)"),
    ("place", "Place", "place", "`place:<city street>` when it is an address (street or coordinates, shared); `place:<card>|<city>` when it is a generic city (stays tied to the card)", "city, street, number, latitude, longitude (Alt+click opens the map)", "Address (`full`, `city`, `street`, `latitude`, `longitude`)"),
    ("vehicle", "Vehicle", "asset", "`vehicle:<plate without spaces>`", "plate, description", "Vehicle (`registrationNumber`)"),
    ("photo", "Photo", "document", "hash of the URL or of the file", "URL, node of origin", "Image"),
    ("link", "Link / URL", "document", "hash of the URL", "URL, title", "HyperText (`sourceUrl`)"),
    ("domain", "Domain", "identifier", "`domain:<name>`", "name, whois from the cards", "HyperText"),
    ("text", "Note / text", "document", "own id", "title, body", "Note (`name`, `description`)"),
    ("breach", "Data breach", "fact", "`breach:<name of the leak>`", "name of the leak, source (hibp, naz.api)", "no FtM schema: exported as Note"),
    ("latin", "Latin form (twin node)", "person", "`latin:<...>` only with the \"Separate Latin nodes\" switch; otherwise it is the `roman` attribute of the node", "transliteration", "alias of the Person"),
]


def esc(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ")


def en_value(v):
    return EN.get(v, v)


def field_row(f):
    t = f.get("type", "text")
    extra = ""
    if t == "select" and f.get("options"):
        extra = " · values: " + ", ".join(en_value(v) for v in f["options"])
    if f.get("hidden"):
        extra += " · hidden"
    return f"`{f['key']}` {esc(f.get('en') or f.get('label'))} ({t}{esc(extra)})"


def type_section(key, t):
    ident = t.get("ident") or []
    alt = t.get("ident_alt") or []
    ftm_sc = t.get("ftm") or (ftm.EXPORT_IT.get(key, ("—",))[0] if key in ftm.EXPORT_IT else "Note (declared loss)")
    lines = [f"### `{key}` — {esc(t.get('en') or t['label'])}", ""]
    lines.append(f"- **Group:** {esc(GROUPS.get(t.get('group'), t.get('group')))} · **Italian label:** {esc(t['label'])} · **icon:** {t.get('icon')} · **colour:** {t.get('color')}")
    lines.append(f"- **Identity** (same value = same node): {', '.join('`'+k+'`' for k in ident) if ident else 'none: every entry is a new node'}"
                 + (f" · alternative key: {', '.join('`'+k+'`' for k in alt)}" if alt else ""))
    lines.append(f"- **Label:** {', '.join('`'+x+'`' for x in (t.get('label_fmt') or [t.get('value') or '']))}")
    lines.append(f"- **Follow the Money:** {ftm_sc}")
    lines.append(f"- **Fields** ({len(t['fields'])}):")
    for f in t["fields"]:
        lines.append(f"  - {field_row(f)}")
    lines.append("")
    return "\n".join(lines)


def main():
    n_it = [k for k, t in o.TYPES.items() if not t.get("ftm")]
    n_ftm = [k for k, t in o.TYPES.items() if t.get("ftm")]
    n_fields = sum(len(t["fields"]) for t in o.TYPES.values())
    out = []
    out.append("# Graph Entities\n")
    out.append("Every node type of the graph with its identity rule, label, fields and Follow the Money equivalent, plus the typed relations on links. Generated by `scripts/make_ontology_doc.py` from the ontology in use (`ontology.py`, `ontology_ftm.py`, `ftm.py`): do not edit by hand, regenerate.\n")
    out.append("The ontology has three layers: the **core types** inherited from OSInt Graph (identity merging, platforms, map, transliteration and the OSINT-export engine, Epieos included, all run on them), the **investigative types** (entered by hand or by the AI; their field keys and stored values are Italian, because the stored value is the identity of the data), and the **Follow the Money types** generated from the `followthemoney` schemata. Each type has an identity (the key that merges two entries into one node), a label, fields and an FtM equivalent on export.\n")
    out.append("---\n")
    out.append(f"| Layer | Types | Fields |\n| :--- | :--- | :--- |\n| core (upstream) | {len(CORE)} | free card (`raw`) |\n| investigative | {len(n_it)} | {sum(len(o.TYPES[k]['fields']) for k in n_it)} |\n| Follow the Money, native | {len(n_ftm)} | {sum(len(o.TYPES[k]['fields']) for k in n_ftm)} |\n| FtM relations on links | {len(ftm.edges_public())} | — |\n")
    out.append("---\n")

    out.append("## 1. Core Types (Upstream)\n")
    out.append("They have no fixed form of fields: the card keeps every field of the source (`raw`), plus images and links. This is where OSINT exports and Epieos responses land.\n")
    out.append("| Type | What it is | Nature | Identity (node id) | In the card | Follow the Money |\n| :--- | :--- | :--- | :--- | :--- | :--- |")
    for key, lab, nat, ident, props, f in CORE:
        out.append(f"| `{key}` | {esc(lab)} | {nat} | {esc(ident)} | {esc(props)} | {esc(f)} |")
    out.append("\nCore links (`rel`): `target`, `result`, `phone`, `email`, `username`, `name`, `place`, `alias`, `phone-link`, `email-alias`, `translit`, `photo`, `breach`, `registered`, plus the role (e.g. `CEO`) for the organisations found by Epieos; manual links have a free label, direction and style.\n")
    out.append("---\n")

    out.append("## 2. Investigative Types\n")
    out.append("Entered by hand (New node) or proposed by the AI. Field keys and select values are stored in Italian (the value is the identity of the data and is what the AI and the search compare); the interface shows them translated. On FtM export they map onto the schema shown (`ftm.EXPORT_IT`); types without an equivalent become `Note`.\n")
    for k in n_it:
        out.append(type_section(k, o.TYPES[k]))
    out.append("---\n")

    out.append("## 3. Follow the Money Types\n")
    out.append("Generated by `scripts/ftm/make_ftm_types.py`; identity = `ftmId` (hidden field: an imported entity always lands on the same node), with an alternative key for manual entry. Four carry the `ftm` prefix because the name was already taken by an investigative type. The eight FtM schemata Person, Address, Email, UserAccount, Image, Note, HyperText and Vehicle are **not** separate types: they are the core types of section 1.\n")
    groups = {}
    for k in n_ftm:
        groups.setdefault(o.TYPES[k].get("group"), []).append(k)
    for g, keys in groups.items():
        out.append(f"\n#### {esc(GROUPS.get(g, g))}\n")
        for k in keys:
            out.append(type_section(k, o.TYPES[k]))
    out.append("---\n")

    out.append("## 4. Follow the Money Relations (Edge Schemata)\n")
    out.append("Chosen in the link window (\"Follow the Money relation\"); the fields sit on the link and the automatic label is `verb (caption)`.\n")
    out.append("| Schema | Verb | Directed | Fields |\n| :--- | :--- | :--- | :--- |")
    for name, e in ftm.edges_public().items():
        fields = ", ".join(f"`{f['key']}` {esc(f.get('label'))} ({f.get('type','text')})" for f in e.get("fields", []))
        out.append(f"| {name} | {esc(e.get('verb'))} | {'yes' if e.get('directed') else 'no'} | {fields} |")
    out.append("")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print(OUT, len(CORE), len(n_it), len(n_ftm), n_fields)


if __name__ == "__main__":
    main()
