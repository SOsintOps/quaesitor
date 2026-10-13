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

"""Builds app.py (the Quaesitor server, package quaesitor/) into a single onefile executable
with PyInstaller and prepares in dist/ the folder ready to be distributed.

Run it with the SAME interpreter as the project (the venv), because it uses the libraries
installed there:

    Windows:   .venv\\Scripts\\python.exe -m pip install -r requirements.txt --group build
               .venv\\Scripts\\python.exe scripts\\build_app.py
    Linux:     .venv/bin/python scripts/build_app.py

What it does:
  * embeds the app's resources in the executable: quaesitor/templates/,
    quaesitor/static/ (page, scripts, styles, logo, icons and the licence
    texts) and quaesitor/generated/ (the Follow the Money schema);
  * uses quaesitor/static/icon.ico as the executable's icon (Windows);
  * checks that the required libraries are installed (requirements.txt)
    and includes the PyICU and anyascii transliteration engines if present;
  * does NOT embed the data: the data/ folder (cases), chatbot.conf and the
    tools/tesseract folder stay EXTERNAL, next to the executable. On the
    first start the program creates data/ and asks to create a case;
  * copies next to the executable the files that must be distributed with it:
    LICENSE, NOTICE, THIRD-PARTY-NOTICES.md e chatbot.conf.example.

Options:
  --name NAME   name of the executable (default: Quaesitor)
  --noconsole   hides the console window (browser only). By default the
                console stays visible: it shows the address, the logs and is the way
                to stop the server (Ctrl+C or closing the window).
  --keep        does not delete build/ and the .spec file at the end

Result:     dist/Quaesitor.exe  (Windows)   /   dist/Quaesitor  (Linux)
            + LICENSE, NOTICE, THIRD-PARTY-NOTICES.md, chatbot.conf.example

Using the executable:
  double-click it (or launch it from a terminal): the server starts and the
  browser opens on http://127.0.0.1:5000. The data are saved in data/ next to
  the executable. Tesseract (OCR) is downloaded from the app, section «Fonti».

AI (optional):
  the chatbot is configured from the app (panel «Intelligenza artificiale») and
  the configuration is kept in chatbot.conf, next to the executable (see
  chatbot.conf.example). With the «AI attiva» switch off the app does not
  connect to anything and only uses the local transliteration.
"""
# "Concordia res parvae crescunt, discordia maximae dilabuntur." (Sallust, Bellum Iugurthinum)
# Through concord small things grow; through discord the greatest fall apart.
import importlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the repository root
SRC = os.path.join(ROOT, "app.py")
SEP = os.pathsep                      # ';' on Windows, ':' on Linux/Mac
ICON = os.path.join(ROOT, "quaesitor", "static", "icon.ico")

# files to distribute NEXT TO the executable
DIST_FILES = ["LICENSE", "NOTICE", "THIRD-PARTY-NOTICES.md", "chatbot.conf.example", "services.conf.example"]

# required libraries (requirements.txt): module to import -> pip package
REQUIRED = {
    "flask": "Flask", "anyascii": "anyascii", "pdfminer": "pdfminer.six",
    "pypdf": "pypdf", "docx": "python-docx", "openpyxl": "openpyxl", "xlrd": "xlrd",
    "PIL": "Pillow", "pytesseract": "pytesseract",
}
# imported lazily by app.py / sources.py: PyInstaller does not see them by itself
HIDDEN = ["docx", "openpyxl", "xlrd", "pypdf", "pytesseract", "PIL.Image",
          "pdfminer.high_level", "quaesitor.setup_tesseract", "tkinter", "tkinter.filedialog",
          # 1.6.0: Cognitor bundles and video transcription (the audio packages of
          # requirements-audio.txt enter the executable only if installed when building)
          "quaesitor.ftm_bundle", "quaesitor.transcripts", "quaesitor.audio",
          "quaesitor.audio.transcribe", "quaesitor.audio.diarize", "quaesitor.audio.voices",
          "quaesitor.audio.translate", "quaesitor.audio.accelerator",
          "quaesitor.generated.ontology_ftm"]


def check_requirements():
    missing = []
    for mod, pkg in REQUIRED.items():
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(pkg)
    if missing:
        sys.exit("Mancano librerie necessarie: " + ", ".join(missing) + "\n"
                 f'Installale con:\n    "{sys.executable}" -m pip install -r requirements.txt')
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.exit("PyInstaller non installato in questo interprete.\n"
                 f'Installalo con:\n    "{sys.executable}" -m pip install --group build')
    for name in DIST_FILES:
        if not os.path.isfile(os.path.join(ROOT, name)):
            sys.exit(f"Manca il file {name}: va distribuito insieme all'eseguibile.")


def main():
    argv = sys.argv[1:]
    noconsole = "--noconsole" in argv
    keep = "--keep" in argv
    name = "Quaesitor"
    if "--name" in argv:
        i = argv.index("--name")
        if i + 1 < len(argv):
            name = argv[i + 1]

    check_requirements()

    args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", name,
        "--noconfirm",
        "--clean",
        # app resources inside the executable (relative paths: it runs from ROOT)
        "--add-data", f"quaesitor/templates{SEP}quaesitor/templates",
        "--add-data", f"quaesitor/static{SEP}quaesitor/static",
        "--add-data", f"quaesitor/generated/ftm_schema.json{SEP}quaesitor/generated",
        # the console shows the logs and is the way to stop the server;
        # --noconsole hides it (the option only matters on Windows)
        ("--windowed" if noconsole else "--console"),
    ]
    if os.path.isfile(ICON):
        args += ["--icon", ICON]
    else:
        print("(nota: quaesitor/static/icon.ico non trovato, l'eseguibile avrà l'icona predefinita)")

    # transliteration engines, included only if installed
    for pkg in ("icu", "anyascii"):
        try:
            importlib.import_module(pkg)
            args += ["--collect-all", pkg]
        except Exception:
            print(f"(nota: {pkg} non installato, lo salto)")

    for mod in HIDDEN:
        args += ["--hidden-import", mod]

    args.append(SRC)

    print(">> " + " ".join(f'"{a}"' if " " in a else a for a in args))
    r = subprocess.run(args, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"PyInstaller ha restituito errore {r.returncode}")

    exe = name + (".exe" if os.name == "nt" else "")
    dist = os.path.join(ROOT, "dist")
    out = os.path.join(dist, exe)
    if not os.path.isfile(out):
        sys.exit("Compilazione finita ma non trovo l'eseguibile in dist/")

    # legal files and example configuration next to the executable
    for fn in DIST_FILES:
        shutil.copy2(os.path.join(ROOT, fn), os.path.join(dist, fn))

    size_mb = os.path.getsize(out) / (1024 * 1024)
    print(f"\nOK  ->  {out}   ({size_mb:.1f} MB)")
    print("In dist/ ci sono anche: " + ", ".join(DIST_FILES))
    print("Da distribuire insieme. Al primo avvio il programma crea data/ e chiede un caso.")

    if not keep:
        shutil.rmtree(os.path.join(ROOT, "build"), ignore_errors=True)
        spec = os.path.join(ROOT, name + ".spec")
        if os.path.isfile(spec):
            os.remove(spec)
        print("Puliti build/ e il file .spec (usa --keep per conservarli).")


if __name__ == "__main__":
    main()
