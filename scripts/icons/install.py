# -*- coding: utf-8 -*-
# Quaesitor - case graph for OSINT investigations
# Copyright (C) 2026 Ramingo (SOsintOps)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Installs the node icons chosen in scripts/icons/mapping.json.

    .venv\\Scripts\\python.exe scripts\\icons\\split_sheets.py      (once, cuts the sheets)
    .venv\\Scripts\\python.exe scripts\\icons\\install.py

Every key of mapping.json must be a node type (ontology.TYPES, ontology.BASE_ICONS) or a
sub-type icon of ontology.icon_of; the cut it names is copied to
static/icons/entities/<key>.png and static/icons/entities/index.json lists the keys.
The client (iconFor in static/app.js) uses these icons before the Font Awesome glyphs.
A review sheet with every installed icon and its key is written next to the cuts.
"""
# "Nomen est omen." (Plautus, Persa)
# The name is a sign.
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import ontology as onto  # noqa: E402

DEST = os.path.join(ROOT, "static", "icons", "entities")


def known_keys():
    keys = set(onto.TYPES) | set(onto.BASE_ICONS) | {"account", "photo", "audio", "video"}
    for table in (onto.DRUG_ICONS, onto.DOC_ICONS, onto.FINDOC_ICONS, onto.LEGALDOC_ICONS, onto.DEVICE_ICONS):
        keys |= set(table.values())
    return keys


def main():
    cuts = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "icone grezze", "_tagli")
    with open(os.path.join(HERE, "mapping.json"), encoding="utf-8") as f:
        mapping = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    unknown = sorted(set(mapping) - known_keys())
    if unknown:
        sys.exit(f"keys that are not node types: {unknown}")
    os.makedirs(DEST, exist_ok=True)
    for old in os.listdir(DEST):
        os.remove(os.path.join(DEST, old))
    for key, (sheet, pos) in sorted(mapping.items()):
        src = os.path.join(cuts, sheet, f"{int(pos):03d}.png")
        if not os.path.isfile(src):
            sys.exit(f"{key}: missing cut {src} (run split_sheets.py)")
        shutil.copyfile(src, os.path.join(DEST, f"{key}.png"))
    with open(os.path.join(DEST, "index.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(sorted(mapping), f, indent=1)
    review(sorted(mapping), os.path.join(cuts, "_installate.png"))
    missing = sorted(set(onto.TYPES) | set(onto.BASE_ICONS) - {"latin"})
    missing = [k for k in missing if k not in mapping]
    print(f"{len(mapping)} icons installed in {DEST}")
    print("node types still on the Font Awesome glyph:", ", ".join(missing) or "none")


def review(keys, path, per_row=10, cell=110):
    rows = (len(keys) + per_row - 1) // per_row
    sheet = Image.new("RGB", (per_row * cell, rows * (cell + 14)), "white")
    d = ImageDraw.Draw(sheet)
    for i, k in enumerate(keys):
        ic = Image.open(os.path.join(DEST, f"{k}.png")).resize((cell - 20, cell - 20))
        x, y = (i % per_row) * cell, (i // per_row) * (cell + 14)
        sheet.paste(ic, (x + 10, y + 2), ic)
        d.text((x + 4, y + cell - 12), k[:18], fill="red")
    sheet.save(path)


if __name__ == "__main__":
    main()
