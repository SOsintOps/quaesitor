# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Transliteration: romanization of names written in other scripts (ICU or
anyascii), the word dictionary, the proposals of the chatbot and the mode in use."""
# "Nomina si nescis, perit et cognitio rerum." (after Linnaeus, Philosophia Botanica)
# If you do not know the names, the knowledge of things is lost too.
import json
import logging
import re
import time
import unicodedata

import regex as _rx

from . import store
from .core import _hash
from .chatbot import _bot, _bot_down, CHATBOT, chatbot_ask, chatbot_probe, chatbot_ready


# ==================== ROMANIZATION ====================
# "Ambiguous" scripts: abjads without short vowels. No automatic engine can
# return a readable name (محمد = m-h-m-d): the manual dictionaries are needed.
AMBIGUOUS_SCRIPTS = {"ARABIC", "HEBREW", "SYRIAC", "THAANA", "CJK"}   # CJK: ambiguous kanji reading

WORD_RE = _rx.compile(r"[\p{L}\p{M}]+")   # letters + combining marks (Devanagari, Thai, kana with dakuten)

try:                                    # PyICU: better quality, every script
    import icu
    _ICU = icu.Transliterator.createInstance("Any-Latin; Latin-ASCII")
    _romanize_raw = _ICU.transliterate
    TRANSLIT_ENGINE = "icu"
except Exception:                       # pure Python fallback
    try:
        from anyascii import anyascii as _romanize_raw
        TRANSLIT_ENGINE = "anyascii"
    except Exception:
        _romanize_raw = None
        TRANSLIT_ENGINE = None

# recognised non-Western scripts (prefix of the Unicode name of the character)
SCRIPTS = (
    "CYRILLIC", "ARABIC", "GREEK", "HEBREW", "HIRAGANA", "KATAKANA", "HANGUL",
    "THAI", "DEVANAGARI", "ARMENIAN", "GEORGIAN", "BENGALI", "GUJARATI",
    "GURMUKHI", "TAMIL", "TELUGU", "KANNADA", "MALAYALAM", "SINHALA",
    "ETHIOPIC", "KHMER", "LAO", "MYANMAR", "TIBETAN", "SYRIAC", "THAANA",
    "CJK", "IDEOGRAPH", "BOPOMOFO", "MONGOLIAN", "CHEROKEE",
)


def script_of(text):
    """Dominant script of a string, None if it is already Latin/neutral."""
    counts = {}
    letters = 0
    for ch in str(text or ""):
        if not ch.isalpha():
            continue
        letters += 1
        try:
            name = unicodedata.name(ch)
        except ValueError:
            continue
        if name.startswith("LATIN"):
            counts["LATIN"] = counts.get("LATIN", 0) + 1
            continue
        for s in SCRIPTS:
            if name.startswith(s):
                key = "CJK" if s in ("CJK", "IDEOGRAPH") else s
                counts[key] = counts.get(key, 0) + 1
                break
    if not letters:
        return None
    best = max(((k, v) for k, v in counts.items() if k != "LATIN"),
               key=lambda kv: kv[1], default=None)
    if not best or best[1] / letters < 0.3:
        return None
    return best[0]


# ---------- transliteration dictionary ('translit' table in SQLite) ----------
# Each word has a single row: 'manual' (written by hand, always wins),
# 'ai' (proposed by the chatbot) or 'pending' (known but still to be transliterated).
def load_word_dict():
    """{original word: transliteration}; '' = still to be done."""
    return store.translit_dict()


def write_pending(pending):
    """New words, still to be transliterated (by hand or with the AI)."""
    n = store.translit_add_pending(sorted(pending or []), script_of)
    if n:
        logging.info(f"{n} words to transliterate added to the dictionary")
    return n


# ---------- transliteration with the chatbot ----------
# The model's answer is DATA, not a command: only its Latin text is taken
# and everything else is discarded (instructions, explanations, markup).
LATIN_OUT = re.compile(r"^[A-Za-z][A-Za-z0-9 '\-.]{0,79}$")

TRANSLIT_PROMPT = (
    "Transliterate each word into the Latin alphabet.\n"
    "Rules:\n"
    "- Reply with a JSON object only, nothing else.\n"
    "- One key for every input word, written exactly as given.\n"
    "- The value is the usual English romanization of the word "
    "(personal names: e.g. Mohamed, Ali, Al-Sharif).\n"
    "- Plain ASCII letters only: no diacritics, no scholarly marks "
    "(write Muhammad, not Muḥammad; Antani, not ʿAntānī).\n"
    "- Do not translate the meaning, do not add comments or extra keys.\n"
    "Words: {parole}"
)


def _pulisci_translit(valore):
    """Keeps only a plausible transliteration: Latin text, short."""
    v = re.sub(r"\s+", " ", str(valore or "")).strip().strip('"\'')
    v = "".join(c for c in v if c.isprintable())
    if script_of(v):                       # still contains non-Latin characters
        return ""
    # models often use the scholarly transcription (Muḥammad, ʿAntānī):
    # diacritics and marks are stripped instead of discarding the word
    v = _clean(v)
    if not v or not LATIN_OUT.match(v):
        return ""
    if script_of(v):                       # still contains non-Latin characters
        return ""
    return v


def _estrai_json(testo):
    """The first JSON object contained in the answer (models often add
    ``` or a polite sentence)."""
    t = str(testo or "")
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return {}
    try:
        d = json.loads(t[i:j + 1])
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def chatbot_translit(parole):
    """{word: Latin form} for the words the chatbot can transliterate."""
    parole = [p for p in parole if p]
    if not parole or not chatbot_ready():
        return {}
    prompt = TRANSLIT_PROMPT.format(parole=json.dumps(parole, ensure_ascii=False))
    risposta = chatbot_ask(prompt)
    if not risposta:
        return {}
    grezzo = _estrai_json(risposta)
    fuori = {}
    for k, v in grezzo.items():
        if k in parole:                     # only the words asked for
            val = _pulisci_translit(v)
            if val:
                fuori[k] = val
    if not fuori:
        logging.warning("Chatbot: answer without usable transliterations: "
                        + re.sub(r"\s+", " ", risposta)[:200])
    return fuori


def save_ai_translit(nuove):
    """Saves the words transliterated by the chatbot; a hand-made transliteration
    always takes precedence and is not overwritten."""
    try:
        return store.translit_save_ai(nuove, CHATBOT["model"])
    except Exception as e:
        logging.error(f"Cannot save the transliterations: {e}")
        return 0


def _per_ai(w):
    """Should the word go to the AI? With the AI active: any non-Latin script
    (it is more accurate than the local engine); without it, only the ambiguous
    scripts, which end up in the dictionary to be filled in by hand."""
    s = script_of(w)
    return bool(s) and (s in AMBIGUOUS_SCRIPTS or chatbot_ready())


def parole_da_traslitterare(graph=None, wdict=None):
    """All the words still without a transliteration: the empty entries of the
    dictionaries plus the non-Latin words that appear in the labels."""
    wdict = load_word_dict() if wdict is None else wdict
    todo = {w for w, v in wdict.items()
            if not str(v or "").strip() and _per_ai(w)}
    for n in (graph or {}).get("nodes", []):
        if n.get("ntype") == "latin":
            continue
        for lab in [n.get("label")] + list(n.get("aliases") or []):
            for w in WORD_RE.findall(str(lab or "")):
                if _per_ai(w) and not str(wdict.get(w) or "").strip():
                    todo.add(w)
    return sorted(todo)


def ai_fill_translit(todo, budget=None, max_words=None, force=False):
    """Has the chatbot transliterate the words of 'todo', in batches, and saves them.
    Returns the statistics; if the chatbot stays silent, 'translated' is 0, nothing more."""
    stat = {"requested": 0, "translated": 0, "remaining": len(todo), "error": "",
            "saved": 0}
    if not todo or not chatbot_ready():
        stat["error"] = "" if todo else "nothing to transliterate"
        return stat
    if not force and time.time() < _bot["down_until"]:
        stat["error"] = _bot["reason"] or "chatbot not reachable"
        return stat
    if force:
        _bot["down_until"] = 0.0
    vivo, perche = chatbot_probe()             # quick probe, no long waits
    if not vivo:
        _bot_down(perche)
        stat["error"] = perche
        return stat

    limite = max_words or CHATBOT["max_words"]
    scadenza = time.time() + (budget or CHATBOT["budget"])
    lotto = CHATBOT["batch"]
    fatte = {}
    for i in range(0, min(len(todo), limite), lotto):
        if time.time() > scadenza:
            break
        gruppo = todo[i:i + lotto]
        stat["requested"] += len(gruppo)
        got = chatbot_translit(gruppo)
        if not got and _bot["reason"]:
            stat["error"] = _bot["reason"]
            break
        fatte.update(got)
    stat["translated"] = len(fatte)
    stat["saved"] = save_ai_translit(fatte)
    stat["remaining"] = len(todo) - len(fatte)
    if fatte:
        logging.info(f"Chatbot: {len(fatte)} words transliterated "
                     f"({stat['remaining']} still to do)")
    return stat


# ---------- engine ----------
_MOD_CATS = {"Lm", "Sk", "Mn", "Mc"}


def _clean(s):
    """Strips diacritics and modifier letters (ʿ ʾ ̣ ...) left by ICU."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) not in _MOD_CATS)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[`'\"]", "", s)          # ʿayn/hamza rendered by anyascii as ` and '
    return re.sub(r"\s+", " ", s).strip(" -_.")


_auto_cache = {}
_HAN_RE = _rx.compile(r"^\p{Han}+$")


def _is_han(word):
    """Ideograms only (Chinese, or kanji without kana)."""
    return bool(_HAN_RE.match(str(word or "")))


def _auto(word):
    """Automatic transliteration of a single word, with capitalisation."""
    if word in _auto_cache:
        return _auto_cache[word]
    if not _romanize_raw:
        return ""
    try:
        if _is_han(word):
            # Chinese: one syllable per character, separated by spaces ("Zhang Wei",
            # not "ZhangWei"); applies to both engines (ICU and anyascii)
            out = " ".join(_clean(_romanize_raw(ch)) for ch in word)
        else:
            out = _clean(_romanize_raw(word))
    except Exception:
        out = ""
    out = " ".join(p.capitalize() if p.islower() else p for p in out.split())
    _auto_cache[word] = out
    return out


def romanize(text, wdict, pending):
    """(Latin form, script, how many words from the manual/AI dictionary).
    Multi-word strings are split: each word is transliterated on its own,
    so the dictionary can be reused anywhere.
    The dictionary (hand-made or filled in by the AI) always wins over the
    automatic engine, for any script."""
    text = str(text or "")
    scr = script_of(text)
    if not scr:
        return None, None, 0

    parts, manual = [], 0
    for w in WORD_RE.findall(text):
        ws = script_of(w)
        if not ws:
            parts.append(w)                    # already Latin
            continue
        val = wdict.get(w)
        if val and val.strip():
            parts.append(val.strip())          # manual or AI dictionary
            manual += 1
            continue
        if val is None and ws in AMBIGUOUS_SCRIPTS:
            pending.add(w)                     # new word -> into the next file
        auto = _auto(w)                        # automatic fallback (ICU/anyascii)
        if not auto:
            return None, scr, 0                # no engine: no half-done node
        parts.append(auto)
    out = re.sub(r"\s+", " ", " ".join(p for p in parts if p)).strip()
    return (out or None), scr, manual


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"


TRANSLIT_MODES = ("attribute", "nodes")


def translit_mode():
    """'attribute' (default in this fork): the Latin form is an attribute of the
    node ('roman' field: second line of the label, line of the card, search);
    'nodes': as in the original, a twin Latin node linked to the original one.
    Global setting, in the archive (meta)."""
    try:
        m = store.get_gmeta("translit_mode", "attribute")
    except Exception:
        m = "attribute"
    return m if m in TRANSLIT_MODES else "attribute"


def add_translit(graph, only=None, offline=False):
    """Adds a Latin node for every label in a non-Western script, linked to
    the original by a 'translit' edge. Idempotent.

    only    : if given, processes only the nodes with these ids (the others stay
              untouched). Used to transliterate nodes added by hand, which do
              not go through build_graph.
    offline : no chatbot and no file writes (new words not collected). Used
              at every request for the manual nodes: it must be instant and
              free of side effects. In this mode the existing Latin nodes are
              not touched (they may come from the cache); new ones are only
              created and linked."""
    if not _romanize_raw and not offline:
        # carry on anyway: the words already in the dictionary (AI or by hand)
        # still yield their Latin node
        logging.warning("No local transliteration engine: dictionary and AI only")

    wdict = load_word_dict()
    # The chatbot fills in the still-uncovered words by itself. If it does not
    # answer nothing changes: work goes on with the dictionary and the automatic engine.
    if not offline and CHATBOT["auto"] and chatbot_ready():
        todo = parole_da_traslitterare(graph, wdict)
        if todo:
            ai_fill_translit(todo)
            wdict = load_word_dict()
    pending = set()
    existing = {n["id"]: n for n in graph["nodes"]}
    edge_keys = {e["id"] for e in graph["edges"]}
    added = 0
    mode = translit_mode()

    for n in list(graph["nodes"]):
        if n.get("ntype") == "latin":
            continue
        if only is not None and n["id"] not in only:
            continue
        labels = [n.get("label")] + list(n.get("aliases") or [])
        rom, scr, manual = romanize(labels[0], wdict, pending)
        for extra in labels[1:]:               # aliases feed the dictionary too
            romanize(extra, wdict, pending)
        if not rom:
            continue

        n["roman"] = rom
        n["script"] = scr
        n["roman_manual"] = manual

        if slug(rom) == slug(n.get("label")):
            continue
        if mode == "attribute":                # no twin node: 'roman' is enough
            continue

        lid = "latin:" + slug(rom)
        if lid not in existing:
            existing[lid] = {
                "id": lid, "label": rom, "ntype": "latin", "platform": "latin",
                "image": None,
                "sources": ["translit:" + ("dizionario" if manual else TRANSLIT_ENGINE or "")],
                "records": [], "aliases": [], "alias_ids": [], "merged": 1,
                "cards": 0, "script": scr, "manual": bool(manual),
            }
            graph["nodes"].append(existing[lid])
            added += 1
        elif not offline:                      # do not mutate Latin nodes already cached
            al = existing[lid].setdefault("aliases", [])
            if n.get("label") and n["label"] not in al:
                al.append(n["label"])

        key = "-".join(sorted([_hash(lid), _hash(n["id"])]))
        if key not in edge_keys:
            edge_keys.add(key)
            graph["edges"].append({"id": key, "source": lid,
                                   "target": n["id"], "rel": "translit"})

    if not offline:
        write_pending(pending)
        done = sum(1 for v in wdict.values() if v.strip())
        logging.info(f"Transliteration ({TRANSLIT_ENGINE}): {added} Latin nodes · "
                     f"dictionary {done}/{len(wdict)} words filled in · "
                     f"{len(pending)} new")
    return graph
