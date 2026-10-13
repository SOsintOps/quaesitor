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

"""Where things are, in one place.

    BASE_DIR   the program folder: the repository root when run from source, the
               folder of the executable when frozen. The user's files live here:
               data/, sources/ (fonti/ before 1.8.0), tools/tesseract,
               chatbot.conf, services.conf, launcher.log.
    RES_DIR    the package resources: templates/, static/, generated/. The
               package folder from source; inside the PyInstaller bundle
               (sys._MEIPASS/quaesitor) when frozen.
"""
# "Omnia mea mecum porto." (Bias of Priene, in Cicero, Paradoxa Stoicorum)
# All that is mine I carry with me.
import os
import sys

FROZEN = bool(getattr(sys, "frozen", False))
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

if FROZEN:
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    RES_DIR = os.path.join(getattr(sys, "_MEIPASS", BASE_DIR), "quaesitor")
else:
    BASE_DIR = os.path.dirname(PACKAGE_DIR)
    RES_DIR = PACKAGE_DIR

GENERATED_DIR = os.path.join(RES_DIR, "generated")
