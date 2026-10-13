# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""What every part of the program shares: the folders, the settings files, the
constants of the graph and the shared state. The routes live in blueprints/, the
rest of the shared code in the modules next to this one."""
# "Divide et impera." (traditional maxim)
# Divide and rule.
import hashlib
import json
import logging
import os
import re
import threading as _threading
import urllib.error

from . import ontology as onto
from .paths import BASE_DIR


logging.basicConfig(level=logging.INFO)

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))

IMG_KEYS = ("pic", "photo", "avatar", "image", "img")
IMG_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif)(\?|$)", re.I)
PHOTO_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff")
# sottocartella di DATA_DIR con le immagini caricate a mano: non è un target
MEDIA_DIRNAME = "media"
URL_RE = re.compile(r"^https?://", re.I)

PLATFORM_TABLE = {
    "instagram": "instagram", "threads": "threads", "snapchat": "snapchat",
    "facebook": "facebook", "google": "google", "discord": "discord",
    "microsoft": "microsoft", "apple": "apple", "amazon": "amazon",
    "tiktok": "tiktok", "linkedin": "linkedin", "github": "github",
    "vkontakte": "vk", "airbnb": "airbnb", "zynga": "zynga", "yahoo": "yahoo",
    "telegram": "telegram", "whatsapp": "whatsapp", "spotify": "spotify",
    "x": "x", "twitter": "x", "fotostrana": "generic",
    "people data labs": "generic", "cuitonline": "generic",
    "naz.api": "breach", "domain whois history": "domain",
}
PHONE_SRC = {"callapp", "showcaller", "hlrlookup", "callerid", "truecaller"}
def _hash(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:12]


def _flat(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


class NodeError(ValueError):
    """Valore non valido per il tipo di nodo richiesto (messaggio per l'utente)."""


def _json_obj(v):
    if isinstance(v, dict):
        return v
    try:
        d = json.loads(v) if v else {}
        return d if isinstance(d, dict) else {}
    except (TypeError, ValueError):
        return {}


def _truthy(v):
    return v is True or str(v or "").strip().lower() in ("1", "true", "si", "sì", "yes", "on", "x")


def _decode_upload(data):
    import base64
    raw = str(data.get("data") or "")
    m = re.match(r"^data:[^;,]*(;base64)?,(.*)$", raw, re.S)
    try:
        blob = base64.b64decode(m.group(2)) if m else base64.b64decode(raw)
    except Exception:
        raise NodeError("file illeggibile")
    if len(blob) > 20 * 1024 * 1024:
        raise NodeError("file troppo grande (max 20 MB)")
    return blob


# ================= IMPORTAZIONE DI JSON DA APP TERZE (export OSINT) =================
# Il file si aggancia a un nodo (di norma il target): i record diventano nodi e
# collegamenti con le stesse regole di sempre (build_graph). Il contenuto sta
# nel database, nessun file o cartella su disco.
IMPORT_MAX_MB = 25


# ======================= IMPORTAZIONE FOLLOW THE MONEY =======================
# File di entita' FtM anche grandi (dataset interi): niente anteprima riga per
# riga, ma conteggi per schema (ispezione), filtri, e importazione in un thread
# a lotti con avanzamento. Gli id FtM finiscono nella tabella ftm_ids del caso:
# un re-import aggiorna i nodi invece di duplicarli.
FTM_MAX_MB = 200
FTM_BATCH = 2000


def _ftm_blob(data):
    blob = _decode_upload(data)
    if len(blob) > FTM_MAX_MB * 1024 * 1024:
        raise NodeError(f"file troppo grande (max {FTM_MAX_MB} MB)")
    return blob


# ======================= OPENSANCTIONS (ricerca online) =======================
# Ricerca di persone e societa' su OpenSanctions (API yente: api.opensanctions.org
# con chiave, oppure un'istanza propria) e importazione delle corrispondenze
# come entita' Follow the Money, con le relazioni annidate.
# E' l'UNICA funzione, insieme all'AI, che manda dati fuori dal computer:
# spenta per impostazione predefinita (services.conf), e i nomi cercati sono
# gli unici dati inviati.
SERVICES_CONF = os.path.join(BASE_DIR, "services.conf")
SERVICES_DEFAULTS = {
    "opensanctions_enabled": "false",
    "opensanctions_endpoint": "https://api.opensanctions.org",
    "opensanctions_api_key": "",
    "opensanctions_dataset": "default",
    "opensanctions_timeout": "20",
    "epieos_enabled": "false",
    "epieos_endpoint": "https://api.epieos.com",
    "epieos_api_key": "",
    "epieos_pack": "osinter",
    "epieos_timeout": "120",
}


def _load_kv_conf(path, defaults, env_prefix):
    """File 'chiave = valore' (commenti con #) + variabili d'ambiente."""
    conf = dict(defaults)
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
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
        logging.error(f"{os.path.basename(path)} illeggibile: {e}")
    for k in list(conf):
        env = os.environ.get(env_prefix + k.upper())
        if env is not None:
            conf[k] = env
    return conf


def _save_kv_conf(path, updates, header):
    """Aggiorna un file 'chiave = valore' conservando commenti e ordine."""
    eol = "\n"
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            testo = f.read()
        if "\r\n" in testo:
            eol = "\r\n"
        lines = testo.splitlines()
    except FileNotFoundError:
        lines = [header]
    todo = dict(updates)
    for i, riga in enumerate(lines):
        s = riga.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k = s.partition("=")[0].strip().lower()
        if k in todo:
            lines[i] = f"{k} = {todo.pop(k)}"
    for k, v in todo.items():
        lines.append(f"{k} = {v}")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(eol.join(lines) + eol)


def _load_services_conf():
    conf = _load_kv_conf(SERVICES_CONF, SERVICES_DEFAULTS, "SERVICES_")
    conf["opensanctions_enabled"] = str(conf["opensanctions_enabled"]).strip().lower() in ("1", "true", "si", "yes", "on")
    conf["opensanctions_endpoint"] = str(conf["opensanctions_endpoint"]).strip().rstrip("/")
    try:
        conf["opensanctions_timeout"] = max(3, min(120, int(float(conf["opensanctions_timeout"]))))
    except (TypeError, ValueError):
        conf["opensanctions_timeout"] = 20
    conf["opensanctions_dataset"] = re.sub(r"[^a-z0-9_\-]", "", str(conf["opensanctions_dataset"]).lower()) or "default"
    conf["epieos_enabled"] = str(conf["epieos_enabled"]).strip().lower() in ("1", "true", "si", "yes", "on")
    conf["epieos_endpoint"] = str(conf["epieos_endpoint"]).strip().rstrip("/")
    try:
        conf["epieos_timeout"] = max(10, min(300, int(float(conf["epieos_timeout"]))))
    except (TypeError, ValueError):
        conf["epieos_timeout"] = 120
    conf["epieos_pack"] = re.sub(r"[^a-z0-9_\-]", "", str(conf["epieos_pack"]).lower()) or "osinter"
    return conf


SERVICES = _load_services_conf()


def _http_json_full(url, payload=None, headers=None, timeout=20, explain=None):
    """Come _http_json ma ritorna (dati, errore, header di risposta, codice HTTP).
    'explain' traduce i codici HTTP del servizio in messaggi chiari; il corpo
    dell'errore (JSON {statusCode, error, message} o testo) e' allegato."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, method="POST" if body is not None else "GET")
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace")), None, dict(r.headers), r.status
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace").strip()[:300]
            try:
                j = json.loads(detail)
                if isinstance(j, dict):
                    detail = str(j.get("message") or j.get("error") or detail)[:160]
            except ValueError:
                detail = detail[:160]
        except Exception:
            pass
        hdrs = dict(e.headers or {})
        text = (explain or {}).get(e.code) or ({401: "chiave API mancante o non valida",
                                                403: "chiave API mancante o non valida"}.get(e.code, ""))
        if text:
            detail = text + (f" - {detail}" if detail else "")
        return None, f"HTTP {e.code} {e.reason}" + (f" - {detail}" if detail else ""), hdrs, e.code
    except urllib.error.URLError as e:
        return None, f"{e.reason}", {}, 0
    except Exception as e:
        return None, f"{type(e).__name__}: {e}", {}, 0

_AI_TYPES = {"person": "persona", "organization": "organization", "organisation": "organization",
             "company": "organization", "phone": "telefono", "email": "email",
             "username": "username", "social": "social", "link": "link", "url": "link",
             "website": "link", "place": "luogo", "address": "luogo", "location": "luogo",
             "vehicle": "veicolo", "car": "veicolo", "text": "testo", "note": "testo"}
_AI_TYPES.update({t: t for t in onto.TYPES})     # arma, stupefacente, assegno...



# stato della scansione in corso, aggiornato dal thread di lavoro e letto dal
# client tramite /api/sources/progress (polling: robusto anche da eseguibile).
_scan = {"running": False, "done": 0, "total": 0, "name": "",
         "finished": False, "error": "", "summary": None}
_scan_lock = _threading.Lock()
