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

"""Which accelerator ONNX Runtime uses: CUDA, or the CPU.

A lightweight module, without InsightFace, so both the face engine and the diarization
read it. Until 2026-09-07 the choice "CUDA or CPU" existed in two copies.

CoreML (Apple's GPU and Neural Engine) is present in onnxruntime on macOS but here it
**is not used**, after a measurement on 2026-09-07 with `buffalo_s` (onnxruntime 1.23.2):
the SCRFD detector does not run under CoreML (dynamic-shape outputs: "CoreML static
output shape and inferred shape have different ranks"), and the recogniser
`w600k_mbf` takes 17 ms per face against 6.8 ms on the CPU, with both ModelFormat
NeuralNetwork and MLProgram. `coreml_presente` only serves to explain this
in the interface.
"""
from __future__ import annotations

CUDA = "CUDAExecutionProvider"
COREML = "CoreMLExecutionProvider"
CPU = "CPUExecutionProvider"


def acceleratore(disponibili) -> str:
    """`cuda` if ONNX Runtime offers CUDA, otherwise `` (empty): the work runs on the CPU."""
    return "cuda" if CUDA in list(disponibili or []) else ""


def coreml_presente(disponibili) -> bool:
    """True on a Mac with the CoreML provider: present, and discarded (see above)."""
    return COREML in list(disponibili or [])


def precarica_cuda(ort, use_gpu: bool, log=print) -> None:
    """The CUDA and cuDNN libraries installed via pip (nvidia-* packages) must be loaded
    explicitly before the first session, otherwise on Windows the CUDA provider does
    not open ("cublasLt64_13.dll missing") and it silently falls back to the CPU.
    Until 2026-09-13 only the face engine did this: the voiceprints always ran
    on the CPU."""
    if use_gpu and hasattr(ort, "preload_dlls"):
        try:
            ort.preload_dlls()
        except Exception as e:  # noqa: BLE001 — without the preload, try anyway
            log(f"[acceleratore] preload CUDA: {e}")


def scegli_provider(use_gpu: bool, disponibili) -> tuple[list[str], int]:
    """The ONNX Runtime providers and the ctx_id for InsightFace (0 = GPU, -1 = CPU).

    With `use_gpu` and CUDA present, CUDA is taken with the CPU behind it; otherwise the
    CPU, without error."""
    if use_gpu and acceleratore(disponibili) == "cuda":
        return [CUDA, CPU], 0
    return [CPU], -1
