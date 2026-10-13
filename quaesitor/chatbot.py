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


# ==================== CHATBOT REMOTO (AI) ====================
# Chatbot dell'utente (Ollama dietro un reverse proxy). Serve a compilare da
# solo il dizionario di traslitterazione: le scritture senza vocali brevi
# (arabo, ebraico...) non sono traducibili da un motore automatico.
# REGOLA: se il chatbot non risponde NON succede nulla. Si prosegue con il
# dizionario compilato a mano e la traslitterazione automatica di sempre.
CHATBOT_CONF = os.path.join(BASE_DIR, "chatbot.conf")
CHATBOT_DEFAULTS = {
    "enabled": "true", "endpoint": "", "api_key": "", "model": "gemma3:12b",
    "timeout": "25", "auth_header": "Authorization", "auth_prefix": "Bearer",
    "api": "auto", "auto": "true", "max_words": "120", "batch": "15",
    "budget": "60",
}


def _load_chatbot_conf():
    """chatbot.conf (chiave = valore) + variabili d'ambiente CHATBOT_*."""
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
    # Un solo interruttore: 'enabled' (lo switch "AI attiva" dell'app). Spento
    # = il chatbot non viene mai contattato, per nessuna funzione.
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

# stato in memoria: quale formato di API funziona e da quando il chatbot e'
# considerato irraggiungibile (per non riprovare a ogni ricostruzione)
BOT_RETRY_AFTER = 300              # secondi di attesa dopo un tentativo fallito
_bot = {"api": None, "down_until": 0.0, "reason": "", "ok_at": 0.0}


def chatbot_ready():
    """Il chatbot si puo' usare: interruttore acceso ed endpoint impostato.
    Da spento non si tenta nessun collegamento."""
    return bool(CHATBOT["enabled"] and CHATBOT["endpoint"])


def _bot_call(path, payload):
    """POST JSON al chatbot. Ritorna (dati, errore): uno dei due e' sempre None."""
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
AI_NUM_CTX = 8192                      # finestra di contesto chiesta a Ollama (token)                      # come il CONNECTTIMEOUT del client PHP


def chatbot_probe():
    """Colpo di sonda veloce: il SERVER risponde? Serve solo a non far
    aspettare il timeout pieno quando la macchina e' spenta o irraggiungibile.
    Un 401 NON conta come guasto: il proxy puo' proteggere /api/tags e lasciare
    passare /api/generate, che e' la rotta che ci interessa davvero.
    Ritorna (raggiungibile, motivo)."""
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
        return True, ""                    # ha risposto: si prova la generazione
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
    """Manda un prompt al chatbot. Ritorna il testo, oppure None se il chatbot
    non risponde: in quel caso il chiamante DEVE proseguire senza.
    ignore_switch=True (prova di collegamento dal pannello): basta l'endpoint.
    json_mode: chiede a Ollama una risposta in JSON valido."""
    if ignore_switch:
        if not CHATBOT["endpoint"]:
            return None
    elif not chatbot_ready():
        return None
    if not force and time.time() < _bot["down_until"]:
        return None

    forme = ["ollama", "openai"] if CHATBOT["api"] == "auto" else [CHATBOT["api"]]
    if _bot["api"] in forme:                     # quella che ha gia' funzionato
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
            # num_ctx: il prompt dei nodi (con gli elenchi di armi, sostanze,
            # reati...) supera la finestra predefinita di Ollama (2-4k token), che
            # altrimenti lo troncherebbe in silenzio
            req = {"model": CHATBOT["model"], "prompt": prompt, "stream": False,
                   "options": {"temperature": 0, "num_ctx": AI_NUM_CTX}}
            if json_mode:
                req["format"] = "json"
            dati, err = _bot_call("/api/generate", req)
            testo = (dati or {}).get("response") or ""
        if err:
            ultimo = err
            if err.startswith(("HTTP 401", "HTTP 403")):
                break                            # la chiave e' sbagliata: inutile insistere
            if not err.startswith("HTTP"):
                break                            # server irraggiungibile: vale per ogni formato
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
