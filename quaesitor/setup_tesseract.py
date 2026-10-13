# -*- coding: utf-8 -*-
# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Download Tesseract OCR into a LOCAL project folder (tools/tesseract),
without installing it system-wide. Used for OCR of the images in the sources.

    Windows:  downloads the official UB-Mannheim installer and extracts it locally
              (silent install into the tools/tesseract folder only).
    Linux/Mac: Tesseract is installed from the package manager; the script says so.

Usage:
    .venv\\Scripts\\python.exe -m quaesitor.setup_tesseract   (Windows)
    python -m quaesitor.setup_tesseract --url <URL_installer.exe>      (different version)

After the download the app finds Tesseract by itself (it looks in tools/tesseract)
and enables OCR: the Sources section will show "OCR active".

The same download can be started from the interface («Download Tesseract»
button in the Sources section): app.py uses setup_windows() from this module.
"""
# "Errare humanum est, perseverare autem diabolicum." (attributed to Seneca)
# To err is human; to persist in error is diabolical.
import os
import io
import sys
import shutil
import tempfile
import subprocess
import urllib.request

try:
    from .paths import BASE_DIR as ROOT
except ImportError:                       # run as a file, not with -m
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "tools", "tesseract")

# Official UB-Mannheim installer (Windows 64-bit build). You can give another
# one with --url if you prefer a different version.
DEFAULT_URL = os.environ.get("TESSERACT_URL") or (
    "https://digi.bib.uni-mannheim.de/tesseract/"
    "tesseract-ocr-w64-setup-5.3.3.20231005.exe")


def _arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def download(url, dst, progress=None):
    """Download 'url' into 'dst'. Calls 'progress(done, total)' if given,
    otherwise prints the progress to the terminal."""
    if progress is None:
        print(f"Downloading:\n  {url}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"})
    with urllib.request.urlopen(req, timeout=60) as r, io.open(dst, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = r.read(262144)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if progress is not None:
                progress(done, total)
            elif total:
                print(f"\r  {done // (1024*1024)} / {total // (1024*1024)} MB "
                      f"({done * 100 // total}%)", end="", flush=True)
    if progress is None:
        print()


def _find_7zip():
    for p in (r"C:\Program Files\7-Zip\7z.exe",
              r"C:\Program Files (x86)\7-Zip\7z.exe"):
        if os.path.isfile(p):
            return p
    return shutil.which("7z") or shutil.which("7za")


def setup_windows(url, dest=DEST, progress=None, stage=None):
    """Download and extract Tesseract into 'dest'. Returns the path of
    tesseract.exe; raises RuntimeError if it is not there at the end.
    'progress(done, total)' and 'stage(name)' ("download", "extract", "verify")
    are for the interface; without them, output goes to the terminal."""
    quiet = progress is not None or stage is not None
    say = (lambda *a, **k: None) if quiet else print
    tell = stage or (lambda name: None)
    os.makedirs(dest, exist_ok=True)
    tmp = os.path.join(tempfile.gettempdir(), "tesseract-setup.exe")
    tell("download")
    download(url, tmp, progress)
    size = os.path.getsize(tmp) / (1024 * 1024)
    say(f"Downloaded {size:.0f} MB.")
    exe = os.path.join(dest, "tesseract.exe")

    tell("extract")
    sevenzip = _find_7zip()
    if sevenzip:
        # EXTRACTION (no admin privileges): the NSIS installer is an archive,
        # 7-Zip extracts its files directly into the local folder.
        say(f"Extracting with 7-Zip into:\n  {dest}")
        subprocess.run([sevenzip, "x", tmp, f"-o{dest}", "-y"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # no 7-Zip: try the silent installer (it may ask for admin rights)
        say("7-Zip not found: using the silent installer "
            "(it may ask for administrator rights)…")
        subprocess.run([tmp, "/S", f"/D={dest}"])

    try:
        os.remove(tmp)
    except OSError:
        pass

    tell("verify")
    if not os.path.isfile(exe):
        raise RuntimeError(f"tesseract.exe not found in {dest}: "
                           "install 7-Zip (for the extraction without admin rights) and try again, "
                           "or run the installer by hand")
    ver = subprocess.run([exe, "--version"], capture_output=True, text=True)
    line = (ver.stdout or ver.stderr).splitlines()
    say("\nOK  ->  " + exe)
    if line:
        say(line[0])
    say("\nStart (or restart) the program: OCR will be on.")
    return exe


def setup_unix():
    print("On Linux/Mac install Tesseract with the package manager:\n")
    print("  Debian/Ubuntu:  sudo apt-get install tesseract-ocr tesseract-ocr-ita")
    print("  Fedora:         sudo dnf install tesseract")
    print("  macOS (brew):   brew install tesseract\n")
    print("Or put a 'tesseract' binary in:")
    print(f"  {DEST}")
    print("and the program will use it from there.")


def main():
    if shutil.which("tesseract"):
        print("Note: Tesseract is already in the system PATH; OCR already works.")
    url = _arg("--url", DEFAULT_URL)
    if os.name == "nt":
        try:
            setup_windows(url)
        except RuntimeError as e:
            sys.exit(str(e))
    else:
        setup_unix()


if __name__ == "__main__":
    main()
