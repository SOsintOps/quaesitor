# -*- coding: utf-8 -*-
# Quaesitor - case graph for OSINT investigations
# Copyright (C) 2026 Ramingo (SOsintOps)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Appearance of the nodes from what they are, as Maltego does with overlays.

Two layers, computed when the graph is built and never saved:
    ficon    a variant of the main icon (a woman, a rifle, a Visa card...)
    badges   up to four marks on the corners of the node, each corner with one
             meaning so that the eye learns where to look:
                 ne  brand or network (card network, blockchain, e-mail provider)
                 sw  country (flag)
                 se  alert (number not valid, expired, forged...)
                 nw  role in the case
             a badge is {"pos", "kind", "key", "title"}: kind "logo" (a Simple Icons
             slug in static/vendor/icons), "letter" (an initial on a colour, for a
             brand without a logo), "flag" (ISO 3166 alpha-2 code, static/vendor/flags)
             or "alert" (a Font Awesome glyph in red); the title is English, the
             interface translates it.

The detectors below read a value (a card number, an IBAN, an address...) and are pure
functions; the country tables come from quaesitor/generated/countries.json
(scripts/appearance/make_assets.py).
"""
# "Facies non omnibus una." (Ovid, Metamorphoses)
# Not one face for all.
from datetime import date
import json
import os
import re
import unicodedata

from . import ontology as onto
from .paths import GENERATED_DIR

_COUNTRIES = None


def _countries():
    global _COUNTRIES
    if _COUNTRIES is None:
        try:
            with open(os.path.join(GENERATED_DIR, "countries.json"), encoding="utf-8") as f:
                _COUNTRIES = json.load(f)
        except (OSError, ValueError):
            _COUNTRIES = {"names": {}, "calling": {}}
    return _COUNTRIES


def _fold(s):
    s = unicodedata.normalize("NFKD", str(s or "")).casefold()
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", s)).strip()


# ------------------------------------------------------------- countries ---
# names that CLDR does not give but people write
_COUNTRY_ALIASES = {"uk": "gb", "england": "gb", "great britain": "gb", "usa": "us",
                    "united states of america": "us", "america": "us", "holland": "nl",
                    "russia": "ru", "czech republic": "cz", "inghilterra": "gb",
                    "stati uniti d america": "us", "olanda": "nl", "vatican": "va"}
_NAME_INDEX = None


def _name_index():
    global _NAME_INDEX
    if _NAME_INDEX is None:
        idx = dict(_COUNTRY_ALIASES)
        for names in _countries()["names"].values():
            for cc, name in names.items():
                idx.setdefault(_fold(name), cc)
        _NAME_INDEX = idx
    return _NAME_INDEX


def country_code(text):
    """ISO 3166 alpha-2 code (lower case) of a country written as a code ('IT', 'it')
    or as a name in one of the interface languages ('Italy', 'Italia', 'Allemagne');
    None if not recognised."""
    t = str(text or "").strip()
    if not t:
        return None
    if re.fullmatch(r"[A-Za-z]{2}", t):
        cc = t.lower()
        return cc if cc in _countries()["names"].get("en", {}) else _COUNTRY_ALIASES.get(cc)
    return _name_index().get(_fold(t))


def country_name(cc, lang="en"):
    names = _countries()["names"]
    return (names.get(lang) or {}).get(cc) or (names.get("en") or {}).get(cc) or cc.upper()


# international vehicle registration codes that are not the ISO code of the country
VEHICLE_CODES = {"i": "it", "d": "de", "f": "fr", "e": "es", "a": "at", "b": "be", "p": "pt",
                 "h": "hu", "s": "se", "n": "no", "l": "lu", "m": "mt", "v": "va", "j": "jp",
                 "fin": "fi", "irl": "ie", "slo": "si", "srb": "rs", "bih": "ba", "mne": "me",
                 "nmk": "mk", "rus": "ru", "lar": "ly", "et": "eg", "usa": "us", "cdn": "ca",
                 "est": "ee", "rsm": "sm", "fl": "li", "mc": "mc", "ks": "xk", "rks": "xk"}


def vehicle_country(code):
    """Country of a licence plate from the sign on the car ('I', 'D', 'GB', 'LAR', 'LY')."""
    c = re.sub(r"[^a-z]", "", str(code or "").lower())
    if not c:
        return None
    return VEHICLE_CODES.get(c) or country_code(c)


# ---------------------------------------------------------------- phones ---
def phone_country(number):
    """Country of an international number (+39..., 0039...); None for a national
    number or for +1 without an area code that names the country."""
    s = str(number or "").strip()
    m = re.match(r"^(?:\+|00)\s*([\d\s().-]+)$", s)
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    calling = _countries()["calling"]
    for n in (1, 2, 3):
        code, rest = digits[:n], digits[n:]
        entry = calling.get(code)
        if not entry:
            continue
        for cc, lead in entry.get("lead") or []:
            if re.match(f"(?:{lead})", rest):
                return cc
        return entry.get("main")
    return None


# ----------------------------------------------------------------- cards ---
# (network, prefixes, lengths): Wikipedia, "Payment card number", 2026-10-13.
# The longest matching prefix wins.
_CARD_RANGES = [
    ("Visa", [(4, 4)], range(13, 20)),
    ("Mastercard", [(51, 55), (2221, 2720)], [16]),
    ("American Express", [(34, 34), (37, 37)], [15]),
    ("Diners Club", [(30, 30), (36, 36), (38, 39)], range(14, 20)),
    ("Discover", [(6011, 6011), (644, 649), (65, 65)], range(16, 20)),
    ("JCB", [(3528, 3589)], range(16, 20)),
    ("UnionPay", [(62, 62)], range(16, 20)),
    ("Maestro", [(5018, 5018), (5020, 5020), (5038, 5038), (5893, 5893), (6304, 6304),
                 (6759, 6759), (6761, 6763)], range(12, 20)),
    ("Mir", [(2200, 2204)], range(16, 20)),
]
# logo (Simple Icons slug) or initial and colour of each network
CARD_BRANDS = {"Visa": ("logo", "visa"), "Mastercard": ("logo", "mastercard"),
               "American Express": ("logo", "americanexpress"), "Diners Club": ("logo", "dinersclub"),
               "Discover": ("logo", "discover"), "JCB": ("logo", "jcb"),
               "UnionPay": ("letter", "U:#d71e28"), "Maestro": ("letter", "M:#0099df"),
               "Mir": ("letter", "M:#0f754e"), "Postepay": ("letter", "P:#ffd200")}


def card_digits(number):
    return re.sub(r"\D", "", str(number or ""))


def card_network(number):
    """Network of a card from its first digits; also for a masked number
    ('4111 **** **** 1111'), which keeps the prefix."""
    s = re.sub(r"[\s-]", "", str(number or ""))
    head = re.match(r"\d+", s)
    if not head:
        return None
    head = head.group(0)
    best, best_len = None, 0
    for name, ranges, _ in _CARD_RANGES:
        for lo, hi in ranges:
            n = len(str(lo))
            if len(head) >= n and lo <= int(head[:n]) <= hi and n > best_len:
                best, best_len = name, n
    return best


def luhn_ok(number):
    """True/False for a complete number, None for a masked or short one."""
    s = str(number or "")
    if re.search(r"[*xX•#]", s):
        return None
    d = card_digits(s)
    if len(d) < 12:
        return None
    total = 0
    for i, c in enumerate(reversed(d)):
        k = int(c)
        if i % 2:
            k = k * 2 - 9 if k > 4 else k * 2
        total += k
    return total % 10 == 0


# ---------------------------------------------------------- bank accounts ---
def iban_compact(iban):
    return re.sub(r"[\s.-]", "", str(iban or "")).upper()


def iban_country(iban):
    s = iban_compact(iban)
    if re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{8,30}", s):
        return country_code(s[:2])
    return None


def iban_ok(iban):
    """ISO 13616 check digits (mod 97); None if it is not shaped as an IBAN."""
    s = iban_compact(iban)
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{8,30}", s):
        return None
    moved = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in moved)) % 97 == 1


def bic_country(bic):
    s = re.sub(r"\s", "", str(bic or "")).upper()
    if re.fullmatch(r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?", s):
        return country_code(s[4:6])
    return None


# --------------------------------------------------------------- crypto ---
_B58 = "[1-9A-HJ-NP-Za-km-z]"
_CHAINS = [
    ("Bitcoin", re.compile(rf"^(?:bc1[02-9ac-hj-np-z]{{11,71}}|[13]{_B58}{{25,34}})$")),
    ("Litecoin", re.compile(rf"^(?:ltc1[02-9ac-hj-np-z]{{11,71}}|[LM]{_B58}{{26,33}})$")),
    ("Tether (USDT) - TRON", re.compile(rf"^T{_B58}{{33}}$")),
    ("Monero", re.compile(rf"^[48][0-9AB]{_B58}{{93}}$")),
    ("Ethereum", re.compile(r"^0x[0-9a-fA-F]{40}$")),
    ("Solana", re.compile(rf"^{_B58}{{43,44}}$")),
]
CHAIN_BRANDS = {"Bitcoin": ("logo", "bitcoin"), "Ethereum": ("logo", "ethereum"),
                "Tether (USDT) - TRON": ("letter", "T:#eb0029"),
                "Tether (USDT) - Ethereum": ("logo", "tether"), "Monero": ("logo", "monero"),
                "Litecoin": ("logo", "litecoin"), "Solana": ("logo", "solana"),
                "BNB Chain": ("logo", "bnbchain")}
# FtM currency codes of a wallet -> chain
_CURRENCY_CHAINS = {"btc": "Bitcoin", "eth": "Ethereum", "usdt": "Tether (USDT) - Ethereum",
                    "xmr": "Monero", "ltc": "Litecoin", "sol": "Solana", "bnb": "BNB Chain",
                    "trx": "Tether (USDT) - TRON"}


def crypto_chain(address):
    """Blockchain of a wallet address from its form; an address of an Ethereum-like
    chain (0x...) is reported as Ethereum."""
    s = re.sub(r"\s", "", str(address or ""))
    return next((name for name, rx in _CHAINS if rx.match(s)), None)


def chain_of(text):
    """Chain named in a field (blockchain option, currency code or name)."""
    t = _fold(text)
    if not t:
        return None
    if t in _CURRENCY_CHAINS:
        return _CURRENCY_CHAINS[t]
    return next((name for name in CHAIN_BRANDS if _fold(name) == t or t in _fold(name).split()), None)


# --------------------------------------------------------------- e-mail ---
_PROVIDERS = [
    (r"gmail\.com|googlemail\.com", "Gmail", ("logo", "gmail")),
    (r"(outlook|hotmail|live)\.[a-z.]+|msn\.com", "Outlook", ("letter", "O:#0078d4")),
    (r"(yahoo|ymail)\.[a-z.]+", "Yahoo", ("letter", "Y:#6001d2")),
    (r"proton\.me|protonmail\.(com|ch)|pm\.me", "Proton Mail", ("logo", "protonmail")),
    (r"icloud\.com|me\.com|mac\.com", "iCloud", ("logo", "icloud")),
    (r"gmx\.[a-z.]+", "GMX", ("logo", "gmx")),
    (r"(mail|bk|list|inbox)\.ru", "Mail.ru", ("logo", "maildotru")),
    (r"yandex\.[a-z.]+|ya\.ru", "Yandex", ("letter", "Y:#fc3f1d")),
    (r"zoho\.[a-z.]+|zohomail\.[a-z.]+", "Zoho", ("logo", "zoho")),
]


def email_provider(address):
    """(name, (kind, key)) of a known mail provider, or None."""
    m = re.search(r"@([\w.-]+)$", str(address or "").strip().lower())
    if not m:
        return None
    dom = m.group(1)
    return next(((name, brand) for rx, name, brand in _PROVIDERS if re.fullmatch(rx, dom)), None)


# ---------------------------------------------------------------- dates ---
def expiry_date(value):
    """Last valid day of an expiry written as YYYY-MM-DD, DD/MM/YYYY, MM/YY or MM/YYYY."""
    v = str(value or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v)
    if m:
        y, mo, d = map(int, m.groups())
        return date(y, mo, d)
    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", v)
    if m:
        d, mo, y = map(int, m.groups())
        return date(y, mo, d)
    m = re.fullmatch(r"(\d{1,2})\s*/\s*(\d{2}|\d{4})", v)
    if m:
        mo, y = int(m.group(1)), int(m.group(2))
        y = y + 2000 if y < 100 else y
        if not 1 <= mo <= 12:
            return None
        nxt = date(y + (mo == 12), 1 if mo == 12 else mo + 1, 1)
        return date.fromordinal(nxt.toordinal() - 1)
    return None


def expired(value, today=None):
    try:
        d = expiry_date(value)
    except ValueError:
        return False
    return bool(d) and d < (today or date.today())


# ================================================================= rules ===
# They read the node as the interface shows it: the investigative fields come back
# from the readable labels of the cards (ontology.raw_of), so a node from the data, a
# card merged into it and a value edited by hand are read the same way.

POSITIONS = ("ne", "sw", "se", "nw")


def _merged_raw(node):
    """First non-empty value of every card key, over all the cards of the node."""
    out = {}
    for r in node.get("records") or []:
        raw = r.get("raw") if isinstance(r, dict) else None
        if isinstance(raw, dict):
            for k, v in raw.items():
                if k not in out and isinstance(v, (str, int, float)) and str(v).strip():
                    out[k] = v
    return out


def node_fields(ntype, raw):
    """{field key: value} of an investigative type from the card labels."""
    spec = onto.TYPES.get(ntype)
    if not spec:
        return {}
    out = {}
    for f in spec["fields"]:
        v = raw.get(f["label"])
        if v in (None, ""):
            continue
        out[f["key"]] = (str(v).strip().lower() in ("yes", "true", "1")) if f["type"] == "check" else str(v)
    return out


class _Ctx:
    def __init__(self, node):
        self.node = node
        self.ntype = node.get("ntype") or ""
        self.raw = _merged_raw(node)
        self.fields = node_fields(self.ntype, self.raw)

    def get(self, *keys):
        """First value among the fields and the card keys named."""
        for k in keys:
            v = self.fields.get(k)
            if v in (None, ""):
                v = self.raw.get(k)
            if v not in (None, "") and str(v).strip():
                return str(v).strip()
        return ""


def badge(pos, kind, key, title):
    return {"pos": pos, "kind": kind, "key": key, "title": title}


def brand_badge(brand, title):
    kind, key = brand
    return badge("ne", kind, key, title)


def flag_badge(cc):
    return badge("sw", "flag", cc, country_name(cc)) if cc else None


def alert_badge(title, icon="triangle-exclamation"):
    return badge("se", "alert", icon, title)


def _variant(ctx):
    """Variant of the main icon: the sex of a person, the sub-type of an item."""
    if ctx.ntype == "name":
        return onto.PERSON_ICONS.get(ctx.node.get("sex") or "")
    if ctx.ntype in onto.TYPES:
        return onto.icon_of(ctx.ntype, ctx.fields)
    return None


# per type: functions (ctx) -> list of badges (None entries are dropped)
RULES = {}


def rule(*ntypes):
    def deco(fn):
        for t in ntypes:
            RULES.setdefault(t, []).append(fn)
        return fn
    return deco


def decorate(node):
    """Sets ficon and badges of the node (in place) and returns it."""
    ctx = _Ctx(node)
    v = _variant(ctx)
    if v:
        node["ficon"] = v
    else:
        node.pop("ficon", None)
    # the value that picked the variant (e.g. "Assault rifle"): the chart key names it
    sub = onto.SUBTYPE_ICONS.get(ctx.ntype)
    fv = ctx.fields.get(sub[0]) if sub else None
    if fv and v and v != onto.TYPES[ctx.ntype]["icon"]:
        node["fvalue"] = fv
    else:
        node.pop("fvalue", None)
    marks = {}
    for fn in RULES.get(ctx.ntype, []) + RULES.get("*", []):
        for b in fn(ctx) or []:
            if b and b["pos"] not in marks:          # first rule wins its corner
                marks[b["pos"]] = b
    if marks:
        node["badges"] = [marks[p] for p in POSITIONS if p in marks]
    else:
        node.pop("badges", None)
    return node


def apply_appearance(g):
    for n in g["nodes"]:
        decorate(n)
    return g


# ------------------------------------------------------------- the rules ---
@rule("card")
def _card(ctx):
    number = ctx.get("number")
    net = ctx.get("network")
    if net not in CARD_BRANDS:
        net = card_network(number)
    out = [brand_badge(CARD_BRANDS[net], net) if net in CARD_BRANDS else None]
    if luhn_ok(number) is False:
        out.append(alert_badge("Card number not valid"))
    elif expired(ctx.get("expiry")):
        out.append(alert_badge("Expired", "clock"))
    return out


@rule("crypto", "cryptowallet")
def _wallet(ctx):
    chain = chain_of(ctx.get("blockchain")) or chain_of(ctx.get("currency")) or \
        crypto_chain(ctx.get("address", "publicKey", "cryptoAddress"))
    return [brand_badge(CHAIN_BRANDS[chain], chain)] if chain in CHAIN_BRANDS else []


@rule("bankaccount", "ftmbankaccount")
def _account(ctx):
    iban = ctx.get("iban")
    cc = iban_country(iban) or bic_country(ctx.get("bic")) or country_code(ctx.get("country"))
    out = [flag_badge(cc)]
    if iban_ok(iban) is False:
        out.append(alert_badge("IBAN not valid"))
    return out


@rule("phone")
def _phone(ctx):
    cc = phone_country(ctx.node.get("label")) or \
        country_code(ctx.get("country_code", "countryCode", "country", "country_name"))
    return [flag_badge(cc)]


@rule("email")
def _email(ctx):
    p = email_provider(ctx.node.get("label"))
    return [brand_badge(p[1], p[0])] if p else []


@rule("document", "identification", "passport")
def _document(ctx):
    out = [flag_badge(country_code(ctx.get("country")))]
    if ctx.fields.get("forged"):
        out.append(alert_badge("Forged"))
    elif expired(ctx.get("expiry", "endDate")):
        out.append(alert_badge("Expired", "clock"))
    return out


@rule("weapon")
def _weapon(ctx):
    return [alert_badge("Serial number removed")] if ctx.fields.get("serial_removed") else []


@rule("cash")
def _cash(ctx):
    return [alert_badge("Counterfeit")] if ctx.fields.get("counterfeit") else []


@rule("name", "target")
def _person(ctx):
    return [flag_badge(country_code(ctx.get("nationality", "citizenship")))]


@rule("company", "legalentity", "ftmorganization", "publicbody", "organization")
def _company(ctx):
    return [flag_badge(country_code(ctx.get("jurisdiction", "mainCountry", "country")))]


@rule("vessel")
def _vessel(ctx):
    return [flag_badge(country_code(ctx.get("flag", "country")))]


@rule("vehicle")
def _vehicle(ctx):
    return [flag_badge(vehicle_country(ctx.get("Country")))]


@rule("*")
def _country(ctx):
    """Any investigative or Follow the Money type with a country field."""
    if ctx.ntype in onto.TYPES and any(f["key"] == "country" for f in onto.TYPES[ctx.ntype]["fields"]):
        return [flag_badge(country_code(ctx.get("country")))]
    return []
