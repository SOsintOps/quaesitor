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

"""Adapter for the responses of the Epieos API (api.epieos.com).

An Epieos search (email or phone) answers with {"result": {<module>: {...}}}:
one object per queried service, with its own fields (photo, name, nick,
id, profile, email, phones, breaches...). This module turns it into the
RECORDS that the OSINT export engine (app.py: handle_record) already understands:

    collection   the service (-> platform of the account node)
    schema       "epieos:<module>"
    category_id  "checker" for the modules that describe the searched identifier
                 (hibp, holehe, phonechecker, protonmail, adobe...) and not an account
    label, names, usernames, identifiers, emails, phones
    breaches, websites, organizations   (extensions handled by handle_record)
    + all the original fields of the module (the card stays complete; 'photo'
      becomes the image, URLs the links, cities/addresses the place nodes)

The content saved in the archive is the original response inside a wrapper:
    {"epieos": {"kind": "email"|"phone", "pack": "osinter", "query": "...",
                "fetched_at": "...", "credits_left": n, "result": {...}}}
so the conversion can be redone at any time without new calls.
No dependency beyond the standard library."""
# "Fronti nulla fides." (Juvenal, Satires)
# Put no trust in appearances.
import json
import re

MODULES_EMAIL = (
    "flickr", "notion", "gravatar", "trello", "hibp", "foursquare", "etsy", "chess", "substack",
    "mapstr", "dropbox", "google", "holehe", "skype", "plex", "linkedin", "nikerunclub", "fitbit",
    "github", "duolingo", "adobe", "runkeeper", "runtastic", "samsung", "strava", "vivino",
    "facebook", "protonmail",
)
MODULES_PHONE = ("skype", "phonechecker", "hibp", "foursquare", "substack", "mapstr", "duolingo",
                 "facebook", "chess")
MODULES = set(MODULES_EMAIL) | set(MODULES_PHONE)
# modules that describe the searched identifier, not a profile: the card goes
# on the email/phone node ('checker' category of handle_record)
CHECKERS = {"hibp", "holehe", "phonechecker", "protonmail", "adobe", "samsung"}

NAME_KEYS = ("name", "full_name", "display_name", "real_name", "realname", "given_name")
USER_KEYS = ("username", "login", "handle", "preferred_username", "screen_name", "login_name", "alias")
ID_KEYS = ("id", "uuid", "user_id", "guid")
FALSE = {"", "false", "none", "null", "0", "n/a"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"\+?[\d\s().\-*]{6,}")


def _is_email(v):
    return bool(EMAIL_RE.match(v or ""))


def _s(v):
    """Meaningful string value ('false', empty, None -> '')."""
    if v is None or isinstance(v, (dict, list)):
        return ""
    v = str(v).strip()
    return "" if v.lower() in FALSE else v


def is_epieos(obj):
    """API response ({"result": {...}}) or wrapper {"epieos": {...}}."""
    if not isinstance(obj, dict):
        return False
    if isinstance(obj.get("epieos"), dict) and isinstance(obj["epieos"].get("result"), dict):
        return True
    res = obj.get("result")
    return isinstance(res, dict) and bool(res) and all(k in MODULES for k in res)


def unwrap(obj):
    """-> (meta, result). meta: kind, pack, query, fetched_at, credits_left."""
    if isinstance(obj.get("epieos"), dict):
        w = obj["epieos"]
        return ({k: w.get(k) for k in ("kind", "pack", "query", "fetched_at", "credits_left")},
                w.get("result") or {})
    res = obj.get("result") or {}
    q = next((_s(m.get("query")) for m in res.values() if isinstance(m, dict) and _s(m.get("query"))), "")
    kind = "email" if "@" in q else ("phone" if re.sub(r"\D", "", q) else "")
    return {"kind": kind, "pack": "", "query": q, "fetched_at": "", "credits_left": None}, res


def wrap(result, kind, query, pack="osinter", fetched_at="", credits_left=None):
    return {"epieos": {"kind": kind, "pack": pack, "query": query, "fetched_at": fetched_at,
                       "credits_left": credits_left, "result": result}}


def _first(d, keys):
    for k in keys:
        v = _s(d.get(k))
        if v:
            return v
    return ""


def _full_name(d):
    n = _first(d, NAME_KEYS)
    if n:
        return n
    fn, ln = _s(d.get("first_name")), _s(d.get("last_name"))
    if fn or ln:
        return f"{fn} {ln}".strip()
    return ""


def _base(module, data, query, kind):
    """Generic record of a module: label, names, nicks, id, emails, phones."""
    rec = {k: v for k, v in data.items() if k != "query"}
    rec["query"] = query
    rec["collection"] = module
    rec["schema"] = f"epieos:{module}"
    label = _full_name(data) or _first(data, USER_KEYS)
    names = []
    for k in NAME_KEYS:
        v = _s(data.get(k))
        if v and v not in names:
            names.append(v)
    fl = f"{_s(data.get('first_name'))} {_s(data.get('last_name'))}".strip()
    if fl and fl not in names:
        names.append(fl)
    usernames = []
    for k in USER_KEYS:
        v = _s(data.get(k)).lstrip("@")
        if v and v not in usernames and "@" not in v:
            usernames.append(v)
    # Identity of the profile: the unique userid of the service. Without an id, the
    # nick; without even the nick, the name. Analyst's rule (2026-10-09): the
    # social profile carries name, userid and all its attributes in its card;
    # no person nodes are created from profiles.
    idents = []
    for k in ID_KEYS:
        v = _s(data.get(k))
        if v:
            idents.append(f"{module}id:{v}")
            break
    if not idents and usernames:
        idents.append(f"{module}:{usernames[0]}")
    elif not idents and (label or names):
        idents.append(f"{module}:{re.sub(r'[^a-z0-9]+', '-', (label or names[0]).lower()).strip('-')}")
    emails, phones = [], []
    for k in ("email",):
        v = _s(data.get(k))
        if _is_email(v):
            emails.append(v)
    for p in (data.get("phones") or []):
        if _s(p):
            phones.append(_s(p))
    for pn in (data.get("phone_numbers") or []):
        if isinstance(pn, dict) and _s(pn.get("value")):
            phones.append(_s(pn["value"]))
    for cp in (data.get("contactpoints") or []):
        if isinstance(cp, dict):
            t, v = _s(cp.get("type")).lower(), _s(cp.get("value"))
            if not v:
                continue
            if "phone" in t or "tel" in t or "mobile" in t or PHONE_RE.fullmatch(v):
                phones.append(v)
            elif "mail" in t or _is_email(v):
                emails.append(v)
            elif v.startswith("@"):
                usernames.append(v.lstrip("@"))
    for acc in (data.get("accounts") or []) if module == "samsung" else []:
        if isinstance(acc, dict):
            t, v = _s(acc.get("type")).lower(), _s(acc.get("value"))
            if v and ("mail" in t or _is_email(v)):
                emails.append(v)
            elif v and ("phone" in t or PHONE_RE.fullmatch(v)):
                phones.append(v)
    for rm in (data.get("recovery_methods") or []):
        if isinstance(rm, dict) and _s(rm.get("value")):
            v, t = _s(rm["value"]), _s(rm.get("type")).lower()
            (emails if "mail" in t or _is_email(v) else phones).append(v)
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    for k, v in contact.items():
        v = _s(v)
        if not v:
            continue
        if _is_email(v):
            emails.append(v)
        elif "phone" in k.lower() or PHONE_RE.fullmatch(v):
            phones.append(v)
        elif k.lower() in ("twitter", "facebook", "instagram", "x"):
            usernames.append(v.lstrip("@"))   # foursquare social handle
        elif not v.startswith("http"):
            usernames.append(v.lstrip("@"))
    rec["label"] = label or module
    # profile attributes in fixed keys (card and FtM UserAccount export)
    rec["profile_name"] = _full_name(data)
    rec["profile_username"] = usernames[0] if usernames else ""
    rec["profile_id"] = idents[0].split(":", 1)[1] if idents and idents[0].startswith(f"{module}id:") else ""
    rec["profile_url"] = _first(data, ("profile", "profile_url", "url", "member_url", "link"))
    rec["profile_created"] = _first(data, ("created_at", "creation_date", "created", "joined", "registered"))
    rec["names"] = list(dict.fromkeys(names))
    rec["usernames"] = list(dict.fromkeys(usernames))
    rec["identifiers"] = idents
    rec["emails"] = list(dict.fromkeys(e for e in emails if _is_email(e)))
    rec["phones"] = list(dict.fromkeys(p for p in phones if p))
    checker = module in CHECKERS or not (names or usernames or idents)
    if checker:
        # The card describes the searched identifier and attaches to its node
        # (email or phone); no name node from the label. For a phone the
        # 'checker' category puts the card on the number's node; for an
        # email the card goes on the email node and the phones found (account
        # recovery) stay linked nodes.
        rec["label"] = ""
        rec["category_id"] = "checker" if kind == "phone" else "account"
        if kind == "email" and query not in rec["emails"]:
            rec["emails"].insert(0, query)
        elif kind == "phone" and query not in rec["phones"]:
            rec["phones"].insert(0, query)
    return rec


def to_records(obj):
    """Epieos response -> records for handle_record (one per module, plus the
    derived ones: other Facebook accounts, Skype/Flickr accounts, Gravatar profiles)."""
    meta, result = unwrap(obj)
    query, kind = _s(meta.get("query")), meta.get("kind") or ""
    out = []
    for module, data in result.items():
        if not isinstance(data, dict) or not data:
            continue
        if module not in MODULES and not any(_s(v) for v in data.values()):
            continue
        q = _s(data.get("query")) or query
        if not kind:
            kind = "email" if "@" in q else "phone"
        # 'found/not found' modules: no card if not found
        if _s(data.get("found")).lower() == "false" or _s(data.get("exists")).lower() == "false":
            continue
        if module in ("skype", "flickr") and isinstance(data.get("accounts"), list):
            for acc in data["accounts"]:
                if isinstance(acc, dict):
                    sub = dict(acc)
                    sub.setdefault("photo", _s(data.get("photo")))
                    out.append(_base(module, sub, q, kind))
            continue
        if module == "gravatar" and isinstance(data.get("accounts"), list):
            for acc in data["accounts"]:
                if not isinstance(acc, dict):
                    continue
                sub = dict(acc)
                sub.setdefault("photo", _s(data.get("photo")))
                if _s(acc.get("profile_url")):
                    sub["profile"] = _s(acc["profile_url"])
                out.append(_base("gravatar", sub, q, kind))
                # linked profiles declared on the Gravatar (domain, url, userid)
                for link in (acc.get("accounts") or []):
                    if not isinstance(link, dict):
                        continue
                    dom = _s(link.get("domain")) or _s(link.get("shortname")) or _s(link.get("name"))
                    svc = re.sub(r"^www\.|\.(com|net|org|it|io|tv|me|co)$", "", dom.lower()) or "generic"
                    r = {"collection": svc, "schema": "epieos:gravatar", "query": q,
                         "label": _s(link.get("display")).lstrip("@") or _s(link.get("name")) or svc,
                         "names": [], "usernames": [], "identifiers": [], "emails": [], "phones": [],
                         "url": _s(link.get("url")), "verified": _s(link.get("verified")),
                         "via": "gravatar"}
                    uid = _s(link.get("userid"))
                    if uid:
                        r["identifiers"] = [f"{re.sub(r'[^a-z0-9]', '', svc)}id:{uid}"]
                    disp = _s(link.get("display")).lstrip("@")
                    if disp and "@" not in disp and " " not in disp:
                        r["usernames"] = [disp]
                        r["profile_username"] = disp
                    r["profile_url"] = r["url"]
                    r["profile_id"] = uid
                    out.append(r)
            continue
        rec = _base(module, data, q, kind)
        if module == "hibp":
            rec["breaches"] = [_s(x) for x in (data.get("leaks") or []) if _s(x)]
        if module in ("holehe", "phonechecker"):
            rec["websites"] = [_s(x) for x in (data.get("websites") or []) if _s(x)]
        if module == "linkedin":
            orgs = []
            for c in (data.get("companies") or []):
                if isinstance(c, dict) and _s(c.get("name")):
                    orgs.append({"name": _s(c["name"]), "role": _s(c.get("title")), "period": _s(c.get("period"))})
            for sch in (data.get("schools") or []):
                if isinstance(sch, dict) and _s(sch.get("name")):
                    orgs.append({"name": _s(sch["name"]), "role": _s(sch.get("field")) or "studente",
                                 "period": _s(sch.get("period")), "kind": "school"})
            if orgs:
                rec["organizations"] = orgs
        if module == "facebook":
            for oa in (data.get("other_accounts") or []):
                if isinstance(oa, dict) and (_s(oa.get("name")) or oa.get("contactpoints")):
                    sub = dict(oa)
                    sub["via"] = "facebook other_accounts"
                    out.append(_base("facebook", sub, q, kind))
        if module == "dropbox" and isinstance(data.get("paired_account"), dict):
            pa = dict(data["paired_account"])
            if _s(pa.get("display_name")) or _s(pa.get("email")):
                pa["via"] = "dropbox paired_account"
                out.append(_base("dropbox", pa, q, kind))
        out.append(rec)
    return out


def summary(obj):
    """Counts for the summary: modules with a result and records produced."""
    meta, result = unwrap(obj)
    found = [m for m, d in result.items() if isinstance(d, dict) and d
             and _s(d.get("found")).lower() != "false" and _s(d.get("exists")).lower() != "false"]
    return {"query": meta.get("query"), "kind": meta.get("kind"), "modules": sorted(found),
            "records": len(to_records(obj))}


def loads(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None
