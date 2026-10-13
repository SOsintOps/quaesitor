# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""The records of the OSINT exports: parsing, identifiers and platforms in normal
form, the labels of photos and the values collected from a record."""
# "Ex ungue leonem." (proverb)
# From the claw, the lion.
import json
import os
import re
import unicodedata

from .core import IMG_KEYS, IMG_RE, PHONE_SRC, PLATFORM_TABLE, URL_RE


def parse_records(txt):
    """Records of an export: a JSON array, a single object or JSON Lines."""
    txt = str(txt or "").lstrip("﻿").strip()
    if not txt:
        return []
    try:
        data = json.loads(txt)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        pass
    recs = []
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return recs


def norm_platform(collection):
    c = (collection or "").lower()
    c = re.sub(r"\(.*?\)", "", c).strip()
    c = c.replace(" accounts", "").strip()
    if c in PLATFORM_TABLE:
        return PLATFORM_TABLE[c]
    if c in PHONE_SRC:
        return "phone_src"
    for k, v in PLATFORM_TABLE.items():
        # very short keys ("x") only on an exact match, already handled above:
        # otherwise any collection containing an "x" would become Twitter/X
        if len(k) > 2 and re.search(r"\b" + re.escape(k) + r"\b", c):
            return v
    return re.sub(r"[^a-z0-9]", "", c) or "generic"


def photo_label(filename):
    """Readable label from the file name: separators -> spaces,
    symbols and digits removed. 'andrea_cumini_02.jpg' -> 'andrea cumini'."""
    stem = os.path.splitext(filename)[0]
    s = re.sub(r"[_\-.+]+", " ", stem)
    s = re.sub(r"[^\w\s]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\d+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) < 3:                      # e.g. 'IMG_20240101_1234' -> fall back to the name
        s = re.sub(r"[_\-.+]+", " ", stem)
        s = re.sub(r"\s+", " ", s).strip()
    return s or filename


def export_query(filename):
    """From the name of an OSINT export, extracts the searched identifier that
    produced the response. E.g. 'export_khalifa.ashini@gmail.com.json' ->
    'khalifa.ashini@gmail.com'; 'export_khalifaashini (1).json' -> 'khalifaashini'.
    Returns None if the file is not a recognisable export."""
    stem = os.path.splitext(filename)[0].strip()
    m = re.match(r"(?:export|ricerca|search|lookup)[ _-]+(.+)$", stem, re.I)
    if not m:
        return None
    q = m.group(1).strip()
    q = re.sub(r"\s*\(\d+\)\s*$", "", q)          # strips the ' (1)', ' (2)'… suffix
    q = q.strip().strip("_-. ")
    return q or None


def norm_ident(val):
    """Normalised key used to merge nodes that represent the same identifier."""
    s = str(val or "").strip().lower()
    if not s:
        return ""
    digits = re.sub(r"\D", "", s)
    # phone numbers: compared on the last 9 digits
    if digits and len(digits) >= 8 and len(re.sub(r"[\d\s\+\-\(\)\.]", "", s)) == 0:
        return "num:" + digits[-9:]
    if "@" in s:
        return "mail:" + re.sub(r"\s", "", s)
    s = re.sub(r"[^a-z0-9@._-]", "", s)
    return ("id:" + s) if len(s) >= 4 else ""


# labels too generic to be a merge key
STOP_LABELS = {
    "social", "generic", "account", "accounts", "unknown", "sconosciuto",
    "null", "none", "n a", "na", "nd", "n d", "vehicle", "target", "profilo",
    "profile", "user", "utente", "anagrafica", "dossier", "scheda",
}
STOP_LABELS |= set(PLATFORM_TABLE.keys()) | set(PLATFORM_TABLE.values()) | PHONE_SRC


def norm_label(label, platform=""):
    """Merge key derived from the label: two nodes with the same label are the
    same entity, even with no identifiers in common.
    Returns '' for unreliable labels (generic or too short)."""
    s = unicodedata.normalize("NFKD", str(label or "")).lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) < 3:
        return ""
    if s in STOP_LABELS or s == str(platform or "").lower():
        return ""
    if s.isdigit():                      # numbers go through norm_ident
        return ""
    return "lbl:" + s


def collect(obj, images, links):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and URL_RE.match(v):
                if any(t in k.lower() for t in IMG_KEYS) or IMG_RE.search(v):
                    images.add(v)
                else:
                    links.add(v)
            else:
                collect(v, images, links)
    elif isinstance(obj, list):
        for it in obj:
            collect(it, images, links)
