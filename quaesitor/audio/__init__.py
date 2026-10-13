# -*- coding: utf-8 -*-
# Quaesitor - case graph for OSINT investigations
# Copyright (C) 2026 Ramingo (SOsintOps)
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Originally part of Cognitor (https://github.com/SOsintOps/cognitor), commit fb93e01,
# released by its holder under the GPL as part of Quaesitor (point 6 of the Cognitor
# licence, 2026-10-12). See audio/README.md for the changes made in the copy.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Video transcription, optional: faster-whisper, diarization (Silero VAD + WeSpeaker on
onnxruntime) and translation (Argos packages via ctranslate2).

The packages are in requirements-audio.txt and are not required to run Quaesitor:
`available()` says whether they are installed, and why not.
"""
import importlib.util

PACKAGES = {"faster_whisper": "faster-whisper", "numpy": "numpy", "scipy": "scipy",
            "onnxruntime": "onnxruntime", "sentencepiece": "sentencepiece"}


def missing_packages():
    """pip names of the packages that are not installed."""
    return [pip for mod, pip in PACKAGES.items() if importlib.util.find_spec(mod) is None]


def available():
    """(True, "") when the transcription can run, else (False, reason)."""
    miss = missing_packages()
    if miss:
        return False, "missing packages: " + ", ".join(miss)
    return True, ""
