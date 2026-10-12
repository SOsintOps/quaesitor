# -*- coding: utf-8 -*-
# Quaesitor - case graph for OSINT investigations
# Copyright (C) 2026 Ramingo (SOsintOps)
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Follow the Money bundles: a zip with the entities and the files they cite.

Cognitor exports a case as a `.cognitor.zip` bundle:

    manifest.json        {"format": "cognitor-ftm-bundle", "version": 1, "case_id",
                          "case_name", "dataset", "counts", "files": {path: sha256}}
    entities.ftm.json    Follow the Money entities, one per line
    media/<sha256>.jpg   the images cited by Image.fileName
    transcripts/<id>.txt the transcript of every Video, named after its FtM id

This module reads a bundle without trusting it: every file is checked against the
sha256 of the manifest, names outside media/ and transcripts/ are refused, an image
must be an image (magic bytes) and stay within the size limit of an upload.
"""
# "Nosce te ipsum." (Delphic maxim)
# Know thyself.
import hashlib
import io
import json
import os
import re
import zipfile

FORMAT = "cognitor-ftm-bundle"
ENTITIES = "entities.ftm.json"
MANIFEST = "manifest.json"
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_TRANSCRIPT_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024        # 2 GB uncompressed (decision of 2026-10-12)
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
_NAME = re.compile(r"^(media/[A-Za-z0-9._-]+|transcripts/[A-Za-z0-9._-]+\.txt)$")


class BundleError(ValueError):
    pass


def sniff_image(blob):
    """Extension of an image from its first bytes, or None."""
    if blob[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if blob[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return ".webp"
    if blob[:2] == b"BM":
        return ".bmp"
    return None


def _open(src):
    """A ZipFile from a path or from bytes; None when it is not a zip."""
    try:
        if isinstance(src, (bytes, bytearray)):
            return zipfile.ZipFile(io.BytesIO(bytes(src)))
        return zipfile.ZipFile(str(src))
    except (zipfile.BadZipFile, OSError):
        return None


def is_bundle(src):
    """True when src (path or bytes) is a zip with a Cognitor manifest."""
    z = _open(src)
    if z is None:
        return False
    with z:
        try:
            man = json.loads(z.read(MANIFEST).decode("utf-8"))
        except (KeyError, ValueError):
            return False
    return isinstance(man, dict) and man.get("format") == FORMAT


class Bundle:
    """An opened, verified bundle. Use as a context manager."""

    def __init__(self, src):
        self.z = _open(src)
        if self.z is None:
            raise BundleError("not a zip file")
        try:
            self.manifest = json.loads(self.z.read(MANIFEST).decode("utf-8"))
        except (KeyError, ValueError):
            self.z.close()
            raise BundleError("manifest.json missing or unreadable")
        if self.manifest.get("format") != FORMAT:
            self.z.close()
            raise BundleError("unknown bundle format")
        files = self.manifest.get("files") or {}
        if ENTITIES not in files:
            self.z.close()
            raise BundleError("entities.ftm.json missing from the manifest")
        names = set(self.z.namelist())
        total = 0
        for info in self.z.infolist():
            total += info.file_size
            if info.filename in (MANIFEST, ENTITIES):
                continue
            if not _NAME.match(info.filename) or ".." in info.filename:
                self.z.close()
                raise BundleError(f"unexpected file in the bundle: {info.filename[:80]}")
        if total > MAX_TOTAL_BYTES:
            self.z.close()
            raise BundleError("bundle too large (max 2 GB uncompressed)")
        missing = [n for n in files if n not in names]
        if missing:
            self.z.close()
            raise BundleError(f"file listed but missing: {missing[0][:80]}")
        self.files = files
        self.media = sorted(n for n in files if n.startswith("media/"))
        self.transcripts = sorted(n for n in files if n.startswith("transcripts/"))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        if self.z is not None:
            self.z.close()
            self.z = None

    def read(self, name, limit=None):
        """Bytes of a listed file, verified against the manifest sha256."""
        if name not in self.files:
            raise BundleError(f"file not listed in the manifest: {name[:80]}")
        info = self.z.getinfo(name)
        if limit and info.file_size > limit:
            raise BundleError(f"file too large: {name[:80]}")
        data = self.z.read(name)
        if hashlib.sha256(data).hexdigest() != str(self.files[name]).lower():
            raise BundleError(f"sha256 mismatch: {name[:80]}")
        return data

    def entities_blob(self):
        return self.read(ENTITIES)

    @property
    def case_key(self):
        """A folder name for the case of origin (letters, digits, - and _)."""
        raw = str(self.manifest.get("case_id") or self.manifest.get("case_name") or "case")
        return re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_")[:80] or "case"

    def summary(self):
        m = self.manifest
        return {"bundle": True, "case_id": m.get("case_id"), "case_name": m.get("case_name"),
                "dataset": m.get("dataset"), "exported_at": m.get("exported_at"),
                "images": len(self.media), "transcripts": len(self.transcripts),
                "left_out": m.get("left_out") or [], "counts": m.get("counts") or {}}

    def install_media(self, data_dir, media_dirname="media"):
        """Copies the images under <data_dir>/<media>/cognitor/<case>/ and returns
        {fileName in the bundle: path relative to data_dir}. Files already there with
        the same content are not written again."""
        rel_dir = f"{media_dirname}/cognitor/{self.case_key}"
        dest = os.path.join(data_dir, *rel_dir.split("/"))
        out, refused = {}, []
        for name in self.media:
            try:
                blob = self.read(name, MAX_IMAGE_BYTES)
            except BundleError:
                refused.append(name)
                continue
            ext = sniff_image(blob)
            if not ext:
                refused.append(name)
                continue
            base = os.path.splitext(os.path.basename(name))[0][:64] + ext
            os.makedirs(dest, exist_ok=True)
            path = os.path.join(dest, base)
            if not (os.path.isfile(path) and os.path.getsize(path) == len(blob)):
                with open(path, "wb") as f:
                    f.write(blob)
            out[name] = f"{rel_dir}/{base}"
        self.refused = refused
        return out

    def install_transcripts(self, folder):
        """Copies the transcripts under <folder>/cognitor/<case>/; returns the paths."""
        dest = os.path.join(folder, "cognitor", self.case_key)
        paths = []
        for name in self.transcripts:
            data = self.read(name, MAX_TRANSCRIPT_BYTES)
            os.makedirs(dest, exist_ok=True)
            path = os.path.join(dest, os.path.basename(name))
            with open(path, "wb") as f:
                f.write(data)
            paths.append(path)
        return paths
