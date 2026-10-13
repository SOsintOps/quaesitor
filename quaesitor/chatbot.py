# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""The remote chatbot (AI): its settings file, the calls and the probe of the service."""
# "Dum loquimur, fugerit invida aetas." (Horace, Odes I)
# While we speak, envious time will have fled.
import json
import logging
import os
import time
import urllib.error

from .paths import BASE_DIR


# ==================== REMOTE CHATBOT (AI) ====================
# The user's chatbot (Ollama behind a reverse proxy). It fills in the
# transliteration dictionary by itself: scripts without short vowels
# (Arabic, Hebrew...) cannot be rendered by an automatic engine.
# RULE: if the chatbot does not answer, NOTHING happens. Work goes on with the
# hand-filled dictionary and the usual automatic transliteration.
CHATBOT_CONF = os.path.join(BASE_DIR, "chatbot.conf")
CHATBOT_DEFAULTS = {
    "enabled": "true", "endpoint": "", "api_key": "", "model": "gemma3:12b",
    "timeout": "25", "auth_header": "Authorization", "auth_prefix": "Bearer",
    "api": "auto", "auto": "true", "max_words": "120", "batch": "15",
    "budget": "60",
}


def _load_chatbot_conf():
    """chatbot.conf (key = value) + CHATBOT_* environment variables."""
    conf = dict(CHATBOT_DEFAULTS)
    try:
        with open(CHATBOT_CONF, "r", encoding="utf-8-sig") as f:
            for riga in f:
                riga = riga.strip()
                if not riga or riga.startswith("#"):
                    continue
                k, sep, v = riga.partition("=")
                if sep:
                    conf[k.strip().lower()] = v.strip()
    except FileNotFoundError:
        pass
    except Exception as e:
        logging.error(f"chatbot.conf illeggibile: {e}")
    for k in list(conf):
        env = os.environ.get("CHATBOT_" + k.upper())
        if env is not None:
            conf[k] = env
    # A single switch: 'enabled' (the app's "AI active" toggle). Off
    # = the chatbot is never contacted, for any feature.
    conf["endpoint"] = conf["endpoint"].rstrip("/")
    for k, minimo in (("timeout", 1), ("max_words", 1), ("batch", 1), ("budget", 5)):
        try:
            conf[k] = max(minimo, int(float(conf[k])))
        except (TypeError, ValueError):
            conf[k] = int(CHATBOT_DEFAULTS[k])
    for k in ("enabled", "auto"):
        conf[k] = str(conf[k]).strip().lower() in ("1", "true", "si", "yes", "on")
    return conf


CHATBOT = _load_chatbot_conf()

# in-memory state: which API format works and since when the chatbot is
# considered unreachable (so as not to retry at every rebuild)
BOT_RETRY_AFTER = 300              # seconds to wait after a failed attempt
_bot = {"api": None, "down_until": 0.0, "reason": "", "ok_at": 0.0}


def chatbot_ready():
    """The chatbot can be used: switch on and endpoint set.
    When off, no connection is attempted."""
    return bool(CHATBOT["enabled"] and CHATBOT["endpoint"])


def _bot_call(path, payload):
    """POST JSON to the chatbot. Returns (data, error): one of the two is always None."""
    url = CHATBOT["endpoint"] + path
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    testa = (CHATBOT["auth_header"] or "").strip()
    if testa and CHATBOT["api_key"]:
        pre = (CHATBOT["auth_prefix"] or "").strip()
        req.add_header(testa, (pre + " " if pre else "") + CHATBOT["api_key"])
    try:
        with urllib.request.urlopen(req, timeout=CHATBOT["timeout"]) as r:
            return json.loads(r.read().decode("utf-8", "replace")), None
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace").strip()[:120]
        except Exception:
            pass
        return None, f"HTTP {e.code} {e.reason}" + (f" - {detail}" if detail else "")
    except urllib.error.URLError as e:
        return None, f"{e.reason}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


PROBE_TIMEOUT = 5
AI_NUM_CTX = 8192                      # context window requested from Ollama (tokens)                      # like the CONNECTTIMEOUT of the PHP client


def chatbot_probe():
    """Quick probe: does the SERVER answer? It only avoids waiting for the
    full timeout when the machine is off or unreachable.
    A 401 does NOT count as a failure: the proxy may protect /api/tags and let
    /api/generate through, which is the route that really matters.
    Returns (reachable, reason)."""
    url = CHATBOT["endpoint"] + "/api/tags"
    req = urllib.request.Request(url, method="GET")
    testa = (CHATBOT["auth_header"] or "").strip()
    if testa and CHATBOT["api_key"]:
        pre = (CHATBOT["auth_prefix"] or "").strip()
        req.add_header(testa, (pre + " " if pre else "") + CHATBOT["api_key"])
    try:
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as r:
            r.read(1)
            return True, ""
    except urllib.error.HTTPError:
        return True, ""                    # it answered: try the generation
    except urllib.error.URLError as e:
        return False, f"{e.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _bot_down(motivo):
    _bot["down_until"] = time.time() + BOT_RETRY_AFTER
    _bot["reason"] = motivo
    logging.warning(f"Chatbot non raggiungibile ({motivo}): "
                    f"si prosegue senza, riprovo fra {BOT_RETRY_AFTER}s")


def chatbot_ask(prompt, force=False, json_mode=False, ignore_switch=False):
    """Sends a prompt to the chatbot. Returns the text, or None if the chatbot
    does not answer: in that case the caller MUST carry on without it.
    ignore_switch=True (connection test from the panel): the endpoint is enough.
    json_mode: asks Ollama for an answer in valid JSON."""
    if ignore_switch:
        if not CHATBOT["endpoint"]:
            return None
    elif not chatbot_ready():
        return None
    if not force and time.time() < _bot["down_until"]:
        return None

    forme = ["ollama", "openai"] if CHATBOT["api"] == "auto" else [CHATBOT["api"]]
    if _bot["api"] in forme:                     # the one that already worked
        forme = [_bot["api"]]
    ultimo = ""
    for forma in forme:
        if forma == "openai":
            dati, err = _bot_call("/v1/chat/completions", {
                "model": CHATBOT["model"], "temperature": 0, "stream": False,
                "messages": [{"role": "user", "content": prompt}]})
            testo = ""
            if dati:
                try:
                    testo = dati["choices"][0]["message"]["content"]
                except Exception:
                    testo = ""
        else:
            # num_ctx: the node prompt (with the lists of weapons, substances,
            # offences...) exceeds Ollama's default window (2-4k tokens), which
            # would otherwise truncate it silently
            req = {"model": CHATBOT["model"], "prompt": prompt, "stream": False,
                   "options": {"temperature": 0, "num_ctx": AI_NUM_CTX}}
            if json_mode:
                req["format"] = "json"
            dati, err = _bot_call("/api/generate", req)
            testo = (dati or {}).get("response") or ""
        if err:
            ultimo = err
            if err.startswith(("HTTP 401", "HTTP 403")):
                break                            # wrong key: no point insisting
            if not err.startswith("HTTP"):
                break                            # server unreachable: applies to every format
            continue
        if testo:
            _bot["api"] = forma
            _bot["down_until"] = 0.0
            _bot["reason"] = ""
            _bot["ok_at"] = time.time()
            return testo
        ultimo = "risposta vuota"
    _bot_down(ultimo or "nessuna risposta")
    return None
