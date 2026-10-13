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

"""Quale acceleratore usa ONNX Runtime: CUDA, oppure la CPU.

Un modulo leggero, senza InsightFace, così lo leggono sia il motore dei volti sia
la diarizzazione. Fino al 2026-09-07 la scelta era «CUDA o CPU» in due copie.

CoreML (GPU e Neural Engine di Apple) è presente in onnxruntime su macOS ma qui
**non si usa**, per una misura del 2026-09-07 su `buffalo_s` (onnxruntime 1.23.2):
il rilevatore SCRFD non gira sotto CoreML (uscite a forma dinamica: «CoreML static
output shape and inferred shape have different ranks»), e il riconoscitore
`w600k_mbf` impiega 17 ms per volto contro 6,8 ms sulla CPU, sia con ModelFormat
NeuralNetwork sia con MLProgram. `coreml_presente` serve solo a spiegarlo
nell'interfaccia.
"""
from __future__ import annotations

CUDA = "CUDAExecutionProvider"
COREML = "CoreMLExecutionProvider"
CPU = "CPUExecutionProvider"


def acceleratore(disponibili) -> str:
    """`cuda` se ONNX Runtime offre CUDA, altrimenti `` (vuoto): si lavora sulla CPU."""
    return "cuda" if CUDA in list(disponibili or []) else ""


def coreml_presente(disponibili) -> bool:
    """True su un Mac con il provider CoreML: presente, e scartato (vedi sopra)."""
    return COREML in list(disponibili or [])


def precarica_cuda(ort, use_gpu: bool, log=print) -> None:
    """Le librerie CUDA e cuDNN installate via pip (pacchetti nvidia-*) vanno caricate in
    modo esplicito prima della prima sessione, altrimenti su Windows il provider CUDA
    non si apre («cublasLt64_13.dll mancante») e si ricade sulla CPU in silenzio.
    Fino al 2026-09-13 lo faceva solo il motore dei volti: le impronte vocali giravano
    sempre sulla CPU."""
    if use_gpu and hasattr(ort, "preload_dlls"):
        try:
            ort.preload_dlls()
        except Exception as e:  # noqa: BLE001 — senza precarico si prova lo stesso
            log(f"[acceleratore] preload CUDA: {e}")


def scegli_provider(use_gpu: bool, disponibili) -> tuple[list[str], int]:
    """I provider ONNX Runtime e il ctx_id per InsightFace (0 = GPU, -1 = CPU).

    Con `use_gpu` e CUDA presente si prende CUDA con la CPU dietro; altrimenti la
    CPU, senza errore."""
    if use_gpu and acceleratore(disponibili) == "cuda":
        return [CUDA, CPU], 0
    return [CPU], -1
