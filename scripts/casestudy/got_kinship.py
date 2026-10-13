"""Game of Thrones kinship case study: builds the import files and the findings.

Reads the character table scraped from A Wiki of Ice and Fire and published by
Tomaz Bratanic (tomasonjo/blog-datasets, ice_fire/characters.tsv), keeps the
father, mother and spouse links, cleans the source, and writes:

- esempi/got_kinship.csv: the largest family network, one row per link, ready
  for the Quaesitor import (Family relations of Follow the Money); a child with
  two fathers or two mothers in the source gets both links dashed;
- esempi/got_kinship_hypotheses.csv: the analyst's hypothesis on the parents of
  Jon Snow, dashed, and the open question as a text node;
- the findings of the case study on standard output (Markdown), the numbers
  quoted in docs/case-study-game-of-thrones.md.

Standard library only. Usage:
    python scripts/casestudy/got_kinship.py [characters.tsv] [--out esempi/got_kinship.csv]
Without a file the table is downloaded from GitHub.
"""
import argparse
import ast
import collections
import csv
import io
import os
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import unquote

DATA_URL = "https://raw.githubusercontent.com/tomasonjo/blog-datasets/main/ice_fire/characters.tsv"
SOURCE = "A Wiki of Ice and Fire, via tomasonjo/blog-datasets"
TARGETS = {"Jon Snow"}
# links the source does not record; drawn dashed, never mixed with the source file
HYPOTHESES = [("Jon Snow", "father", "Rhaegar Targaryen"),
              ("Jon Snow", "mother", "Lyanna Stark"),
              ("Lyanna Stark", "spouse", "Rhaegar Targaryen")]
QUESTION = "Open question: who are the parents of Jon Snow?"
# pages the source links as a parent or spouse that are not people: groups,
# places, gods, trades. Their links are dropped (checked by hand on the wiki titles)
NOT_PEOPLE = {"acorn_water", "andal", "archmaester", "craster%27s_wives", "dothraki",
              "goddess_of_the_wind", "gulltown", "hellholt", "knight", "lion_of_night", "lys",
              "magister", "maiden-made-of-light", "ny_sar", "old_blood", "oldtown",
              "prostitution", "reach", "rock_wife", "salt_wife", "salt_wives", "sea_god",
              "septa", "septon", "smallfolk", "summer_islander", "thenns", "weeping_water",
              "whore"}
# the same woman under her maiden and her married name, with no redirect to tell
SAME_PERSON = {"catelyn_tully": "catelyn_stark", "lysa_tully": "lysa_arryn"}
WIKI = "awoiaf.westeros.org/index.php/"
PREFIX = re.compile(r"^(Lady|Lord|King|Queen|Prince|Princess|Ser|Septa|Septon|Maester)(?=[A-Z])")
CITE = re.compile(r"\[[^\]]*\]")

csv.field_size_limit(10 ** 8)


def as_list(v):
    v = (v or "").strip()
    if not v:
        return []
    try:
        x = ast.literal_eval(v)
    except (ValueError, SyntaxError):
        return []
    return x if isinstance(x, list) else []


def flat(v):
    """"[b'In131AC[1],King's Landing[1]']" -> "131 AC, King's Landing"."""
    out = []
    for x in as_list(v):
        for y in (x if isinstance(x, list) else [x]):
            s = y.decode("utf-8", "replace") if isinstance(y, bytes) else str(y)
            s = CITE.sub("", s)
            s = re.sub(r"^In(?=[a-z])", "In ", s)
            s = re.sub(r"^In(?=\d)", "", s)
            s = re.sub(r"(\d)(AC|BC)\b", r"\1 \2", s)
            s = re.sub(r"\s*,\s*", ", ", s).strip(" ,")
            if s:
                out.append(s)
    return "; ".join(out)


def key(url):
    """One key per wiki page: lower case, http and https alike."""
    return re.sub(r"^https?://", "", url.strip()).lower()


def url_name(url):
    return unquote(url.rstrip("/").split("/")[-1]).replace("_", " ").strip()


def titled(s):
    """A lower-case page name in title case: "aegon_iii_targaryen" -> "Aegon III Targaryen"."""
    words = []
    for w in s.split():
        up = w.upper()
        words.append(up if re.fullmatch(r"[IVX]+", up) else w[:1].upper() + w[1:])
    return " ".join(words)


def clean(name):
    return PREFIX.sub("", CITE.sub("", name)).strip()


def load(path):
    if path:
        text = Path(path).read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(DATA_URL, timeout=60) as r:
            text = r.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def build(rows):
    quality = collections.Counter()
    people, edges, own = {}, set(), set()
    schemes = collections.defaultdict(set)
    for r in rows:
        k = key(r["url"])
        own.add(k)
        schemes[k].add(r["url"].strip().split(":")[0].lower())
        name = clean(r["name"]) or titled(url_name(r["url"]).lower())
        if name != r["name"]:
            quality["names cleaned (title glued to the name, citation mark, stray space)"] += 1
        people[k] ={"name": name, "url": r["url"].strip(), "born": flat(r["born"]),
                     "died": flat(r["died"]), "titles": flat(r["title"]),
                     "houses": [url_name(a) for a in as_list(r["allegiance"]) if "House_" in a]}
        for rel in ("father", "mother", "spouse"):
            for u in as_list(r[rel]):
                if isinstance(u, str) and u.strip():
                    edges.add((k, rel, key(u)))
                    schemes[key(u)].add(u.strip().split(":")[0].lower())
    quality["pages reached both as http and as https, one key"] = sum(len(v) > 1 for v in schemes.values())
    # pages linked but without a row of their own: the name comes from the address
    for a, _, b in sorted(edges):
        for x in (a, b):
            if x not in people:
                people[x] = {"name": titled(url_name(x)), "url": "https://" + x,
                             "born": "", "died": "", "titles": "", "houses": []}
                quality["people known only from a link (no page of their own)"] += 1
    # one person, two pages. A linked page without a row whose title is the name
    # of exactly one row is a wiki redirect to that row (Olenna Tyrell, the row
    # of Olenna Redwyne); the notebook's Catelyn merge and Lysa are done by hand
    rows_by_name = collections.defaultdict(list)
    for k in own:
        rows_by_name[people[k]["name"].lower()].append(k)
    alias = {}
    for k in people:
        if k in own or k[len(WIKI):] in NOT_PEOPLE:
            continue
        hits = rows_by_name.get(people[k]["name"].lower(), [])
        if len(hits) == 1:
            alias[k] = hits[0]
            quality["linked pages that redirect to a row under another name, merged"] += 1
    for a, b in SAME_PERSON.items():
        if WIKI + a in people and WIKI + b in people:
            alias[WIKI + a] = WIKI + b
            quality["maiden and married name merged by hand (Catelyn, Lysa)"] += 1
    links = {}
    for a, rel, b in sorted(edges):
        a, b = alias.get(a, a), alias.get(b, b)
        if rel == "spouse":
            a, b = sorted((a, b))
        if a == b:
            quality["links of a page to itself dropped"] += 1
            continue
        if "/house_" in a or "/house_" in b:
            quality["links to a house page in place of a person, dropped"] += 1
            continue
        if any(x[len(WIKI):] in NOT_PEOPLE for x in (a, b)):
            quality["links to a group, place, god or trade in place of a person, dropped"] += 1
            continue
        if people[a]["name"].lower() == people[b]["name"].lower():
            # the notebook drops these; most are a son named after his father
            quality["links between two pages with the same name, kept"] += 1
        k = (rel,) + (tuple(sorted((a, b))) if rel == "spouse" else (a, b))
        if k in links:
            quality["marriages recorded on both sides, counted once"] += 1
        links[k] = (a, rel, b)
    for k in alias:
        people.pop(k, None)
    used = {x for a, _, b in links.values() for x in (a, b)}
    for k in [k for k in people if k not in own and k not in used]:
        people.pop(k)
    # homonyms: two pages, one name. The node takes the wiki page title instead
    by_name = collections.defaultdict(list)
    for k, p in people.items():
        by_name[p["name"]].append(k)
    for name, ks in by_name.items():
        if len(ks) > 1:
            quality["homonyms renamed after their wiki page"] += len(ks)
            for k in ks:
                u = url_name(people[k]["url"])
                people[k]["name"] = titled(u) if u.islower() else u
    return people, list(links.values()), quality


def adjacency(links):
    adj = collections.defaultdict(set)
    for a, _, b in links:
        adj[a].add(b)
        adj[b].add(a)
    return adj


def components(adj):
    seen, out = set(), []
    for n in adj:
        if n in seen:
            continue
        comp, stack = [], [n]
        seen.add(n)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def shortest(adj, a, b):
    prev, q = {a: None}, collections.deque([a])
    while q:
        x = q.popleft()
        if x == b:
            break
        for y in sorted(adj[x]):
            if y not in prev:
                prev[y] = x
                q.append(y)
    if b not in prev:
        return None
    path = [b]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])
    return path[::-1]


def betweenness(adj, nodes):
    """Brandes, unweighted, undirected."""
    bc = dict.fromkeys(nodes, 0.0)
    for s in nodes:
        stack, pred = [], {v: [] for v in nodes}
        sigma, dist = dict.fromkeys(nodes, 0), dict.fromkeys(nodes, -1)
        sigma[s], dist[s] = 1, 0
        q = collections.deque([s])
        while q:
            v = q.popleft()
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = dict.fromkeys(nodes, 0.0)
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]
    return {k: v / 2 for k, v in bc.items()}


def cut_size(adj, nodes, x):
    """People cut off from the largest remaining block when x is removed."""
    rest = {k: adj[k] - {x} for k in nodes if k != x}
    sizes = [len(c) for c in components(rest)]
    return sum(sizes[1:]) if sizes else 0


def write_csv(path, people, links, keep):
    cols = ["name1", "type1", "target1", "note1", "url1", "relation", "arrow", "line", "color",
            "width", "ftm", "ftm_props", "name2", "type2", "target2", "note2", "url2", "Source"]
    colour = {"father": "#2563eb", "mother": "#db2777", "spouse": "#dc2626"}
    noted = set()
    # two fathers (or two mothers) for one child: neither link is confirmed
    count = collections.Counter((a, rel) for a, rel, _ in links if rel != "spouse")
    contested = {k for k, c in count.items() if c > 1}

    def side(k):
        p = people[k]
        note = ""
        if k not in noted:
            noted.add(k)
            parts = [f"Born: {p['born']}" if p["born"] else "", f"Died: {p['died']}" if p["died"] else "",
                     f"Titles: {p['titles']}" if p["titles"] else "",
                     f"Allegiance: {', '.join(p['houses'])}" if p["houses"] else ""]
            note = " | ".join(x for x in parts if x)
        return [p["name"], "person", "yes" if p["name"] in TARGETS else "", note, p["url"]]

    rows = sorted((l for l in links if l[0] in keep),
                  key=lambda l: (people[l[0]]["name"], l[1], people[l[2]]["name"]))
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for a, rel, b in rows:
            doubt = (a, rel) in contested
            w.writerow(side(a) + [f"{rel} (conflicting records)" if doubt else rel,
                                  "->" if rel != "spouse" else "-", "dashed" if doubt else "",
                                  colour[rel], "2" if rel == "spouse" else "", "Family",
                                  '{"relationship": "%s"}' % rel] + side(b) + [SOURCE])
    return len(rows)


def write_hypotheses(path, people, hyp):
    """Second import file: the hypothesised links, dashed, plus a text node for
    the open question linked to every candidate parent."""
    jon = next(k for k, p in people.items() if p["name"] == "Jon Snow")
    cols = ["name1", "type1", "relation", "arrow", "line", "color", "ftm", "ftm_props",
            "name2", "type2", "Source"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for a, rel, b in hyp:
            w.writerow([people[a]["name"], "person", f"hypothesis: {rel}",
                        "-" if rel == "spouse" else "->", "dashed", "#7c3aed", "Family",
                        '{"relationship": "%s"}' % rel, people[b]["name"], "person",
                        "Analyst hypothesis, not in the source"])
        w.writerow([QUESTION, "text", "concerns", "->", "dotted", "", "", "",
                    people[jon]["name"], "person", "Collection plan"])
        for rel, b in sorted((rel, b) for a, rel, b in [l for l in LINKS if l[0] == jon]) +                 [(rel, b) for a, rel, b in hyp if a == jon]:
            w.writerow([QUESTION, "text", f"candidate {rel}", "->", "dotted", "", "", "",
                        people[b]["name"], "person", "Collection plan"])


LINKS = []


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tsv", nargs="?")
    ap.add_argument("--out", default="esempi/got_kinship.csv")
    args = ap.parse_args()

    rows = load(args.tsv)
    people, links, quality = build(rows)
    LINKS[:] = links
    adj = adjacency(links)
    comps = components(adj)
    big = set(comps[0])
    n = lambda k: people[k]["name"]
    find = lambda name: next(k for k, p in people.items() if p["name"] == name)
    rel_of = {}
    for a, rel, b in links:
        rel_of[(a, b)] = f"{rel} of" if rel != "spouse" else "spouse of"
        rel_of[(b, a)] = {"father": "child of", "mother": "child of", "spouse": "spouse of"}[rel]
    # rel_of[(x, y)]: what y is to x, read along the path
    rel_of = {(x, y): ("father" if r == "father of" else "mother" if r == "mother of"
                       else "spouse" if r == "spouse of" else "child") for (x, y), r in rel_of.items()}

    written = write_csv(args.out, people, links, big)
    pr = print
    pr(f"# Findings\n\nSource rows: {len(rows)} characters. Family network: {len(adj)} people, "
       f"{len(links)} links ({', '.join(f'{c} {r}' for r, c in collections.Counter(l[1] for l in links).most_common())}).")
    pr(f"\nComponents: {len(comps)}; the five largest: {', '.join(str(len(c)) for c in comps[:5])}. "
       f"Written to {args.out}: the largest, {len(big)} people and {written} links.")
    pr("\n## Data quality\n")
    for k, v in quality.items():
        pr(f"- {k}: {v}")
    pr("\n## Houses in the largest network (surname count)\n")
    sur = collections.Counter(n(k).split()[-1] for k in big if len(n(k).split()) > 1 and len(n(k).split()[-1]) > 3)
    pr(", ".join(f"{s} {c}" for s, c in sur.most_common(10)))
    pr("\n## Degree (links of each person, step 5 of the method)\n")
    for k in sorted(big, key=lambda k: (-len(adj[k]), n(k)))[:10]:
        pr(f"- {n(k)}: {len(adj[k])}")
    nodes = sorted(big)
    bc = betweenness(adj, nodes)
    pr("\n## Betweenness (people on the most shortest paths)\n")
    for k in sorted(nodes, key=lambda k: -bc[k])[:10]:
        pr(f"- {n(k)}: {bc[k]:.0f}")
    pr("\n## Cut points (people whose removal splits the network)\n")
    top = sorted(nodes, key=lambda k: -bc[k])[:40]
    cuts = sorted(((cut_size(adj, nodes, k), k) for k in top), reverse=True)[:8]
    for size, k in cuts:
        pr(f"- {n(k)}: {size} people cut off")
    pr("\n## Shortest kinship paths\n")
    for a, b in [("Tyrion Lannister", "Viserys I"), ("Jon Snow", "Daenerys Targaryen"),
                 ("Sansa Stark", "Cersei Lannister"), ("Margaery Tyrell", "Sansa Stark")]:
        p = shortest(adj, find(a), find(b))
        steps = " ".join(f"→ ({rel_of[(p[i], p[i + 1])]}) {n(p[i + 1])}" for i in range(len(p) - 1))
        pr(f"- {a} to {b}, {len(p) - 1} hops: {n(p[0])} {steps}")
    pr("\n## Ancestry of Margaery Tyrell\n")
    parents = collections.defaultdict(list)
    for a, rel, b in links:
        if rel in ("father", "mother"):
            parents[a].append((rel, b))
    todo, gen = [(find("Margaery Tyrell"), 0)], {}
    while todo:
        k, g = todo.pop()
        for rel, p in sorted(parents[k], key=lambda x: n(x[1])):
            if p not in gen:
                gen[p] = (g + 1, rel, k)
                todo.append((p, g + 1))
    for p, (g, rel, child) in sorted(gen.items(), key=lambda x: (x[1][0], n(x[0]))):
        pr(f"- generation {g}: {n(p)}, {rel} of {n(child)}")
    # the notebook's last query: (Targaryen)<-[:FATHER|MOTHER]-(s1)-[:SPOUSE]-(s2)-[:FATHER|MOTHER]->(Stark)
    pr("\n## Marriages between a child of a Targaryen and a child of a Stark\n")
    of_house = lambda k, h: h in n(k) or f"House {h}" in people[k]["houses"]
    for a, rel, b in sorted(links, key=lambda l: (n(l[0]), n(l[2]))):
        if rel != "spouse":
            continue
        for s1, s2 in ((a, b), (b, a)):
            t = sorted(n(p) for _, p in parents[s1] if of_house(p, "Targaryen"))
            s = sorted(n(p) for _, p in parents[s2] if of_house(p, "Stark"))
            if t and s:
                pr(f"- {n(s1)} (child of {', '.join(t)}) married {n(s2)} (child of {', '.join(s)})")
    pr("\n## Conflicting parentage (two fathers or two mothers for one child)\n")
    claims = collections.defaultdict(list)
    for a, rel, b in links:
        if rel != "spouse":
            claims[(a, rel)].append(n(b))
    for (a, rel), v in sorted(claims.items(), key=lambda x: n(x[0][0])):
        if len(v) > 1:
            pr(f"- {n(a)}: {rel} {' or '.join(sorted(v))}{'' if a in big else ' (outside the largest network)'}")
    pr("\n## The record of Jon Snow\n")
    j = find("Jon Snow")
    for rel, p in sorted(parents[j]):
        pr(f"- {rel}: {n(p)}")
    for name in ("Lyanna Stark", "Rhaegar Targaryen"):
        for k in [k for k in people if n(k).startswith(name)]:
            pr(f"- {n(k)}: {len(adj[k])} links, in the largest network: {k in big}")
    hyp = [(find(a), rel, find(b)) for a, rel, b in HYPOTHESES]
    hpath = os.path.splitext(args.out)[0] + "_hypotheses.csv"
    write_hypotheses(hpath, people, hyp)
    for a, rel, b in hyp:
        adj[a].add(b)
        adj[b].add(a)
        rel_of[(a, b)], rel_of[(b, a)] = rel, ("child" if rel != "spouse" else rel)
    p = shortest(adj, find("Jon Snow"), find("Daenerys Targaryen"))
    steps = " ".join(f"→ ({rel_of[(p[i], p[i + 1])]}) {n(p[i + 1])}" for i in range(len(p) - 1))
    pr(f"\nWith the {len(hyp)} hypothesised links of {hpath}, Jon Snow to Daenerys Targaryen, "
       f"{len(p) - 1} hops: {n(p[0])} {steps}")


if __name__ == "__main__":
    sys.exit(main())
