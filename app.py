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

"""Starts Quaesitor: python app.py (PORT and DATA_DIR in the environment).

The program lives in the quaesitor/ package; this file stays in the root so that
start.bat, the Linux launchers and the habit of `python app.py` keep working."""
from quaesitor.app import main

if __name__ == "__main__":
    main()
