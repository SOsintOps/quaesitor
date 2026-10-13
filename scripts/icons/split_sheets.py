# -*- coding: utf-8 -*-
# Quaesitor - case graph for OSINT investigations
# Copyright (C) 2026 Ramingo (SOsintOps)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Cuts the icon sheets generated with ChatGPT / Gemini into single icons.

    .venv\\Scripts\\python.exe scripts\\icons\\split_sheets.py [<folder of the sheets>]

Every sheet is a grid of icons on a white background. The script finds the icons as
connected areas of non-white pixels (dilated, so that the parts of one icon stay
together), orders them by row and column, makes the white background transparent with
a flood fill from the border (the white inside an icon stays), and writes a square
128x128 PNG per icon into <sheets>/../_tagli/<sheet>/NNN.png, plus a numbered contact
sheet per source (<sheets>/_tagli/_contatto_<sheet>.png) used to label the icons.

A development tool: it needs numpy and scipy (requirements-audio.txt), the program
does not. The sheets live in docs/evaluation/icons/sheets, in the development repository
only (release_public.py leaves docs/evaluation/ out); scripts/icons/labels.json records what every
cut shows, scripts/icons/mapping.json which cut becomes the icon of which node type.
"""
# "Divide et impera." (attributed to Philip II of Macedon)
# Divide and rule.
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SIZE = 128
# columns x rows of every sheet, counted on the images: a sheet listed here is cut on
# a grid (the icons of dense sheets touch, and connected areas would merge them)
GRID = {
    "3d-finance-and-payment-icon-collection": (7, 5),
    "3d-investigation-and-finance-icon-grid": (12, 9),
    "comprehensive-forensic-and-finance-icon-library": (13, 10),
    "corporate-finance-and-compliance-icon-grid": (6, 8),
    "financial-card-icon-collection": (6, 6),
    "glossy-3d-icon-collection-grid": (13, 10),
    "glossy-3d-investigation-icon-atlas": (15, 11),
    "glossy-investigation-and-security-icon-grid": (6, 7),
    "mystery-and-investigation-icon-grid": (6, 6),
}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", os.path.splitext(name)[0].lower()).strip("-")


def foreground(rgb):
    """True where a pixel is not background (white or the light grey of shadows)."""
    a = rgb.astype(np.int16)
    light = a.min(axis=2)
    sat = a.max(axis=2) - a.min(axis=2)
    return (light < 225) | (sat > 28)


def boxes(mask, dilate):
    grown = ndimage.binary_dilation(mask, iterations=dilate)
    lab, n = ndimage.label(grown)
    out = []
    for sl in ndimage.find_objects(lab):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        out.append([x0, y0, x1, y1])
    if not out:
        return out
    area = [(b[2] - b[0]) * (b[3] - b[1]) for b in out]
    big = max(area)
    return [b for b, a in zip(out, area) if a > big * 0.04]     # dust and stray marks out


def order(bxs):
    """Row-major order: rows are clusters of box centres along y."""
    bxs = sorted(bxs, key=lambda b: (b[1] + b[3]) / 2)
    hs = sorted(b[3] - b[1] for b in bxs)
    gap = hs[len(hs) // 2] * 0.5
    rows, cur, last = [], [], None
    for b in bxs:
        cy = (b[1] + b[3]) / 2
        if last is not None and cy - last > gap:
            rows.append(cur)
            cur = []
        cur.append(b)
        last = cy if last is None else (last * (len(cur) - 1) + cy) / len(cur)
    if cur:
        rows.append(cur)
    return [sorted(r, key=lambda b: b[0]) for r in rows]


def transparent(img):
    """White background to alpha: flood fill of near-white pixels from the border."""
    rgb = np.asarray(img.convert("RGB")).astype(np.int16)
    near_white = (rgb.min(axis=2) > 232) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 22)
    lab, _ = ndimage.label(near_white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    bg = ndimage.binary_erosion(bg, iterations=1, border_value=1)   # keep the anti-aliased edge
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    alpha = ndimage.uniform_filter(alpha.astype(np.float32), 3).astype(np.uint8)
    out = np.dstack([np.asarray(img.convert("RGB")), alpha])
    return Image.fromarray(out, "RGBA")


def square(icon, size=SIZE, pad=0.06):
    w, h = icon.size
    side = int(max(w, h) * (1 + 2 * pad))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(icon, ((side - w) // 2, (side - h) // 2), icon)
    return canvas.resize((size, size), Image.LANCZOS)


def cuts_at(profile, n, length):
    """n-1 cut positions: the emptiest point within a window around each expected one."""
    step = length / n
    out = [0]
    for i in range(1, n):
        c = int(i * step)
        w = int(step * 0.3)
        lo, hi = max(1, c - w), min(length - 1, c + w)
        out.append(lo + int(np.argmin(profile[lo:hi])))
    out.append(length)
    return out


def grid_rows(mask, cols, rows):
    """Boxes by grid: row cuts on the whole sheet, column cuts within every row band,
    then the box shrunk to the foreground inside its cell."""
    h, w = mask.shape
    ys = cuts_at(ndimage.uniform_filter1d(mask.sum(axis=1).astype(float), 9), rows, h)
    out = []
    for r in range(rows):
        band = mask[ys[r]:ys[r + 1]]
        xs = cuts_at(ndimage.uniform_filter1d(band.sum(axis=0).astype(float), 9), cols, w)
        row = []
        for c in range(cols):
            # the cell, widened by 25% on every side: a whole icon fits even when the
            # grid drifts; inside it only the connected area nearest to the centre counts
            cx0, cx1, cy0, cy1 = xs[c], xs[c + 1], ys[r], ys[r + 1]
            mx, my = int((cx1 - cx0) * 0.25), int((cy1 - cy0) * 0.25)
            X0, X1, Y0, Y1 = max(0, cx0 - mx), min(w, cx1 + mx), max(0, cy0 - my), min(h, cy1 + my)
            sub = ndimage.binary_dilation(mask[Y0:Y1, X0:X1], iterations=3)
            lab, n = ndimage.label(sub)
            if n == 0:
                continue
            # every area whose centre falls inside the cell belongs to its icon (three
            # cartridges, a pill and a leaf); the slivers of the neighbours stay out
            parts = []
            for sl in ndimage.find_objects(lab):
                size = (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start)
                yy, xx = Y0 + (sl[0].start + sl[0].stop) / 2, X0 + (sl[1].start + sl[1].stop) / 2
                if size >= (cx1 - cx0) * (cy1 - cy0) * 0.01 and cx0 <= xx < cx1 and cy0 <= yy < cy1:
                    parts.append(sl)
            if not parts:
                continue
            best = (slice(min(p_[0].start for p_ in parts), max(p_[0].stop for p_ in parts)),
                    slice(min(p_[1].start for p_ in parts), max(p_[1].stop for p_ in parts)))
            row.append([X0 + best[1].start, Y0 + best[0].start, X0 + best[1].stop, Y0 + best[0].stop])
        out.append(row)
    return out


def split(path, out_root, dilate=6):
    img = Image.open(path).convert("RGB")
    rgb = np.asarray(img)
    name = slug(os.path.basename(path))
    if name in GRID:
        rows = grid_rows(foreground(rgb), *GRID[name])
    else:
        rows = order(boxes(foreground(rgb), dilate))
    dest = os.path.join(out_root, name)
    os.makedirs(dest, exist_ok=True)
    cuts, k = [], 0
    for r, row in enumerate(rows):
        for c, (x0, y0, x1, y1) in enumerate(row):
            k += 1
            m = 4
            crop = img.crop((max(0, x0 - m), max(0, y0 - m), min(img.width, x1 + m), min(img.height, y1 + m)))
            square(transparent(crop)).save(os.path.join(dest, f"{k:03d}.png"), optimize=True)
            cuts.append({"n": k, "row": r + 1, "col": c + 1, "box": [x0, y0, x1, y1]})
    contact(dest, cuts, os.path.join(out_root, f"_contatto_{name}.png"))
    return name, [len(r) for r in rows], cuts


def contact(dest, cuts, path, per_row=12, cell=96):
    n = len(cuts)
    rows = (n + per_row - 1) // per_row
    sheet = Image.new("RGB", (per_row * cell, rows * (cell + 14)), "white")
    d = ImageDraw.Draw(sheet)
    for i, cut in enumerate(cuts):
        ic = Image.open(os.path.join(dest, f"{cut['n']:03d}.png")).resize((cell - 8, cell - 8))
        x, y = (i % per_row) * cell, (i // per_row) * (cell + 14)
        sheet.paste(ic, (x + 4, y + 2), ic)
        d.text((x + 4, y + cell - 4), f"{cut['n']}", fill="red")
    sheet.save(path)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "evaluation", "icons", "sheets")
    out_root = os.path.join(os.path.dirname(os.path.abspath(src)), "_tagli")
    os.makedirs(out_root, exist_ok=True)
    report = {}
    for f in sorted(os.listdir(src)):
        if f.lower().endswith(".png"):
            name, per_row, cuts = split(os.path.join(src, f), out_root)
            report[name] = {"file": f, "per_row": per_row, "cuts": len(cuts)}
            print(f"{name}: {len(cuts)} icons, per row {per_row}")
    with open(os.path.join(out_root, "_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
