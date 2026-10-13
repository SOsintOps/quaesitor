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

"""SQLite store of the application, organised by CASES (case files).

    data/osintgraph.db        GLOBAL store, shared by all cases:
        cases                 list of cases
        translit              transliteration dictionary
        blobs                 document index (sources)
        meta                  current case, dictionary version
    data/cases/<id>.db        one database per case:
        imports               JSON imported from third-party apps, attached to a node
        ann_*                 annotations: manually added nodes (and cards),
                              links, notes, labels, edited values,
                              styles, hidden nodes
        views                 saved graph views
        meta                  data version (invalidates the graph cache)

Annotations are read as a single dictionary (load_annotations) and saved
as a DIFF against what was read (save_annotations): only the changed rows
are written, in one transaction. So two close requests touching
different things do not overwrite each other.
"""
# "Veritas filia temporis." (Aulus Gellius, Noctes Atticae)
# Truth is the daughter of time.
import os
import json
import time
import sqlite3
import logging
import threading

import re
import uuid

DB_NAME = "osintgraph.db"
CASES_DIR = "cases"
_data_dir = None
_g_path = None                  # global store
_db_path = None                 # database of the current case
_case_id = None
_local = threading.local()
_write_lock = threading.RLock()

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS imports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor       TEXT NOT NULL,          -- id of the node (target) it is attached to
    anchor_label TEXT NOT NULL,
    anchor_ntype TEXT NOT NULL DEFAULT 'generic',
    anchor_platform TEXT NOT NULL DEFAULT 'generic',
    filename     TEXT NOT NULL,
    content      TEXT NOT NULL,
    size         INTEGER NOT NULL,
    records      INTEGER NOT NULL,
    dossier      INTEGER NOT NULL DEFAULT 0,   -- personal-details card of the target
    imported_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS imports_anchor ON imports(anchor);
CREATE TABLE IF NOT EXISTS ann_added      (id TEXT PRIMARY KEY, seq INTEGER NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ann_links      (id TEXT PRIMARY KEY, seq INTEGER NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ann_deleted    (id TEXT PRIMARY KEY, seq INTEGER NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ann_notes      (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ann_labels     (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ann_edits      (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ann_edge_styles(id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ann_targets    (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS views (
    id    TEXT PRIMARY KEY,
    name  TEXT NOT NULL,
    at    TEXT NOT NULL,
    count INTEGER NOT NULL,
    data  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ftm_ids (
    ftm_id     TEXT PRIMARY KEY,          -- id of the Follow the Money entity
    node_id    TEXT NOT NULL,             -- graph node that represents it
    schema     TEXT NOT NULL DEFAULT '',
    dataset    TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ftm_ids_node ON ftm_ids(node_id);
"""

SCHEMA_GLOBAL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS blobs (
    key   TEXT PRIMARY KEY,
    data  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS translit (
    word       TEXT PRIMARY KEY,
    value      TEXT NOT NULL DEFAULT '',
    source     TEXT NOT NULL CHECK (source IN ('manual', 'ai', 'pending')),
    script     TEXT NOT NULL DEFAULT '',
    model      TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
"""

# annotation collections: name -> (table, is it an ordered list?)
_ANN_LISTS = {"added": "ann_added", "links": "ann_links", "deleted": "ann_deleted"}
_ANN_MAPS = {"notes": "ann_notes", "labels": "ann_labels", "edits": "ann_edits",
             "edge_styles": "ann_edge_styles", "targets": "ann_targets"}


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class NoCaseError(RuntimeError):
    """No case open: everything that lives in the case database (nodes,
    links, notes, views, imported JSON) is unavailable."""


def init(data_dir):
    """Open the global store and the current case. If no case exists, one is
    NOT created: the user must create one from the interface (on first
    start the program runs with no cases)."""
    global _data_dir, _g_path
    _data_dir = data_dir
    os.makedirs(os.path.join(data_dir, CASES_DIR), exist_ok=True)
    _g_path = os.path.join(data_dir, DB_NAME)
    _migrate_single_db()
    with _write_lock:
        gconn().executescript(SCHEMA_GLOBAL)
    cid = get_gmeta("current_case")
    if not cid or not case_exists(cid):
        rows = list_cases()
        cid = rows[0]["id"] if rows else None
    if cid:
        open_case(cid)
    else:
        _close_case()
    return _g_path


def _close_case():
    """No current case (store just created or last case deleted)."""
    global _db_path, _case_id
    with _write_lock:
        _db_path, _case_id = None, None
    set_gmeta("current_case", "")


def _migrate_single_db():
    """Before cases there was a single database (data/osintgraph.db) with
    everything: it becomes the first case, and dictionary and index move to
    the global store."""
    if not os.path.exists(_g_path):
        return
    c = sqlite3.connect(_g_path)
    try:
        tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        c.close()
    if "cases" in tabs or "ann_added" not in tabs:
        return
    # The tables are COPIED into the new case's database instead of moving the
    # file: on Windows a file held open by another process (the Flask reloader,
    # a second start) cannot be moved.
    cid = _new_case_id()
    dest = _case_file(cid)
    d = sqlite3.connect(dest)
    try:
        d.executescript(SCHEMA)
        d.execute("ATTACH DATABASE ? AS old", (_g_path,))
        for t in _CASE_TABLES:
            if t in tabs:
                cols = [r[1] for r in d.execute(f"PRAGMA old.table_info({t})")]
                mine = {r[1] for r in d.execute(f"PRAGMA main.table_info({t})")}
                cols = ", ".join(c for c in cols if c in mine)
                d.execute(f"INSERT OR IGNORE INTO main.{t}({cols}) SELECT {cols} FROM old.{t}")
        d.commit()
        d.execute("DETACH DATABASE old")
    finally:
        d.close()
    g = sqlite3.connect(_g_path)
    try:
        g.executescript(SCHEMA_GLOBAL)
        g.execute("INSERT INTO cases(id, name, description, created_at, updated_at) "
                  "VALUES(?, 'Caso 1', '', ?, ?)", (cid, _now(), _now()))
        g.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('current_case', ?)", (cid,))
        g.execute("DELETE FROM meta WHERE key = 'data_version'")
        for t in _CASE_TABLES:
            if t != "meta":
                g.execute(f"DROP TABLE IF EXISTS {t}")     # they now live in the case
        g.commit()
    finally:
        g.close()
    logging.info(f"Archivio convertito: i dati esistenti sono ora il caso {cid}")


# tables that belong to a case (the old single database had all of them)
_CASE_TABLES = ("meta", "imports", "ann_added", "ann_links", "ann_deleted", "ann_notes",
                "ann_labels", "ann_edits", "ann_edge_styles", "ann_targets", "views")


def _new_case_id():
    return "c" + time.strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:4]


def _case_file(cid):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", str(cid or "")):
        raise ValueError("id del caso non valido")
    return os.path.join(_data_dir, CASES_DIR, f"{cid}.db")


def path():
    return _db_path


def current_case():
    return _case_id


def _connect(p):
    c = sqlite3.connect(p, timeout=30, isolation_level=None, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    c.execute("PRAGMA synchronous = NORMAL")
    return c


def conn():
    """Connection to the current CASE database, one per thread (Flask serves
    requests on several threads). It reopens by itself when the case changes."""
    if _db_path is None:
        raise NoCaseError("nessun caso aperto: crea un caso o scegline uno esistente")
    c = getattr(_local, "conn", None)
    if c is None or getattr(_local, "path", None) != _db_path:
        if c is not None:
            try:
                c.close()
            except Exception:
                pass
        c = _connect(_db_path)
        _local.conn, _local.path = c, _db_path
    return c


def gconn():
    """Connection to the GLOBAL store (cases, dictionary, sources index)."""
    c = getattr(_local, "gconn", None)
    if c is None:
        c = _connect(_g_path)
        _local.gconn = c
    return c


class _tx:
    """Write transaction (one at a time in the process)."""
    def __init__(self, glob=False):
        self.glob = glob

    def __enter__(self):
        _write_lock.acquire()
        try:
            self.c = gconn() if self.glob else conn()
            self.c.execute("BEGIN IMMEDIATE")
        except Exception:
            _write_lock.release()
            raise
        return self.c

    def __exit__(self, et, ev, tb):
        try:
            self.c.execute("ROLLBACK" if et else "COMMIT")
        finally:
            _write_lock.release()
        return False


def tx(glob=False):
    return _tx(glob)


# --------------------------------------------------------------------- cases ---
def list_cases():
    rows = gconn().execute("SELECT * FROM cases ORDER BY name COLLATE NOCASE").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["current"] = d["id"] == _case_id
        try:
            d["size"] = os.path.getsize(_case_file(d["id"]))
        except OSError:
            d["size"] = 0
        out.append(d)
    return out


def case_exists(cid):
    return gconn().execute("SELECT 1 FROM cases WHERE id = ?", (cid,)).fetchone() is not None \
        and os.path.exists(_case_file(cid))


def get_case(cid):
    r = gconn().execute("SELECT * FROM cases WHERE id = ?", (cid,)).fetchone()
    return dict(r) if r else None


def create_case(name, description=""):
    cid = _new_case_id()
    c = _connect(_case_file(cid))
    try:
        c.executescript(SCHEMA)
    finally:
        c.close()
    with tx(True) as g:
        g.execute("INSERT INTO cases(id, name, description, created_at, updated_at) "
                  "VALUES(?, ?, ?, ?, ?)", (cid, name, description, _now(), _now()))
    return get_case(cid)


def update_case(cid, name=None, description=None):
    with tx(True) as g:
        if name is not None:
            g.execute("UPDATE cases SET name = ?, updated_at = ? WHERE id = ?", (name, _now(), cid))
        if description is not None:
            g.execute("UPDATE cases SET description = ?, updated_at = ? WHERE id = ?",
                      (description, _now(), cid))
    return get_case(cid)


def open_case(cid):
    """Make the case current: from here on all reads and writes
    (annotations, views, imported JSON) go to its database."""
    global _db_path, _case_id
    p = _case_file(cid)
    c = _connect(p)
    try:
        c.executescript(SCHEMA)          # create or update the case tables
    finally:
        c.close()
    with _write_lock:
        _db_path, _case_id = p, cid
    set_gmeta("current_case", cid)
    return get_case(cid)


def delete_case(cid):
    """Delete the case and its database (images in data/media are kept)."""
    p = _case_file(cid)
    with tx(True) as g:
        g.execute("DELETE FROM cases WHERE id = ?", (cid,))
    if getattr(_local, "path", None) == p and getattr(_local, "conn", None) is not None:
        _local.conn.close()
        _local.conn = None
    if cid == _case_id:
        _close_case()                    # it was the open case: now there is none
    for ext in ("", "-wal", "-shm"):
        try:
            os.remove(p + ext)
        except OSError:
            pass


def merge_cases(ids, name, description=""):
    """New case with the content of all the given cases. Items with the same
    id (same person, same phone...) become ONE node: if the data differ, the
    entry from the second case becomes an extra card."""
    new = create_case(name, description)
    dest = _connect(_case_file(new["id"]))
    try:
        for cid in ids:
            src = _case_file(cid)
            if not os.path.exists(src):
                continue
            _merge_into(dest, src)
    finally:
        dest.close()
    return new


def _merge_into(dest, src):
    s = _connect(src)
    try:
        dest.execute("BEGIN IMMEDIATE")
        # lists (added nodes, links, hidden nodes)
        for table in ("ann_added", "ann_links", "ann_deleted"):
            base = dest.execute(f"SELECT COALESCE(MAX(seq), 0) FROM {table}").fetchone()[0]
            for r in s.execute(f"SELECT id, data FROM {table} ORDER BY seq"):
                old = dest.execute(f"SELECT data FROM {table} WHERE id = ?", (r["id"],)).fetchone()
                if old is not None:
                    if old["data"] == r["data"] or table == "ann_deleted":
                        continue
                    # same id, different data: extra card (nodes) or new link
                    nid = f"{r['id'].split('~')[0]}~{uuid.uuid4().hex[:6]}"
                    d = json.loads(r["data"])
                    d["id"] = nid
                    if table == "ann_links" and "edge_id" in d:
                        d["edge_id"] = nid
                    if table == "ann_added" and d.get("edge_id"):
                        d["edge_id"] = f"{d['edge_id']}_{uuid.uuid4().hex[:4]}"
                    data, rid = _dumps(d), nid
                else:
                    data, rid = r["data"], r["id"]
                base += 1
                dest.execute(f"INSERT INTO {table}(id, seq, data) VALUES(?, ?, ?)", (rid, base, data))
        # notes: if present in both cases, both are kept
        for r in s.execute("SELECT id, data FROM ann_notes"):
            old = dest.execute("SELECT data FROM ann_notes WHERE id = ?", (r["id"],)).fetchone()
            if old is None:
                dest.execute("INSERT INTO ann_notes(id, data) VALUES(?, ?)", (r["id"], r["data"]))
            elif old["data"] != r["data"]:
                a, b = json.loads(old["data"]), json.loads(r["data"])
                dest.execute("UPDATE ann_notes SET data = ? WHERE id = ?",
                             (_dumps(f"{a}\n---\n{b}"), r["id"]))
        # labels, edited values, styles: the first case wins
        for table in ("ann_labels", "ann_edits", "ann_edge_styles"):
            for r in s.execute(f"SELECT id, data FROM {table}"):
                dest.execute(f"INSERT OR IGNORE INTO {table}(id, data) VALUES(?, ?)", (r["id"], r["data"]))
        # views: renamed if the id is the same
        for r in s.execute("SELECT * FROM views"):
            vid = r["id"]
            if dest.execute("SELECT 1 FROM views WHERE id = ?", (vid,)).fetchone():
                vid = f"{vid}_{uuid.uuid4().hex[:4]}"
            d = json.loads(r["data"])
            d["id"] = vid
            dest.execute("INSERT INTO views(id, name, at, count, data) VALUES(?, ?, ?, ?, ?)",
                         (vid, r["name"], r["at"], r["count"], _dumps(d)))
        # imported JSON: all of them (new ids)
        for r in s.execute("SELECT * FROM imports ORDER BY imported_at, id"):
            dest.execute("INSERT INTO imports(anchor, anchor_label, anchor_ntype, anchor_platform, "
                         "filename, content, size, records, dossier, imported_at) "
                         "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (r["anchor"], r["anchor_label"], r["anchor_ntype"], r["anchor_platform"],
                          r["filename"], r["content"], r["size"], r["records"], r["dossier"],
                          r["imported_at"]))
        _bump(dest)
        dest.execute("COMMIT")
    except Exception:
        dest.execute("ROLLBACK")
        raise
    finally:
        s.close()


# -------------------------------------------------------------- data version ---
def bump(key="data_version"):
    """Signal that the data the graph is built from have changed."""
    with tx() as c:
        _bump(c, key)


def _bump(c, key="data_version"):
    c.execute("INSERT INTO meta(key, value) VALUES(?, '1') ON CONFLICT(key) "
              "DO UPDATE SET value = CAST(CAST(value AS INTEGER) + 1 AS TEXT)", (key,))


def version(key="data_version"):
    """Version of the case data (or of the dictionary, which is global)."""
    c = gconn() if key == "translit_version" else conn()
    r = c.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return int(r["value"]) if r else 0


def get_meta(key, default=None):
    r = conn().execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return r["value"] if r else default


def set_meta(key, value):
    with tx() as c:
        c.execute("INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) "
                  "DO UPDATE SET value = excluded.value", (key, str(value)))


def get_gmeta(key, default=None):
    r = gconn().execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return r["value"] if r else default


def set_gmeta(key, value):
    with tx(True) as c:
        c.execute("INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) "
                  "DO UPDATE SET value = excluded.value", (key, str(value)))


# ---------------------------------------------------------------- annotations ---
def _dumps(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True)


def load_annotations():
    """{'added': [...], 'links': [...], 'deleted': [...], 'notes': {}, 'labels': {},
    'edits': {}, 'edge_styles': {}} + '_snap' (state as read, for saving)."""
    c = conn()
    ann, snap = {}, {}
    for name, table in _ANN_LISTS.items():
        rows = c.execute(f"SELECT id, data FROM {table} ORDER BY seq").fetchall()
        ann[name] = [json.loads(r["data"]) for r in rows]
        snap[name] = {r["id"]: r["data"] for r in rows}
    for name, table in _ANN_MAPS.items():
        rows = c.execute(f"SELECT id, data FROM {table}").fetchall()
        ann[name] = {r["id"]: json.loads(r["data"]) for r in rows}
        snap[name] = {r["id"]: r["data"] for r in rows}
    ann["_snap"] = snap
    return ann


def _list_key(name, item):
    if name == "links":
        return str(item.get("id") or item.get("edge_id") or "")
    return str(item.get("id") or "")


def save_annotations(ann):
    """Write only the differences from what load_annotations read."""
    snap = ann.get("_snap") or {}
    with tx() as c:
        for name, table in _ANN_LISTS.items():
            old = snap.get(name, {})
            cur, order = {}, []
            for item in ann.get(name) or []:
                k = _list_key(name, item)
                if k and k not in cur:
                    cur[k] = _dumps(item)
                    order.append(k)
            for k in set(old) - set(cur):
                c.execute(f"DELETE FROM {table} WHERE id = ?", (k,))
            base = c.execute(f"SELECT COALESCE(MAX(seq), 0) FROM {table}").fetchone()[0]
            for k in order:
                if k not in old:
                    base += 1
                    c.execute(f"INSERT INTO {table}(id, seq, data) VALUES(?, ?, ?) "
                              f"ON CONFLICT(id) DO UPDATE SET data = excluded.data",
                              (k, base, cur[k]))
                elif old[k] != cur[k]:
                    c.execute(f"UPDATE {table} SET data = ? WHERE id = ?", (cur[k], k))
        for name, table in _ANN_MAPS.items():
            old = snap.get(name, {})
            cur = {str(k): _dumps(v) for k, v in (ann.get(name) or {}).items()}
            for k in set(old) - set(cur):
                c.execute(f"DELETE FROM {table} WHERE id = ?", (k,))
            for k, v in cur.items():
                if old.get(k) != v:
                    c.execute(f"INSERT INTO {table}(id, data) VALUES(?, ?) "
                              f"ON CONFLICT(id) DO UPDATE SET data = excluded.data", (k, v))
    # the next save of the same dictionary starts from here
    ann["_snap"] = {n: {_list_key(n, i): _dumps(i) for i in ann.get(n) or []}
                    for n in _ANN_LISTS}
    ann["_snap"].update({n: {str(k): _dumps(v) for k, v in (ann.get(n) or {}).items()}
                         for n in _ANN_MAPS})
    return True


# ---------------------------------------------------------------------- views ---
def load_views():
    rows = conn().execute("SELECT data FROM views ORDER BY at").fetchall()
    return [json.loads(r["data"]) for r in rows]


def get_view(vid):
    r = conn().execute("SELECT data FROM views WHERE id = ?", (vid,)).fetchone()
    return json.loads(r["data"]) if r else None


def save_view(v):
    with tx() as c:
        c.execute("INSERT INTO views(id, name, at, count, data) VALUES(?, ?, ?, ?, ?) "
                  "ON CONFLICT(id) DO UPDATE SET name = excluded.name, at = excluded.at, "
                  "count = excluded.count, data = excluded.data",
                  (v["id"], v.get("name") or v["id"], v.get("at") or _now(),
                   int(v.get("count") or 0), _dumps(v)))


def delete_view(vid):
    with tx() as c:
        return c.execute("DELETE FROM views WHERE id = ?", (vid,)).rowcount


# ------------------------------------------------------------ transliteration ---
def translit_dict():
    """{word: Latin form}; '' = known word not yet translated."""
    rows = gconn().execute("SELECT word, value FROM translit").fetchall()
    return {r["word"]: r["value"] for r in rows}


def translit_rows(source=None, query="", limit=500, offset=0):
    sql, args = "SELECT * FROM translit WHERE 1=1", []
    if source:
        sql += " AND source = ?"
        args.append(source)
    if query:
        sql += " AND (word LIKE ? OR value LIKE ?)"
        args += [f"%{query}%", f"%{query}%"]
    sql += " ORDER BY updated_at DESC, word LIMIT ? OFFSET ?"
    args += [limit, offset]
    return [dict(r) for r in gconn().execute(sql, args).fetchall()]


def translit_counts():
    rows = gconn().execute("SELECT source, COUNT(*) AS n FROM translit GROUP BY source").fetchall()
    return {r["source"]: r["n"] for r in rows}


def translit_add_pending(words, script_of=None):
    """New words, to be translated: existing ones are left untouched."""
    if not words:
        return 0
    n = 0
    with tx(True) as c:
        for w in words:
            n += c.execute("INSERT OR IGNORE INTO translit(word, value, source, script, updated_at) "
                           "VALUES(?, '', 'pending', ?, ?)",
                           (w, (script_of(w) if script_of else "") or "", _now())).rowcount
        if n:
            _bump(c, "translit_version")
    return n


def translit_save_ai(values, model=""):
    """AI translations: they never overwrite a manual translation."""
    if not values:
        return 0
    n = 0
    with tx(True) as c:
        for w, v in values.items():
            n += c.execute(
                "INSERT INTO translit(word, value, source, model, updated_at) "
                "VALUES(?, ?, 'ai', ?, ?) ON CONFLICT(word) DO UPDATE SET "
                "value = excluded.value, source = 'ai', model = excluded.model, "
                "updated_at = excluded.updated_at "
                "WHERE translit.source <> 'manual' OR translit.value = ''",
                (w, v, model, _now())).rowcount
        if n:
            _bump(c, "translit_version")
    return n


def translit_set(word, value):
    """Manual translation (always wins); empty value = to be translated."""
    value = str(value or "").strip()
    with tx(True) as c:
        c.execute("INSERT INTO translit(word, value, source, updated_at) VALUES(?, ?, ?, ?) "
                  "ON CONFLICT(word) DO UPDATE SET value = excluded.value, "
                  "source = excluded.source, model = '', updated_at = excluded.updated_at",
                  (word, value, "manual" if value else "pending", _now()))
        _bump(c, "translit_version")


def translit_delete(word):
    with tx(True) as c:
        n = c.execute("DELETE FROM translit WHERE word = ?", (word,)).rowcount
        if n:
            _bump(c, "translit_version")
        return n


# ------------------------------------------- Follow the Money entities ---
def ftm_map():
    """{FtM id: node id} of the current case (for re-import and export)."""
    rows = conn().execute("SELECT ftm_id, node_id FROM ftm_ids").fetchall()
    return {r["ftm_id"]: r["node_id"] for r in rows}


def ftm_by_node():
    """{node id: (FtM id, schema, dataset)}: for export."""
    rows = conn().execute("SELECT ftm_id, node_id, schema, dataset FROM ftm_ids").fetchall()
    return {r["node_id"]: (r["ftm_id"], r["schema"], r["dataset"]) for r in rows}


def ftm_set(items):
    """items: iterable of (ftm_id, node_id, schema, dataset). Overwrites."""
    items = list(items)
    if not items:
        return 0
    with tx() as c:
        c.executemany("INSERT INTO ftm_ids(ftm_id, node_id, schema, dataset, updated_at) "
                      "VALUES(?, ?, ?, ?, ?) ON CONFLICT(ftm_id) DO UPDATE SET "
                      "node_id = excluded.node_id, schema = excluded.schema, "
                      "dataset = excluded.dataset, updated_at = excluded.updated_at",
                      [(a, b, c_ or "", d or "", _now()) for a, b, c_, d in items])
    return len(items)


def ftm_forget_nodes(node_ids):
    node_ids = [str(x) for x in node_ids if x]
    if not node_ids:
        return 0
    with tx() as c:
        n = 0
        for i in range(0, len(node_ids), 500):
            chunk = node_ids[i:i + 500]
            n += c.execute("DELETE FROM ftm_ids WHERE node_id IN (%s)" % ",".join("?" * len(chunk)),
                           chunk).rowcount
    return n


# ------------------------------------- JSON imported from third-party apps ---
def add_import(anchor, anchor_label, filename, content, records, dossier=False,
               anchor_ntype="generic", anchor_platform="generic"):
    with tx() as c:
        cur = c.execute("INSERT INTO imports(anchor, anchor_label, anchor_ntype, anchor_platform, "
                        "filename, content, size, records, dossier, imported_at) "
                        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (anchor, anchor_label, anchor_ntype, anchor_platform, filename, content,
                         len(content.encode("utf-8")), records, int(bool(dossier)), _now()))
        _bump(c)
        return cur.lastrowid


def list_imports(anchor=None):
    sql = ("SELECT id, anchor, anchor_label, filename, size, records, dossier, imported_at "
           "FROM imports" + (" WHERE anchor = ?" if anchor else "") +
           " ORDER BY anchor_label COLLATE NOCASE, imported_at, id")
    return [dict(r) for r in conn().execute(sql, (anchor,) if anchor else ()).fetchall()]


def delete_import(iid):
    with tx() as c:
        n = c.execute("DELETE FROM imports WHERE id = ?", (iid,)).rowcount
        if n:
            _bump(c)
        return n


def delete_imports_of(anchors):
    """JSON attached to these nodes (deleted together with the node)."""
    anchors = list(anchors)
    if not anchors:
        return 0
    with tx() as c:
        n = c.execute(f"DELETE FROM imports WHERE anchor IN ({','.join('?' * len(anchors))})",
                      anchors).rowcount
        if n:
            _bump(c)
        return n


def iter_imports():
    """Rows of the imported JSON (dict), in import order."""
    rows = conn().execute("SELECT id, anchor, anchor_label, anchor_ntype, anchor_platform, "
                          "filename, content, dossier FROM imports ORDER BY imported_at, id").fetchall()
    for r in rows:
        yield dict(r)


# ------------------------------------------ JSON blobs (sources index) ---
def get_blob(key):
    r = gconn().execute("SELECT data FROM blobs WHERE key = ?", (key,)).fetchone()
    return json.loads(r["data"]) if r else None


def set_blob(key, value):
    with tx(True) as c:
        c.execute("INSERT INTO blobs(key, data) VALUES(?, ?) ON CONFLICT(key) "
                  "DO UPDATE SET data = excluded.data", (key, json.dumps(value, ensure_ascii=False)))


def is_empty():
    c = conn()
    for t in ("imports", "ann_added", "ann_links", "ann_notes", "views"):
        if c.execute(f"SELECT 1 FROM {t} LIMIT 1").fetchone():
            return False
    return True
