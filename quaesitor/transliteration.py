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


# ==================== ROMANIZZAZIONE ====================
# Scritture "ambigue": abjad senza vocali brevi. Nessun motore automatico può
# restituire un nome leggibile (محمد = m-h-m-d), servono i dizionari manuali.
AMBIGUOUS_SCRIPTS = {"ARABIC", "HEBREW", "SYRIAC", "THAANA", "CJK"}   # CJK: lettura dei kanji ambigua

WORD_RE = _rx.compile(r"[\p{L}\p{M}]+")   # lettere + segni combinanti (devanagari, thai, kana con dakuten)

try:                                    # PyICU: qualità migliore, tutti gli alfabeti
    import icu
    _ICU = icu.Transliterator.createInstance("Any-Latin; Latin-ASCII")
    _romanize_raw = _ICU.transliterate
    TRANSLIT_ENGINE = "icu"
except Exception:                       # fallback puro Python
    try:
        from anyascii import anyascii as _romanize_raw
        TRANSLIT_ENGINE = "anyascii"
    except Exception:
        _romanize_raw = None
        TRANSLIT_ENGINE = None

# alfabeti non occidentali riconosciuti (prefisso del nome Unicode del carattere)
SCRIPTS = (
    "CYRILLIC", "ARABIC", "GREEK", "HEBREW", "HIRAGANA", "KATAKANA", "HANGUL",
    "THAI", "DEVANAGARI", "ARMENIAN", "GEORGIAN", "BENGALI", "GUJARATI",
    "GURMUKHI", "TAMIL", "TELUGU", "KANNADA", "MALAYALAM", "SINHALA",
    "ETHIOPIC", "KHMER", "LAO", "MYANMAR", "TIBETAN", "SYRIAC", "THAANA",
    "CJK", "IDEOGRAPH", "BOPOMOFO", "MONGOLIAN", "CHEROKEE",
)


def script_of(text):
    """Alfabeto dominante di una stringa, None se è già latina/neutra."""
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


# ---------- dizionario di traslitterazione (tabella 'translit' di SQLite) ----------
# Ogni parola ha una sola riga: 'manual' (scritta a mano, vince sempre),
# 'ai' (proposta dal chatbot) o 'pending' (nota ma ancora da tradurre).
def load_word_dict():
    """{parola originale: traslitterazione}; '' = da tradurre."""
    return store.translit_dict()


def write_pending(pending):
    """Parole nuove, da tradurre (a mano o con l'AI)."""
    n = store.translit_add_pending(sorted(pending or []), script_of)
    if n:
        logging.info(f"{n} parole da traslitterare aggiunte al dizionario")
    return n


# ---------- traslitterazione con il chatbot ----------
# La risposta del modello e' un DATO, non un comando: se ne prende solo il
# testo latino e si scarta tutto il resto (istruzioni, spiegazioni, markup).
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
    """Tiene solo una traslitterazione plausibile: testo latino, breve."""
    v = re.sub(r"\s+", " ", str(valore or "")).strip().strip('"\'')
    v = "".join(c for c in v if c.isprintable())
    if script_of(v):                       # contiene ancora caratteri non latini
        return ""
    # i modelli usano spesso la trascrizione accademica (Muḥammad, ʿAntānī):
    # si tolgono diacritici e segni invece di scartare la parola
    v = _clean(v)
    if not v or not LATIN_OUT.match(v):
        return ""
    if script_of(v):                       # contiene ancora caratteri non latini
        return ""
    return v


def _estrai_json(testo):
    """Il primo oggetto JSON contenuto nella risposta (i modelli aggiungono
    spesso ``` o una frase di cortesia)."""
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
    """{parola: forma latina} per le parole che il chatbot sa tradurre."""
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
        if k in parole:                     # solo le parole chieste
            val = _pulisci_translit(v)
            if val:
                fuori[k] = val
    if not fuori:
        logging.warning("Chatbot: risposta senza traslitterazioni utilizzabili: "
                        + re.sub(r"\s+", " ", risposta)[:200])
    return fuori


def save_ai_translit(nuove):
    """Salva le parole tradotte dal chatbot; una traduzione fatta a mano
    ha sempre la precedenza e non viene sovrascritta."""
    try:
        return store.translit_save_ai(nuove, CHATBOT["model"])
    except Exception as e:
        logging.error(f"Impossibile salvare le traslitterazioni: {e}")
        return 0


def _per_ai(w):
    """La parola va fatta tradurre all'AI? Con l'AI attiva: qualunque alfabeto
    non latino (e' piu' precisa del motore locale); senza, solo le scritture
    ambigue, che finiscono nel dizionario da compilare a mano."""
    s = script_of(w)
    return bool(s) and (s in AMBIGUOUS_SCRIPTS or chatbot_ready())


def parole_da_traslitterare(graph=None, wdict=None):
    """Tutte le parole ancora senza traslitterazione: le voci vuote dei
    dizionari piu' le parole non latine che compaiono nelle etichette."""
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
    """Fa tradurre al chatbot le parole di 'todo', a gruppi, e le salva.
    Ritorna le statistiche; se il chatbot tace, 'tradotte' e' 0 e basta."""
    stat = {"chieste": 0, "tradotte": 0, "restano": len(todo), "errore": "",
            "salvate": 0}
    if not todo or not chatbot_ready():
        stat["errore"] = "" if todo else "niente da tradurre"
        return stat
    if not force and time.time() < _bot["down_until"]:
        stat["errore"] = _bot["reason"] or "chatbot non raggiungibile"
        return stat
    if force:
        _bot["down_until"] = 0.0
    vivo, perche = chatbot_probe()             # sonda veloce, niente attese lunghe
    if not vivo:
        _bot_down(perche)
        stat["errore"] = perche
        return stat

    limite = max_words or CHATBOT["max_words"]
    scadenza = time.time() + (budget or CHATBOT["budget"])
    lotto = CHATBOT["batch"]
    fatte = {}
    for i in range(0, min(len(todo), limite), lotto):
        if time.time() > scadenza:
            break
        gruppo = todo[i:i + lotto]
        stat["chieste"] += len(gruppo)
        got = chatbot_translit(gruppo)
        if not got and _bot["reason"]:
            stat["errore"] = _bot["reason"]
            break
        fatte.update(got)
    stat["tradotte"] = len(fatte)
    stat["salvate"] = save_ai_translit(fatte)
    stat["restano"] = len(todo) - len(fatte)
    if fatte:
        logging.info(f"Chatbot: {len(fatte)} parole traslitterate "
                     f"({stat['restano']} ancora da fare)")
    return stat


# ---------- motore ----------
_MOD_CATS = {"Lm", "Sk", "Mn", "Mc"}


def _clean(s):
    """Toglie diacritici e lettere modificatrici (ʿ ʾ ̣ ...) lasciate da ICU."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) not in _MOD_CATS)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[`'\"]", "", s)          # ʿayn/hamza resi da anyascii come ` e '
    return re.sub(r"\s+", " ", s).strip(" -_.")


_auto_cache = {}
_HAN_RE = _rx.compile(r"^\p{Han}+$")


def _is_han(word):
    """Solo ideogrammi (cinese, o kanji senza kana)."""
    return bool(_HAN_RE.match(str(word or "")))


def _auto(word):
    """Traslitterazione automatica di una singola parola, con capitalizzazione."""
    if word in _auto_cache:
        return _auto_cache[word]
    if not _romanize_raw:
        return ""
    try:
        if _is_han(word):
            # cinese: una sillaba per carattere, separate da spazi ("Zhang Wei",
            # non "ZhangWei"); vale per entrambi i motori (ICU e anyascii)
            out = " ".join(_clean(_romanize_raw(ch)) for ch in word)
        else:
            out = _clean(_romanize_raw(word))
    except Exception:
        out = ""
    out = " ".join(p.capitalize() if p.islower() else p for p in out.split())
    _auto_cache[word] = out
    return out


def romanize(text, wdict, pending):
    """(forma latina, alfabeto, quante parole dal dizionario manuale/AI).
    Le stringhe multi-parola vengono spezzate: ogni parola è tradotta
    singolarmente, così il dizionario è riutilizzabile ovunque.
    Il dizionario (a mano o compilato dall'AI) vince sempre sul motore
    automatico, per qualunque alfabeto."""
    text = str(text or "")
    scr = script_of(text)
    if not scr:
        return None, None, 0

    parts, manual = [], 0
    for w in WORD_RE.findall(text):
        ws = script_of(w)
        if not ws:
            parts.append(w)                    # già latina
            continue
        val = wdict.get(w)
        if val and val.strip():
            parts.append(val.strip())          # dizionario manuale o AI
            manual += 1
            continue
        if val is None and ws in AMBIGUOUS_SCRIPTS:
            pending.add(w)                     # parola nuova -> nel prossimo file
        auto = _auto(w)                        # ripiego automatico (ICU/anyascii)
        if not auto:
            return None, scr, 0                # nessun motore: niente nodo a metà
        parts.append(auto)
    out = re.sub(r"\s+", " ", " ".join(p for p in parts if p)).strip()
    return (out or None), scr, manual


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"


TRANSLIT_MODES = ("attribute", "nodes")


def translit_mode():
    """'attribute' (predefinito in questo fork): la forma latina e' un attributo
    del nodo (campo 'roman': seconda riga dell'etichetta, riga della scheda,
    ricerca); 'nodes': come nell'originale, un nodo latino gemello collegato
    all'originale. Impostazione globale, nell'archivio (meta)."""
    try:
        m = store.get_gmeta("translit_mode", "attribute")
    except Exception:
        m = "attribute"
    return m if m in TRANSLIT_MODES else "attribute"


def add_translit(graph, only=None, offline=False):
    """Aggiunge un nodo latino per ogni etichetta in alfabeto non occidentale,
    collegato all'originale con un arco 'translit'. Idempotente.

    only    : se dato, elabora solo i nodi con questi id (gli altri restano
              intatti). Serve per traslitterare i nodi aggiunti a mano, che non
              passano da build_graph.
    offline : niente chatbot e niente scrittura di file (nuove parole non
              raccolte). Usato a ogni richiesta per i nodi manuali: dev'essere
              istantaneo e senza effetti collaterali. In questa modalita' non
              si toccano i nodi latini gia' esistenti (potrebbero venire dalla
              cache), ci si limita a crearne di nuovi e a collegarli."""
    if not _romanize_raw and not offline:
        # si prosegue lo stesso: le parole gia' nel dizionario (AI o a mano)
        # danno comunque il loro nodo latino
        logging.warning("Nessun motore di traslitterazione locale: solo dizionario/AI")

    wdict = load_word_dict()
    # Il chatbot compila da solo le parole ancora scoperte. Se non risponde
    # non cambia nulla: si prosegue con il dizionario e il motore automatico.
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
        for extra in labels[1:]:               # anche gli alias alimentano il dizionario
            romanize(extra, wdict, pending)
        if not rom:
            continue

        n["roman"] = rom
        n["script"] = scr
        n["roman_manual"] = manual

        if slug(rom) == slug(n.get("label")):
            continue
        if mode == "attribute":                # niente nodo gemello: basta 'roman'
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
        elif not offline:                      # non mutare i latini gia' in cache
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
        logging.info(f"Traslitterazione ({TRANSLIT_ENGINE}): {added} nodi latini · "
                     f"dizionario {done}/{len(wdict)} parole compilate · "
                     f"{len(pending)} nuove")
    return graph
