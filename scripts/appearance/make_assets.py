# -*- coding: utf-8 -*-
# Quaesitor - case graph for OSINT investigations
# Copyright (C) 2026 Ramingo (SOsintOps)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Builds the data behind the node appearance (quaesitor/appearance.py):

    quaesitor/static/vendor/flags/<cc>.svg   square flags of flag-icons (MIT)
    quaesitor/static/vendor/icons/<slug>.svg brand logos of Simple Icons (CC0), coloured
    quaesitor/generated/countries.json       country names in the six interface languages
                                             (CLDR, through Intl.DisplayNames of Node) and
                                             the calling codes of libphonenumber (Apache-2.0)

    .venv\\Scripts\\python.exe scripts\\appearance\\make_assets.py

Needs Node (for the country names) and the network; the versions are pinned and the npm
packages are checked against their published sha512. Run it again to update them.
"""
# "Signa temporis." (after Matthew 16:3)
# The signs of the times.
import base64
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VENDOR = os.path.join(ROOT, "quaesitor", "static", "vendor")
GENERATED = os.path.join(ROOT, "quaesitor", "generated")

FLAG_ICONS = "7.5.0"
SIMPLE_ICONS = "16.35.0"
LIBPHONENUMBER = "v9.0.40"
LANGS = ("en", "it", "fr", "de", "es", "ar")
# logos used by the appearance rules: card networks, blockchains, e-mail providers
LOGOS = ("visa", "mastercard", "americanexpress", "dinersclub", "discover", "jcb",
         "bitcoin", "ethereum", "tether", "monero", "litecoin", "solana", "bnbchain",
         "gmail", "protonmail", "icloud", "gmx", "maildotru", "zoho")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "quaesitor-make-assets"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def npm(name, version):
    """The package tarball, checked against the integrity published by npm."""
    meta = json.loads(get(f"https://registry.npmjs.org/{name}/{version}"))
    blob = get(meta["dist"]["tarball"])
    algo, digest = meta["dist"]["integrity"].split("-", 1)
    if base64.b64encode(hashlib.new(algo, blob).digest()).decode() != digest:
        raise SystemExit(f"{name} {version}: integrity check failed")
    return tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz")


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def flags():
    out = os.path.join(VENDOR, "flags")
    n = 0
    with npm("flag-icons", FLAG_ICONS) as t:
        for m in t.getmembers():
            hit = re.fullmatch(r"package/flags/1x1/([a-z]{2})\.svg", m.name)
            if hit:
                write(os.path.join(out, f"{hit.group(1)}.svg"), t.extractfile(m).read())
                n += 1
            elif m.name == "package/LICENSE":
                write(os.path.join(out, "LICENSE"), t.extractfile(m).read())
    return n


def logos():
    with npm("simple-icons", SIMPLE_ICONS) as t:
        data = json.loads(t.extractfile("package/data/simple-icons.json").read())
        icons = data if isinstance(data, list) else data["icons"]
        hexes = {i.get("slug"): i["hex"] for i in icons if i.get("slug")}
        for slug in LOGOS:
            svg = t.extractfile(f"package/icons/{slug}.svg").read().decode()
            svg = svg.replace("<svg ", f'<svg fill="#{hexes[slug]}" ', 1)
            write(os.path.join(VENDOR, "icons", f"{slug}.svg"), svg.encode())
    return len(LOGOS)


def nanp_area_codes(territory):
    """Area codes of the United States or Canada: the three digits after +1 that the
    fixed-line or mobile pattern of the territory accepts. libphonenumber gives the two
    countries no leading digits; toll-free codes (800...) belong to neither list."""
    pats = [re.sub(r"\s", "", e.findtext("nationalNumberPattern") or "")
            for e in (territory.find("fixedLine"), territory.find("mobile")) if e is not None]
    return [str(a) for a in range(200, 1000)
            if any(re.fullmatch(p, f"{a}{rest}") for p in pats if p
                   for rest in ("2345678", "5550100", "7654321", "9876543"))]


def calling_codes():
    """{code: {"main": cc or None, "lead": [[cc, leadingDigits], ...]}}. The main country
    is the one libphonenumber marks as such (+44 United Kingdom, +212 Morocco); +1 has none,
    because the United States and Canada share it: their area codes are listed as leading
    digits instead, so a toll-free number stays without a country."""
    xml = get("https://raw.githubusercontent.com/google/libphonenumber/"
              f"{LIBPHONENUMBER}/resources/PhoneNumberMetadata.xml")
    by_code, nanp = {}, {}
    for t in ET.fromstring(xml).iter("territory"):
        if t.get("id") in ("US", "CA"):
            nanp[t.get("id").lower()] = "|".join(nanp_area_codes(t))
        cc, code = t.get("id"), t.get("countryCode")
        if not cc or not code or cc == "001":
            continue
        by_code.setdefault(code, []).append((cc.lower(), t.get("mainCountryForCode") == "true",
                                             (t.get("leadingDigits") or "").strip()))
    out = {}
    for code, terr in by_code.items():
        plain = [t for t in terr if not t[2]]
        flagged = [t[0] for t in terr if t[1]]
        main = flagged[0] if flagged else (plain[0][0] if len(plain) == 1 else None)
        lead = [[c, ld] for c, _, ld in terr if ld]
        if code == "1":
            main = None
            lead += [[cc, nanp[cc]] for cc in ("us", "ca")]
        out[code] = {"main": main, "lead": lead}
    return out


def names(codes):
    js = ("const codes=" + json.dumps(sorted(codes)) + ";const out={};"
          "for(const l of " + json.dumps(list(LANGS)) + "){const d=new Intl.DisplayNames([l],{type:'region'});"
          "out[l]={};for(const c of codes){const n=d.of(c.toUpperCase());"
          "if(n&&n.toUpperCase()!==c.toUpperCase())out[l][c]=n;}}"
          "process.stdout.write(JSON.stringify(out));")
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, check=True,
                                     encoding="utf-8").stdout)


def main():
    n_flags = flags()
    n_logos = logos()
    codes = sorted(f[:-4] for f in os.listdir(os.path.join(VENDOR, "flags")) if f.endswith(".svg"))
    data = {"_source": f"names: CLDR via Intl.DisplayNames; calling codes: libphonenumber {LIBPHONENUMBER}",
            "names": names(codes), "calling": calling_codes()}
    with open(os.path.join(GENERATED, "countries.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print(f"{n_flags} flags, {n_logos} logos, {len(data['names']['en'])} country names, "
          f"{len(data['calling'])} calling codes")


if __name__ == "__main__":
    main()
