# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Transliteration: the mode, the AI, the hand-made dictionary."""
# "Nomen est omen." (after Plautus, Persa)
# The name is a sign.
import logging
import re
import time

from flask import Blueprint, jsonify, request

from .. import store
from ..core import _decode_upload, NodeError
from ..chatbot import _bot, CHATBOT, chatbot_ready
from ..transliteration import (
    _auto, ai_fill_translit, load_word_dict, parole_da_traslitterare, script_of,
    TRANSLIT_ENGINE, translit_mode, TRANSLIT_MODES, WORD_RE, write_pending,
)
from ..labels import _cache
from ..archive import current_graph

bp = Blueprint("translit", __name__)


@bp.route("/api/translit/status")
def api_translit_status():
    """How many words are left to transliterate and whether the chatbot is usable."""
    wdict = load_word_dict()
    todo = parole_da_traslitterare(current_graph(), wdict)
    return jsonify({
        "enabled": chatbot_ready(), "auto": bool(CHATBOT["auto"]),
        "model": CHATBOT["model"], "endpoint": CHATBOT["endpoint"],
        "engine": TRANSLIT_ENGINE or "", "todo": len(todo),
        "done": sum(1 for v in wdict.values() if str(v or "").strip()),
        "total": len(wdict),
        "down": bool(time.time() < _bot["down_until"]),
        "reason": _bot["reason"],
        "mode": translit_mode(),
    })


@bp.route("/api/translit/mode", methods=["GET", "POST"])
def api_translit_mode():
    """Where the Latin form goes: 'attribute' (in the node) or 'nodes' (twins)."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        mode = str(data.get("mode") or "").strip()
        if mode not in TRANSLIT_MODES:
            return jsonify({"error": "invalid mode"}), 400
        store.set_gmeta("translit_mode", mode)
        _cache["key"] = None                   # the graph must be rebuilt
        logging.info(f"Transliteration: mode {mode}")
    return jsonify({"ok": True, "mode": translit_mode()})


@bp.route("/api/translit/ai", methods=["POST"])
def api_translit_ai():
    """Has the chatbot transliterate all the words still uncovered.
    If the chatbot does not respond it says so and changes nothing."""
    if not chatbot_ready():
        return jsonify({"error": "AI switched off or endpoint not set "
                                 "(Artificial intelligence panel)"}), 400
    wdict = load_word_dict()
    todo = parole_da_traslitterare(current_graph(), wdict)
    if not todo:
        return jsonify({"ok": True, "translated": 0, "remaining": 0, "error": ""})
    stat = ai_fill_translit(todo, force=True,
                            budget=max(CHATBOT["budget"], 120),
                            max_words=max(CHATBOT["max_words"], len(todo)))
    if not stat["translated"] and stat["error"]:
        return jsonify({"error": stat["error"]}), 502
    if stat["translated"]:
        _cache["key"] = None                  # the Latin labels must be redone
    stat["ok"] = True
    stat.pop("error", None)
    return jsonify(stat)


# ==================== TRANSLITERATION DICTIONARY (by hand) ====================
# The "Dizionario" window of the panel: list of the non-Latin words seen
# in the graph (pending, translated by hand, translated by the AI), inline editing,
# CSV import/export. A value written by hand always wins over the automatic
# engine and the AI (store.translit_set); empty = back to "to translate".
# Every edit increments translit_version: the graph rebuilds itself.

@bp.route("/api/translit/words")
def api_translit_words():
    """Dictionary page. Parameters: q (filter on word or value),
    source (pending | manual | ai | empty = all), limit, offset."""
    q = str(request.args.get("q") or "").strip()[:80]
    source = str(request.args.get("source") or "").strip()
    if source not in ("", "pending", "manual", "ai"):
        source = ""
    try:
        limit = max(1, min(int(request.args.get("limit", 200)), 2000))
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        limit, offset = 200, 0
    rows = store.translit_rows(source or None, q, limit + 1, offset)
    more = len(rows) > limit
    rows = rows[:limit]
    for r in rows:
        # proposal of the automatic engine, shown as a suggestion
        r["auto"] = _auto(r["word"]) if not str(r.get("value") or "").strip() else ""
    return jsonify({"rows": rows, "more": more, "offset": offset,
                    "counts": store.translit_counts(),
                    "engine": TRANSLIT_ENGINE or ""})


@bp.route("/api/translit/set", methods=["POST"])
def api_translit_set():
    """Writes (or clears) the transliteration of a word: {word, value}."""
    data = request.get_json(silent=True) or {}
    word = re.sub(r"\s+", " ", str(data.get("word") or "")).strip()[:120]
    value = re.sub(r"\s+", " ", str(data.get("value") or "")).strip()[:120]
    if not word:
        return jsonify({"error": "word missing"}), 400
    if not script_of(word):
        return jsonify({"error": "the word is already in Latin characters"}), 400
    if value and script_of(value):
        return jsonify({"error": "the transliteration must be in Latin characters"}), 400
    store.translit_set(word, value)
    logging.info(f"Dictionary: {word!r} -> {value!r}" if value else f"Dictionary: {word!r} to transliterate")
    return jsonify({"ok": True, "word": word, "value": value,
                    "source": "manual" if value else "pending"})


@bp.route("/api/translit/delete", methods=["POST"])
def api_translit_delete():
    """Removes the word from the dictionary: it will be pending again if it reappears."""
    data = request.get_json(silent=True) or {}
    word = str(data.get("word") or "").strip()
    if not word:
        return jsonify({"error": "word missing"}), 400
    n = store.translit_delete(word)
    return jsonify({"ok": True, "deleted": n})


@bp.route("/api/translit/collect", methods=["POST"])
def api_translit_collect():
    """Marks as pending ALL the non-Latin words in the graph (not only those
    of the ambiguous scripts), so the automatic romanisations (Chinese,
    Cyrillic...) can be corrected by hand too."""
    words = set()
    for n in current_graph().get("nodes", []):
        if n.get("ntype") == "latin":
            continue
        for lab in [n.get("label")] + list(n.get("aliases") or []):
            for w in WORD_RE.findall(str(lab or "")):
                if script_of(w):
                    words.add(w)
    added = write_pending(words)
    return jsonify({"ok": True, "added": added, "total": len(words)})


@bp.route("/api/translit/import", methods=["POST"])
def api_translit_import():
    """Imports a 'word;transliteration' CSV (also , or tab; with or without a
    header). The rows become MANUAL entries; a row with an empty value puts
    the word back to pending. Body: {text} or {data: base64}."""
    import csv
    import io
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "")
    if not text and data.get("data"):
        try:
            text = _decode_upload(data).decode("utf-8-sig")
        except (NodeError, UnicodeDecodeError) as e:
            return jsonify({"error": f"unreadable file: {e}"}), 400
    text = text.lstrip("\ufeff")
    if not text.strip():
        return jsonify({"error": "empty file"}), 400
    sample = text[:3000]
    delim = max(";,\t|", key=sample.count) if any(d in sample for d in ";,\t|") else ";"
    done, skipped, errors = 0, 0, []
    for i, cells in enumerate(csv.reader(io.StringIO(text), delimiter=delim), 1):
        if not cells or not str(cells[0]).strip():
            continue
        word = str(cells[0]).strip()
        value = str(cells[1]).strip() if len(cells) > 1 else ""
        if i == 1 and word.lower() in ("parola", "word", "originale", "original"):
            continue                                    # header
        if not script_of(word) or (value and script_of(value)):
            skipped += 1
            if len(errors) < 10:
                errors.append(f"row {i}: {word} -> {value}")
            continue
        store.translit_set(word, value)
        done += 1
    logging.info(f"Dictionary: {done} entries imported, {skipped} discarded")
    return jsonify({"ok": True, "imported": done, "skipped": skipped, "errors": errors})


@bp.route("/api/translit/export")
def api_translit_export():
    """Downloads the whole dictionary as CSV (word;transliteration;source;script;updated);
    the import also reads the Italian header of the versions before 2.0."""
    import csv
    import io
    from flask import Response
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow(["word", "transliteration", "source", "script", "updated"])
    for r in store.translit_rows(limit=200000):
        w.writerow([r["word"], r["value"], r["source"], r["script"], r["updated_at"]])
    data = "\ufeff" + out.getvalue()                  # BOM: Excel opens the UTF-8 correctly
    return Response(data, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=transliterations.csv"})
