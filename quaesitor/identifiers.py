# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Services and identifiers: phone numbers, social profiles and vehicles of the
dossiers, and the graph built from the records."""
# "Nosce te ipsum." (Latin rendering of the Delphic maxim)
# Know thyself.
from urllib.parse import quote
import logging
import re

from . import ontology as onto
from . import epieos, store
from .core import _flat, _hash
from .transliteration import add_translit, slug, WORD_RE
from .normalize import collect_places, NAME_STOP, person_id, place_is_address
from .records import collect, export_query, norm_ident, norm_platform, parse_records


# ==================== SERVICES AND IDENTIFIERS ====================
# messaging services: the account is the phone number
MESSAGING = {
    "whatsapp", "viber", "imo", "botim", "telegram", "signal", "wechat",
    "line", "skype", "zangi", "tango", "kakaotalk", "threema", "icq", "snapchat",
}

# cards that describe the NUMBER (not an account): they end up in the phone node
PHONE_CARD_SCHEMAS = {"callerid"}
PHONE_CARD_CATEGORIES = {"technical", "checker"}

# identifier prefix -> service
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

# abbreviations used in dossiers: 'FB 1234 (nick)', 'IG nick', 'TikTok @nick'
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
    """Unique identifier of a number: digits only."""
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
    """An opaque identifier (UUID, numeric id) is not a good label."""
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
    if re.fullmatch(r"\d{5,}", rest):                 # numeric id + nick in brackets
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
    # when True, the nodes created/touched are "seed data": they come from the
    # target's initial file (dossier). The frontend gives them a red border.
    _seed = [False]

    def add_node(nid, **attrs):
        seed = bool(_seed[0] or attrs.get("seed"))
        if nid in nodes:
            n = nodes[nid]
            if seed:
                n["seed"] = True            # once seed, always seed (OR)
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
        """Merge key of an account: platform + normalised value, separated by
        '|'. The value must be meaningful (>= 3 useful characters): otherwise
        the merge is SKIPPED. Stops different accounts with an empty or
        non-Latin nick from all collapsing onto the same key (the bug by which
        4 different TikTok users ended up merged on 'id:tiktok')."""
        svc = re.sub(r"[^a-z0-9]", "", str(svc or "").lower()) or "generic"
        v = re.sub(r"[^a-z0-9@._]", "", str(raw or "").strip().lower()).strip("._@")
        if len(v) < 3:
            return
        ident_map.setdefault(f"acct:{svc}|{v}", set()).add(nid)

    # ---------- builders of elementary nodes ----------
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
        """'Name' node derived from how a phone line is saved in address books.
        Discards what is not a name: numbers, abbreviations, service labels."""
        lab = re.sub(r"\s+", " ", str(value or "")).strip(" .,-–—")
        if not lab or len(lab) < 3 or len(lab) > 80:
            return None
        if not WORD_RE.search(lab):                  # no letters: it is a number
            return None
        if re.sub(r"\D", "", lab) and len(re.sub(r"\D", "", lab)) >= 6:
            return None                              # contains a phone number
        if lab.lower() in NAME_STOP:
            return None
        nid = person_id(lab)
        add_node(nid, label=lab, ntype="name", platform="name",
                 sources=[source] if source else [])
        return nid

    def node_place(info, source="", scope=""):
        """Place node derived from a card: label and/or coordinates.
        With coordinates the node opens on the map with Alt+Click.

        A GENERIC place (city, region, country) stays confined to its target:
        the id carries the target's prefix, so "Tripoli" mentioned in ten case
        files becomes ten distinct nodes and creates no links between unrelated
        people. Only an ADDRESS (street address or coordinates) is shared and
        can therefore join two cards."""
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
                 sources=["vehicle"], record=record)
        map_ident(vid, targa)
        return vid

    def search_anchor(fn, tid):
        """Search node to hang an export on: the identifier in the file name
        (email, phone or user name). It stays attached to the target, so the
        hierarchy becomes  target -> searched identifier -> results found,
        instead of linking everything directly to the target.
        Returns None if the file is not an export or the query cannot be parsed."""
        q = export_query(fn)
        if not q:
            return None
        if "@" in q and "." in q.split("@")[-1]:
            nid = node_email(q, source="search")
        elif re.fullmatch(r"\+?[0-9][0-9\s().\-]{5,}", q):
            nid = node_phone(q, source="search")
        else:
            nid = node_username(q, source="search")
        add_edge(tid, nid, "target")              # the identifier stays attached to the target
        return nid

    # ---------- "normal" card (export of a service) ----------
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

        # --- phones: one node per number, the numbers of the same card are linked
        phone_ids = [node_phone(p, source=coll) for p in phones]
        for extra in phone_ids[1:]:
            add_edge(phone_ids[0], extra, "phone-link")

        # --- email: the secondary ones are linked to the main one
        email_ids = [node_email(e, source=coll) for e in emails]
        for extra in email_ids[1:]:
            add_edge(email_ids[0], extra, "email-alias")

        # --- username
        user_ids = [node_username(u, platform, coll) for u in usernames]

        # --- main node(s) of the card
        primary = []
        if on_target:
            add_node(tid, image=img, sources=[coll or "dossier"], record=record)
            primary = [tid]

        elif idents:
            # ONE node per SERVICE: several identifiers of the same social network are
            # the same account (snapchatid:UUID + snapchat:nick), different
            # services in the same card (instagram + threads) stay distinct
            groups = {}
            for ident in idents:
                svc, val = parse_identifier(ident)
                groups.setdefault(svc or platform, []).append((ident, val))

            for svc, items in groups.items():
                # canonical id: the readable identifier is preferred to the opaque one
                items = sorted(items, key=lambda t: (bool(OPAQUE_ID.match(t[1] or "")), t[0]))
                canon_ident, canon_val = items[0]
                aid = "acct:" + canon_ident.strip().lower()
                # profile from an API (Epieos): the label is the profile name,
                # the userid stays the identity and is kept in the card
                lab = str(label) if schema.startswith("epieos:") and label else ident_label(canon_val, label)
                add_node(aid, label=lab, ntype="account",
                         platform=svc or platform, image=img,
                         sources=[coll], record=record)
                # ALL the identifiers of the group point to this node: different
                # cards that mention only one of them still end up on the same node
                for ident, val in items:
                    map_acct(aid, svc, val)
                for un in usernames:            # user name unique per platform:
                    map_acct(aid, svc, un)      # different ids + same nick = same account
                primary.append(aid)

            for extra in primary[1:]:
                add_edge(primary[0], extra, "alias")

        elif platform in MESSAGING and phones:
            # messaging without identifier: the account IS the number -> whatsapp-<number>
            for ph, pid in zip(phones, phone_ids):
                aid = f"acct:{platform}-{phone_key(ph)}"
                lab = str(label) if label and label != ph else f"{platform} {ph}"
                add_node(aid, label=lab, ntype="account", platform=platform,
                         image=img, sources=[coll], record=record)
                add_edge(aid, pid, "phone")
                primary.append(aid)

        elif phones and (schema in PHONE_CARD_SCHEMAS or cat in PHONE_CARD_CATEGORIES
                         or not (emails or usernames)):
            # aggregator/lookup: the card describes the number, lists the services found
            for pid in phone_ids:
                add_node(pid, sources=[coll], record=record)
            primary = list(phone_ids)
            # the names under which the number is saved become nodes of their own:
            # they recur across several phone lines and are an excellent anchor.
            # If they are in a non-Latin script, add_translit creates by itself
            # the node with the Latin form, linked to the original.
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

        # --- places mentioned in the card (cities, addresses, coordinates)
        place_ids, visti = [], set()
        for info in collect_places(rec):
            pid = node_place(info, coll, tid)
            if pid and pid not in visti:
                visti.add(pid)
                place_ids.append(pid)
            if len(place_ids) >= 12:            # a card never mentions more
                break

        # --- which node does the card attach to?
        # The dossier goes on the target; an OSINT export goes on the SEARCH NODE
        # that produced it (the identifier in the file name), not on the target.
        # If the query cannot be parsed it falls back to the target (no orphans).
        anchor = tid
        if not on_target:
            anchor = search_anchor(fn, tid) or tid

        # --- data breaches (hibp), sites with an account (holehe,
        #     phonechecker), organisations (linkedin): Epieos extensions
        extra_ids = []
        for br in (rec.get("breaches") or []):
            name = re.sub(r"\s+", " ", str(br)).strip()
            if not name:
                continue
            bid = "breach:" + slug(name)
            add_node(bid, label=name, ntype="breach", platform="breach", sources=[coll],
                     record={"collection": coll, "images": [], "links": [],
                             "raw": {"Breach": name, "Source": coll}})
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
                                             "raw": {"Site": site, "Registered with": str(rec.get("query") or "")}})
            extra_ids.append((sid, "registered"))
        for org in (rec.get("organizations") or []):
            if not isinstance(org, dict) or not str(org.get("name") or "").strip():
                continue
            fields = {"name": str(org["name"]).strip()}
            oid = "organization:" + onto.ident_of("organization", fields)
            add_node(oid, label=fields["name"], ntype="organization", platform="organization",
                     sources=[coll], record={"collection": coll, "images": [], "links": [],
                                             "raw": {"Name": fields["name"],
                                                     "Role": org.get("role") or "", "Period": org.get("period") or ""}})
            extra_ids.append((oid, org.get("role") or ("student" if org.get("kind") == "school" else "organization")))

        # --- links
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

        # --- blocks in "structured dossier" format (compatibility)
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
                                   {"collection": "vehicle", "images": [], "links": [], "raw": veh})
                add_edge(primary[0] if primary else anchor, vid, "vehicle")

    # ---------- investigative dossier (A22.json and similar) ----------
    def handle_dossier(rec, tid, fn):
        coll = rec.get("collection") or "dossier"
        add_node(tid, sources=[coll],
                 record={"collection": coll, "schema": rec.get("schema"),
                         "category": "dossier", "images": [], "links": [], "raw": rec})

        card = lambda voce: {"collection": coll, "images": [], "links": [],
                             "raw": {"Entry": voce, "Source": fn}}

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
                continue                              # handled by handle_record
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
            if user:                            # same nick on the same social network =
                map_acct(aid, svc, user)        # same account, even with different ids
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
            rec = card(voce)
            if paese:
                rec["raw"]["Country"] = paese      # sign of the country: the flag of the node
            add_edge(tid, node_vehicle(targa, lab, rec), "vehicle")

    # ---------- JSON imported from third-party apps (database) ----------
    # Each file is attached to a node (usually the target, a person): the node
    # itself is created by apply_annotations from its manual entry; here it is
    # declared only so that the file's links have an endpoint.
    n_files = 0
    for imp in store.iter_imports():
        n_files += 1
        tid, fn, dossier = imp["anchor"], imp["filename"], bool(imp["dossier"])
        add_node(tid, label=imp["anchor_label"], ntype=imp["anchor_ntype"],
                 platform=imp["anchor_platform"])
        _seed[0] = dossier                 # the nodes of this file are seed data
        recs = parse_records(imp["content"])
        if len(recs) == 1 and epieos.is_epieos(recs[0]):
            recs = epieos.to_records(recs[0])      # Epieos API response
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
    logging.info(f"Imported JSON: {n_files} files")

    # ---- MERGE by identifier + ROMANISATION ----
    return add_translit(merge_nodes(nodes, edges, ident_map))



TYPE_RANK = {"target": 0, "account": 1, "vehicle": 2, "email": 3,
             "phone": 4, "username": 5, "domain": 6, "photo": 8, "generic": 9}


def _mixed_case(s):
    s = str(s or "")
    return any(c.isupper() for c in s) and any(c.islower() for c in s)


def merge_nodes(nodes, edges, ident_map):
    """Nodes sharing the same identifier become ONE node, which keeps all the
    cards (records) and the alternative labels (aliases)."""
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
        # representative node: most informative type, richest label,
        # on a tie the one with correct upper/lower case is preferred
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
        base["seed"] = any(nodes[i].get("seed") for i in ids)   # seed if any of them is
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
    logging.info(f"Merged nodes: {fused} groups · {len(nodes)} -> {len(merged)} nodes")
    return {"nodes": list(merged.values()), "edges": list(new_edges.values())}
