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
    """Quante parole restano da traslitterare e se il chatbot e' utilizzabile."""
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
    """Dove va la forma latina: 'attribute' (nel nodo) o 'nodes' (gemelli)."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        mode = str(data.get("mode") or "").strip()
        if mode not in TRANSLIT_MODES:
            return jsonify({"error": "modalita' non valida"}), 400
        store.set_gmeta("translit_mode", mode)
        _cache["key"] = None                   # il grafo va ricostruito
        logging.info(f"Traslitterazione: modalita' {mode}")
    return jsonify({"ok": True, "mode": translit_mode()})


@bp.route("/api/translit/ai", methods=["POST"])
def api_translit_ai():
    """Fa traslitterare al chatbot tutte le parole ancora scoperte.
    Se il chatbot non risponde lo dice e non cambia niente."""
    if not chatbot_ready():
        return jsonify({"error": "AI disattivata o endpoint non impostato "
                                 "(pannello Intelligenza artificiale)"}), 400
    wdict = load_word_dict()
    todo = parole_da_traslitterare(current_graph(), wdict)
    if not todo:
        return jsonify({"ok": True, "tradotte": 0, "restano": 0, "errore": ""})
    stat = ai_fill_translit(todo, force=True,
                            budget=max(CHATBOT["budget"], 120),
                            max_words=max(CHATBOT["max_words"], len(todo)))
    if not stat["tradotte"] and stat["errore"]:
        return jsonify({"error": stat["errore"]}), 502
    if stat["tradotte"]:
        _cache["key"] = None                  # le etichette latine vanno rifatte
    stat["ok"] = True
    return jsonify(stat)


# ==================== DIZIONARIO DI TRASLITTERAZIONE (a mano) ====================
# La finestra "Dizionario" del pannello: elenco delle parole non latine viste
# nel grafo (in sospeso, tradotte a mano, tradotte dall'AI), modifica in riga,
# import/export CSV. Un valore scritto a mano vince sempre sul motore
# automatico e sull'AI (store.translit_set); vuoto = torna "da tradurre".
# Ogni modifica incrementa translit_version: il grafo si ricostruisce da solo.

@bp.route("/api/translit/words")
def api_translit_words():
    """Pagina del dizionario. Parametri: q (filtro su parola o valore),
    source (pending | manual | ai | vuoto = tutte), limit, offset."""
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
        # proposta del motore automatico, mostrata come suggerimento
        r["auto"] = _auto(r["word"]) if not str(r.get("value") or "").strip() else ""
    return jsonify({"rows": rows, "more": more, "offset": offset,
                    "counts": store.translit_counts(),
                    "engine": TRANSLIT_ENGINE or ""})


@bp.route("/api/translit/set", methods=["POST"])
def api_translit_set():
    """Scrive (o svuota) la traslitterazione di una parola: {word, value}."""
    data = request.get_json(silent=True) or {}
    word = re.sub(r"\s+", " ", str(data.get("word") or "")).strip()[:120]
    value = re.sub(r"\s+", " ", str(data.get("value") or "")).strip()[:120]
    if not word:
        return jsonify({"error": "parola mancante"}), 400
    if not script_of(word):
        return jsonify({"error": "la parola e' gia' in caratteri latini"}), 400
    if value and script_of(value):
        return jsonify({"error": "la traslitterazione deve essere in caratteri latini"}), 400
    store.translit_set(word, value)
    logging.info(f"Dizionario: {word!r} -> {value!r}" if value else f"Dizionario: {word!r} da tradurre")
    return jsonify({"ok": True, "word": word, "value": value,
                    "source": "manual" if value else "pending"})


@bp.route("/api/translit/delete", methods=["POST"])
def api_translit_delete():
    """Toglie la parola dal dizionario: tornera' in sospeso se ricompare."""
    data = request.get_json(silent=True) or {}
    word = str(data.get("word") or "").strip()
    if not word:
        return jsonify({"error": "parola mancante"}), 400
    n = store.translit_delete(word)
    return jsonify({"ok": True, "deleted": n})


@bp.route("/api/translit/collect", methods=["POST"])
def api_translit_collect():
    """Mette in sospeso TUTTE le parole non latine presenti nel grafo (non solo
    quelle delle scritture ambigue), cosi' si possono correggere a mano anche
    le romanizzazioni automatiche (cinese, cirillico...)."""
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
    """Importa un CSV 'parola;traslitterazione' (anche , o tab; con o senza
    intestazione). Le righe diventano voci MANUALI; una riga con il valore
    vuoto rimette la parola in sospeso. Corpo: {text} oppure {data: base64}."""
    import csv
    import io
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "")
    if not text and data.get("data"):
        try:
            text = _decode_upload(data).decode("utf-8-sig")
        except (NodeError, UnicodeDecodeError) as e:
            return jsonify({"error": f"file illeggibile: {e}"}), 400
    text = text.lstrip("\ufeff")
    if not text.strip():
        return jsonify({"error": "file vuoto"}), 400
    sample = text[:3000]
    delim = max(";,\t|", key=sample.count) if any(d in sample for d in ";,\t|") else ";"
    done, skipped, errors = 0, 0, []
    for i, cells in enumerate(csv.reader(io.StringIO(text), delimiter=delim), 1):
        if not cells or not str(cells[0]).strip():
            continue
        word = str(cells[0]).strip()
        value = str(cells[1]).strip() if len(cells) > 1 else ""
        if i == 1 and word.lower() in ("parola", "word", "originale", "original"):
            continue                                    # intestazione
        if not script_of(word) or (value and script_of(value)):
            skipped += 1
            if len(errors) < 10:
                errors.append(f"riga {i}: {word} -> {value}")
            continue
        store.translit_set(word, value)
        done += 1
    logging.info(f"Dizionario: importate {done} voci, {skipped} scartate")
    return jsonify({"ok": True, "imported": done, "skipped": skipped, "errors": errors})


@bp.route("/api/translit/export")
def api_translit_export():
    """Scarica tutto il dizionario come CSV (parola;traslitterazione;origine;scrittura)."""
    import csv
    import io
    from flask import Response
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow(["parola", "traslitterazione", "origine", "scrittura", "aggiornata"])
    for r in store.translit_rows(limit=200000):
        w.writerow([r["word"], r["value"], r["source"], r["script"], r["updated_at"]])
    data = "\ufeff" + out.getvalue()                  # BOM: Excel apre l'UTF-8 correttamente
    return Response(data, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=traslitterazioni.csv"})
