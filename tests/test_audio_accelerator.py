"""Copied from Cognitor (tests/test_acceleratore.py, commit fb93e01) with the modules in audio/."""
import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

"""La scelta dell'acceleratore: CUDA, altrimenti CPU. CoreML si segnala, non si usa."""
import pytest

from quaesitor.audio import accelerator as A

CUDA, COREML, CPU, AZURE = A.CUDA, A.COREML, A.CPU, "AzureExecutionProvider"


@pytest.mark.parametrize("disponibili, atteso", [
    ([CUDA, CPU], "cuda"),
    ([CUDA, COREML, CPU], "cuda"),
    ([COREML, AZURE, CPU], ""),                 # a Mac with onnxruntime 1.23
    ([CPU], ""),
    ([], ""),
    (None, ""),
])
def test_acceleratore(disponibili, atteso):
    assert A.acceleratore(disponibili) == atteso


def test_coreml_si_riconosce_ma_non_si_sceglie():
    """Measurement of 2026-09-07: the SCRFD detector does not run under CoreML and the
    recogniser takes 17 ms against 6.8 ms on the CPU."""
    assert A.coreml_presente([COREML, AZURE, CPU]) is True
    assert A.coreml_presente([CPU]) is False
    assert A.scegli_provider(True, [COREML, AZURE, CPU]) == ([CPU], -1)


def test_cuda_resta_come_prima():
    assert A.scegli_provider(True, [CUDA, CPU]) == ([CUDA, CPU], 0)


@pytest.mark.parametrize("disponibili", [[CPU], [COREML, CPU], [CUDA, CPU]])
def test_senza_richiesta_lavora_la_cpu(disponibili):
    assert A.scegli_provider(False, disponibili) == ([CPU], -1)


def test_senza_acceleratore_la_richiesta_ricade_sulla_cpu():
    assert A.scegli_provider(True, [CPU]) == ([CPU], -1)
