# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""AI: from free text to nodes, configuration and test of the chatbot."""
# "Quis custodiet ipsos custodes?" (Juvenal, Satires VI)
# Who will guard the guards themselves?
import json
import logging
import re
import time

from flask import Blueprint, jsonify, request

from .. import ontology as onto
from ..core import _AI_TYPES, NodeError
from ..chatbot import (
    _bot, _load_chatbot_conf, CHATBOT, chatbot_ask, CHATBOT_CONF, chatbot_probe, chatbot_ready,
)
from ..transliteration import _estrai_json
from ..normalize import parse_birth
from ..archive import current_graph
from ..bulk_import import _norm, _plan_json, commit_plan, plan_rows, SOCIAL_PLATFORMS

bp = Blueprint("ai", __name__)


# ======================= AI: DAL TESTO LIBERO AI NODI =======================
# L'utente incolla un testo libero; il chatbot ne estrae entita' e relazioni in
# JSON. La risposta del modello e' un DATO, mai un comando: se ne prendono solo
# i campi previsti, validati dalle stesse regole dell'importazione da file.

AI_MAX_TEXT = 12000
AI_MAX_NODES = 60
AI_MAX_LINKS = 120
AI_TIMEOUT_MIN = 90            # l'estrazione e' piu' lunga di una traslitterazione

AI_NODES_PROMPT = """You extract entities for an OSINT link-analysis graph from the TEXT below.
Reply with ONE JSON object only (no markdown, no comments), exactly in this shape:
{{"nodes":[{{"key":"n1","type":"person","value":"...","birth":"","address":"","brand":"","model":"","color":"","fields":{{}},"label":"","url":"","platform":"","note":""}}],
 "links":[{{"from":"n1","to":"n2","label":"...","direction":"forward"}}]}}
Rules:
- type is one of: person, phone, email, username, social, link, place, vehicle, text,
  {onto_types}.
- value is the identifier exactly as written in the text: full name, phone number, e-mail,
  username without @, profile URL, web address (with http/https), city, licence plate.
- person: value = the full name with capitalised words (e.g. "Mario Rossi");
  birth = the date of birth if the TEXT states it, as YYYY-MM-DD (e.g. "nato il 12/03/1980"
  -> "1980-03-12"), otherwise "". "birth" is used only for person nodes.
- place: ONE node per location, with the CITY and the STREET ADDRESS TOGETHER in the same node:
  value = the city/town only (e.g. "Brescia"); address = street type (if written),
  street name and house number in the usual form (e.g. "Via Papa Leone 13"; "nr."/"n."
  dropped), otherwise "". The street type (via, viale, piazza, corso, largo, strada...)
  is optional: "abita in Giacomo Leopardi 5 a Brescia" -> value "Brescia",
  address "Giacomo Leopardi 5". Never put the street type or the street in value,
  never put the city in address.
  NEVER create a separate node for the city and another for the street of the same location.
  If only a city is mentioned, address = "". "address" is used only for place nodes.
  Link the person/organization to the place (label e.g. "residenza", "sede", "domicilio").
- Place of birth ("nato a", "nata a", "born in"): ALWAYS a SEPARATE place node with the
  birth city only (address = ""), even when it is the same city as the residence, linked
  from the person with label exactly "città di nascita". Never put it only in a note.
  Example: "Mario Rossi che abita a Brescia in via papa leone nr. 13" ->
  nodes: {{"key":"n1","type":"person","value":"Mario Rossi"}},
         {{"key":"n2","type":"place","value":"Brescia","address":"Via Papa Leone 13"}};
  links: {{"from":"n1","to":"n2","label":"residenza","direction":"forward"}}.
  Example: "Giulia Verdi, nata a Roma, vive a Milano in corso Buenos Aires 45" ->
  nodes: {{"key":"n1","type":"person","value":"Giulia Verdi"}},
         {{"key":"n2","type":"place","value":"Roma","address":""}},
         {{"key":"n3","type":"place","value":"Milano","address":"Corso Buenos Aires 45"}};
  links: {{"from":"n1","to":"n2","label":"città di nascita","direction":"forward"}},
         {{"from":"n1","to":"n3","label":"residenza","direction":"forward"}}.
- vehicle: value = the licence plate ONLY (e.g. "AB123CD"), never the make or model;
  brand = the make (e.g. "Fiat"), model = the model (e.g. "Panda"), color = the colour
  (e.g. "Bianco"), each "" if not stated. "brand", "model", "color" are used only for vehicles.
  The TEXT may be a table (CSV, ";" or tab separated, with a header row such as
  marca;modello;targa;colore): then EVERY data row is one vehicle, read each value from
  its column, and do not create nodes for the header. A vehicle linked to nobody gets no link.
  Example: "marca;modello;targa;colore\nFiat;Panda;AB123CD;Bianco" ->
  nodes: {{"key":"n1","type":"vehicle","value":"AB123CD","brand":"Fiat","model":"Panda","color":"Bianco"}}.
- Investigative items (weapons, drugs, money, documents, devices, organizations, events,
  real estate): put the details in "fields" (an object with the keys listed below; only
  keys that the TEXT states, use the exact option text when one fits) and set value to the
  main detail. One node per distinct item (e.g. each seized drug with its own quantity).
{onto_rules}
- social: value = the profile URL if present, otherwise the username; always set platform
  (instagram, facebook, tiktok, x, telegram, whatsapp, linkedin, youtube, vk, snapchat, github...).
- label: optional short display name (e.g. the owner's name for a social profile), otherwise "".
- note: optional short context taken from the text (max 200 characters), otherwise "".
- text: only for a relevant free-text fact; value = short title, note = the content.
- links: relationships stated or clearly implied by the text. label = a short relationship
  written in the language of the TEXT (e.g. "fratello", "socio", "utenza", "profilo", "residenza").
  direction: "forward" (from -> to), "backward", "both" or "none".
{root}- Never invent data that is not in the TEXT. One node per distinct identifier. Max {max_nodes} nodes.
TEXT:
<<<
{text}
>>>"""

AI_ROOT_RULE = ('- The TEXT is about an EXISTING node with key "ROOT": "{label}" (type {ntype}). '
                'Do NOT add it to "nodes"; use "ROOT" in links. '
                'Connect every new node to ROOT or to another node.\n')
_AI_DIR = {"forward": "->", "backward": "<-", "both": "<->", "none": ""}


def ai_ready():
    """L'AI e' utilizzabile: interruttore acceso ed endpoint impostato."""
    return chatbot_ready()


def _ai_str(v, n=300):
    v = re.sub(r"\s+", " ", str(v if v is not None else "")).strip()
    return "".join(c for c in v if c.isprintable())[:n]


# inizio tipico di un indirizzo (via, piazza, street...) o numero civico
_STREET_RE = re.compile(
    r"^(via|viale|v\.le|piazza|p\.za|piazzale|corso|c\.so|largo|vicolo|strada|"
    r"contrada|localita|località|loc\.|frazione|borgo|lungomare|lungo\w+|"
    r"calle|avenida|rue|street|st\.|road|rd\.|avenue|ave\.)\b|\d", re.I)


def _is_street(v):
    return bool(_STREET_RE.search(str(v or "").strip()))


BIRTH_LABEL = "città di nascita"
_BIRTH_RE = re.compile(r"nascit|nato|nata\b|natal|birth|born", re.I)


def _norm_street(v):
    """'via papa leone nr. 13' -> 'Via papa leone 13'."""
    v = re.sub(r"\b(nr|n|num|numero|civico)\.?\s*(?=\d)", "", str(v or ""), flags=re.I)
    v = re.sub(r"\s+", " ", v).strip(" ,")
    return v[:1].upper() + v[1:]


def _ai_merge_places(nodes, links):
    """Citta' e indirizzo della stessa localita' devono stare in UN nodo luogo.
    Se il modello li ha separati (un luogo 'Brescia' e un luogo 'Via Papa
    Leone 13'), la via confluisce nella citta' collegata: a lei stessa, oppure
    allo stesso nodo (es. la persona che ci abita). Ritorna i link aggiornati."""
    luoghi = [k for k, n in nodes.items() if n["type"] == "luogo"]
    nascita = set()                        # citta' di nascita: sempre un nodo a se'
    for l in links:
        if _BIRTH_RE.search(_ai_str(l.get("label"), 120)):
            l["label"] = BIRTH_LABEL
            nascita.update(k for k in (_ai_str(l.get("from"), 40), _ai_str(l.get("to"), 40))
                           if k in luoghi)
    for k in luoghi:                       # un luogo con solo la via nel valore
        n = nodes[k]
        if not n["address"] and _is_street(n["value"]):
            n["address"], n["value"] = n["value"], ""
    vie = [k for k in luoghi if nodes[k]["address"] and not nodes[k]["value"]]
    citta = [k for k in luoghi if nodes[k]["value"] and not nodes[k]["address"]
             and k not in nascita]

    def vicini(k):
        out = set()
        for l in links:
            a, b = _ai_str(l.get("from"), 40), _ai_str(l.get("to"), 40)
            if a == k:
                out.add(b)
            elif b == k:
                out.add(a)
        return out

    rinomina = {}
    for v in vie:
        nv = vicini(v)
        # prima una citta' collegata direttamente, poi una che condivide un vicino,
        # infine l'unica citta' del testo
        cand = [c for c in citta if c in nv] or \
               [c for c in citta if vicini(c) & nv] or \
               (citta if len(citta) == 1 and len(vie) == 1 else [])
        if not cand:
            continue
        c = cand[0]
        citta.remove(c)
        nodes[v]["value"] = nodes[c]["value"]
        nodes[v]["note"] = nodes[v]["note"] or nodes[c]["note"]
        rinomina[c] = v
        del nodes[c]
    for k in luoghi:
        if k not in nodes:
            continue
        nodes[k]["address"] = _norm_street(nodes[k]["address"])
        if not nodes[k]["value"]:          # via senza citta': resta la via come valore
            nodes[k]["value"], nodes[k]["address"] = nodes[k]["address"], ""
    if not rinomina:
        return links
    out, visti = [], set()
    for l in links:
        a = rinomina.get(_ai_str(l.get("from"), 40), _ai_str(l.get("from"), 40))
        b = rinomina.get(_ai_str(l.get("to"), 40), _ai_str(l.get("to"), 40))
        lab = _ai_str(l.get("label"), 120).casefold()
        if a == b or (a, b, lab) in visti or (b, a, lab) in visti:
            continue                       # l'arco citta'-via o un doppione
        visti.add((a, b, lab))
        out.append(dict(l, **{"from": a, "to": b}))
    return out


def _ai_vehicle(node, raw):
    """Veicolo proposto dal modello: l'identificativo e' la TARGA; marca e
    modello (se ci sono) vanno nell'etichetta, il colore nella nota.
    'AB 123 CD' + Fiat Panda bianca -> 'AB123CD Fiat Panda', colore 'Bianco' (va
    solo nella scheda, non nelle note)."""
    targa = re.sub(r"[\s.-]+", "", node["value"]).upper()
    marca = _ai_str(raw.get("brand"), 60)
    modello = _ai_str(raw.get("model"), 60)
    colore = _ai_str(raw.get("color"), 40)
    node["value"] = targa
    node["label"] = " ".join(p for p in (targa, marca, modello) if p)
    node["colore"] = colore[:1].upper() + colore[1:] if colore else ""


def _safe_birth(v):
    """Data di nascita proposta dal modello: se non e' valida si ignora."""
    try:
        return parse_birth(_ai_str(v, 20))
    except NodeError:
        return ""


def ai_rows_from_json(d, parent=None):
    """JSON del modello -> righe per plan_rows(). Si tengono solo i campi
    previsti, ripuliti e limitati: il resto della risposta si ignora."""
    raw_nodes = d.get("nodes") if isinstance(d.get("nodes"), list) else []
    raw_links = d.get("links") if isinstance(d.get("links"), list) else []
    nodes = {}
    for n in raw_nodes[:AI_MAX_NODES]:
        if not isinstance(n, dict):
            continue
        key = _ai_str(n.get("key"), 40) or f"n{len(nodes) + 1}"
        value = _ai_str(n.get("value"), 500)
        typ = _AI_TYPES.get(_ai_str(n.get("type"), 30).lower(), "")             or onto.type_of(_ai_str(n.get("type"), 30)) or ""
        raw_f = dict(n.get("fields") or {}) if isinstance(n.get("fields"), dict) else {}
        if typ in onto.TYPES:
            # il modello a volte mette marca/modello nei campi dei veicoli
            for k_ai, k_f in (("brand", "marca"), ("model", "modello")):
                if n.get(k_ai) and not raw_f.get(k_f):
                    raw_f[k_f] = n.get(k_ai)
        fields = onto.clean_fields(typ, raw_f) if typ in onto.TYPES else {}
        if typ in onto.TYPES and not value:
            value = fields.get(onto.TYPES[typ]["value"]) or onto.label_of(typ, fields) if fields else ""
        if not value or key == "ROOT" or key in nodes:
            continue
        plat = _norm(n.get("platform"))
        url = _ai_str(n.get("url"), 500)
        if not re.match(r"^https?://", url, re.I):
            url = ""
        if typ == "social" and re.match(r"^https?://", value, re.I) and not url:
            url = value
        nodes[key] = {"type": typ, "value": value, "label": _ai_str(n.get("label"), 200),
                      "url": url, "platform": plat if plat in SOCIAL_PLATFORMS else "",
                      "note": _ai_str(n.get("note"), 400),
                      "address": _ai_str(n.get("address"), 300) if typ == "luogo" else "",
                      "birth": _safe_birth(n.get("birth")) if typ == "persona" else ""}
        if typ == "veicolo":
            _ai_vehicle(nodes[key], n)
        nodes[key]["fields"] = fields
    raw_links = _ai_merge_places(nodes, [l for l in raw_links[:AI_MAX_LINKS]
                                         if isinstance(l, dict)])

    def side(key, s, row):
        if key == "ROOT" and parent:
            row[f"id{s}"] = parent
            return True
        n = nodes.get(key)
        if not n:
            return False
        row.update({f"name{s}": n["value"], f"type{s}": n["type"], f"url{s}": n["url"],
                    f"label{s}": n["label"], f"platform{s}": n["platform"],
                    f"note{s}": n["note"], f"address{s}": n["address"],
                    f"nascita{s}": n["birth"], f"colore{s}": n.get("colore", ""),
                    f"fields{s}": json.dumps(n.get("fields") or {}, ensure_ascii=False)})
        if n["type"] == "testo":
            row[f"text{s}"] = n["note"]
        return True

    rows, used = [], set()
    for l in raw_links[:AI_MAX_LINKS]:
        if not isinstance(l, dict):
            continue
        a, b = _ai_str(l.get("from"), 40), _ai_str(l.get("to"), 40)
        if a == b:
            continue
        row = {"rel": _ai_str(l.get("label"), 120),
               "arrow": _AI_DIR.get(_ai_str(l.get("direction"), 10).lower(), "")}
        if side(a, "1", row) and side(b, "2", row):
            rows.append(row)
            used.update((a, b))
    if parent and rows and not any(r.get("id1") == parent or r.get("id2") == parent
                                   for r in rows):
        # dalla scheda di un nodo ma il modello non lo ha mai citato: il nodo
        # principale del testo (quello con piu' collegamenti) si aggancia a lui
        deg = {}
        for l in raw_links[:AI_MAX_LINKS]:
            if isinstance(l, dict):
                for k in (_ai_str(l.get("from"), 40), _ai_str(l.get("to"), 40)):
                    if k in nodes:
                        deg[k] = deg.get(k, 0) + 1
        main = max(nodes, key=lambda k: (deg.get(k, 0), -list(nodes).index(k)))
        row = {}
        side("ROOT", "1", row)
        side(main, "2", row)
        rows.insert(0, row)
    for key in nodes:                     # nodi rimasti senza collegamenti
        if key in used:
            continue
        row = {}
        if parent:                        # dalla scheda di un nodo: si collegano a lui
            side("ROOT", "1", row)
            side(key, "2", row)
        else:
            side(key, "1", row)
        rows.append(row)
    for i, r in enumerate(rows):
        r["_row"] = i + 1
    return rows


@bp.route("/api/ai/nodes", methods=["POST"])
def api_ai_nodes():
    """Testo libero -> proposta di nodi e collegamenti (niente viene scritto:
    l'utente conferma poi con /api/ai/commit)."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()
    parent = str(data.get("parent") or "").strip()
    if not ai_ready():
        return jsonify({"error": "AI disattivata o non configurata", "config": True}), 400
    if len(text) < 3:
        return jsonify({"error": "testo mancante"}), 400
    text = text[:AI_MAX_TEXT]
    root = ""
    if parent:
        p = next((n for n in current_graph()["nodes"] if n["id"] == parent), None)
        if p is None:
            return jsonify({"error": "nodo di partenza non trovato"}), 404
        root = AI_ROOT_RULE.format(label=_ai_str(p.get("label"), 120).replace('"', "'"),
                                   ntype=p.get("ntype") or "")
    ok, why = chatbot_probe()                  # sonda rapida: niente attese inutili
    if not ok:
        return jsonify({"error": f"il chatbot non risponde ({CHATBOT['endpoint']}): {why}"}), 502
    prompt = AI_NODES_PROMPT.format(root=root, text=text, max_nodes=AI_MAX_NODES,
                                    onto_types=", ".join(onto.TYPES), onto_rules=onto.ai_rules())
    old = CHATBOT["timeout"]
    CHATBOT["timeout"] = max(old, AI_TIMEOUT_MIN)
    try:
        answer = chatbot_ask(prompt, force=True, json_mode=True)
    finally:
        CHATBOT["timeout"] = old
    if answer is None:
        return jsonify({"error": "il chatbot non risponde: " + (_bot["reason"] or "nessuna risposta")}), 502
    rows = ai_rows_from_json(_estrai_json(answer), parent or None)
    if not rows:
        return jsonify({"error": "l'AI non ha trovato entita' nel testo"}), 422
    plan = plan_rows(rows)
    logging.info(f"AI: proposti {len(rows)} elementi dal testo ({len(text)} caratteri)")
    return jsonify({"ok": True, "rows": _plan_json(plan), "items": rows,
                    "model": CHATBOT["model"]})


@bp.route("/api/ai/commit", methods=["POST"])
def api_ai_commit():
    """Crea i nodi e i collegamenti proposti dall'AI e confermati dall'utente.
    Le righe passano di nuovo per le stesse validazioni dell'importazione."""
    data = request.get_json(silent=True) or {}
    items = [r for r in (data.get("items") or []) if isinstance(r, dict)][:AI_MAX_NODES + AI_MAX_LINKS]
    rows = [{str(k): str(v)[:2000] for k, v in r.items()} for r in items]
    skip = {int(x) for x in (data.get("skip") or []) if str(x).isdigit()}
    try:
        res = commit_plan(plan_rows(rows), skip)
    except NodeError as e:
        return jsonify({"error": str(e)}), 400
    logging.info(f"AI: creati {res['nodes']} nodi e {res['links']} collegamenti")
    return jsonify(res)


# ---------------- pannello di configurazione dell'AI (chatbot.conf) ----------------
AI_CONF_KEYS = ("enabled", "endpoint", "api_key", "model", "api", "timeout",
                "auth_header", "auth_prefix", "auto")


def _conf_public():
    k = CHATBOT.get("api_key") or ""
    return {"enabled": bool(CHATBOT["enabled"]), "endpoint": CHATBOT["endpoint"],
            "has_key": bool(k), "key_hint": ("…" + k[-4:]) if len(k) > 8 else ("•" * len(k)),
            "model": CHATBOT["model"], "api": CHATBOT["api"], "timeout": CHATBOT["timeout"],
            "auth_header": CHATBOT["auth_header"], "auth_prefix": CHATBOT["auth_prefix"],
            "auto": bool(CHATBOT["auto"]), "ready": ai_ready(),
            "down": _bot["reason"] or ""}


def save_chatbot_conf(updates):
    """Aggiorna chatbot.conf conservando commenti e ordine delle righe; le voci
    che mancano si aggiungono in fondo."""
    eol = "\n"
    try:
        # newline="": si legge il file com'e', per riscriverlo con le stesse
        # fine riga (su Windows la modalita' testo le convertirebbe in CRLF)
        with open(CHATBOT_CONF, "r", encoding="utf-8-sig", newline="") as f:
            testo = f.read()
        if "\r\n" in testo:
            eol = "\r\n"
        lines = testo.splitlines()
    except FileNotFoundError:
        lines = ["# chatbot.conf - configurazione del chatbot (AI)."]
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
    with open(CHATBOT_CONF, "w", encoding="utf-8", newline="") as f:
        f.write(eol.join(lines) + eol)


def reload_chatbot_conf():
    CHATBOT.clear()
    CHATBOT.update(_load_chatbot_conf())
    _bot.update({"api": None, "down_until": 0.0, "reason": "", "ok_at": 0.0})


@bp.route("/api/ai/config", methods=["GET", "POST"])
def api_ai_config():
    """Legge / salva la configurazione dell'AI. La chiave non viene mai
    restituita per intero: si manda solo se la si vuole cambiare."""
    if request.method == "GET":
        return jsonify(_conf_public())
    data = request.get_json(silent=True) or {}
    up = {}
    for k in AI_CONF_KEYS:
        if k not in data:
            continue
        v = data[k]
        if k in ("enabled", "auto"):
            up[k] = "true" if v in (True, "true", "1", 1, "on") else "false"
            continue
        v = re.sub(r"[\r\n]+", " ", str(v if v is not None else "")).strip()[:500]
        if k == "api_key" and not v and not data.get("clear_key"):
            continue                              # vuota = lascia quella che c'e'
        if k == "endpoint" and v and not re.match(r"^https?://[^\s]+$", v, re.I):
            return jsonify({"error": "endpoint non valido (serve http:// o https://)"}), 400
        if k == "api" and v not in ("auto", "ollama", "openai"):
            return jsonify({"error": "formato API non valido"}), 400
        if k == "timeout":
            try:
                v = str(max(1, min(600, int(float(v)))))
            except ValueError:
                return jsonify({"error": "timeout non valido"}), 400
        up[k] = v
    try:
        save_chatbot_conf(up)
    except OSError as e:
        return jsonify({"error": f"impossibile scrivere chatbot.conf: {e}"}), 500
    reload_chatbot_conf()
    logging.info(f"Configurazione AI aggiornata: {sorted(up)}")
    return jsonify(_conf_public())


@bp.route("/api/ai/test", methods=["POST"])
def api_ai_test():
    """Prova di collegamento: una domanda banale al modello configurato."""
    if not CHATBOT["endpoint"]:
        return jsonify({"ok": False, "error": "endpoint non impostato"})
    t0 = time.time()
    ok, why = chatbot_probe()
    if not ok:
        return jsonify({"ok": False, "error": f"server irraggiungibile: {why}",
                        "ms": int((time.time() - t0) * 1000)})
    answer = chatbot_ask('Reply with the single word: OK', force=True, ignore_switch=True)
    ms = int((time.time() - t0) * 1000)
    if answer is None:
        return jsonify({"ok": False, "error": _bot["reason"] or "nessuna risposta", "ms": ms})
    return jsonify({"ok": True, "answer": _ai_str(answer, 80), "ms": ms,
                    "api": _bot["api"], "model": CHATBOT["model"]})
