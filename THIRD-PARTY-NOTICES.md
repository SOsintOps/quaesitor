# Third-party notices

Quaesitor, a fork of OSInt Graph by Andrea Cumini, is free software under the GNU GPL version 3 (see LICENSE and NOTICE).
It includes or uses the following third-party components. The full license
texts are in `static/licenses/` and can be read from the program itself
(link «Licenze» in the left panel).

| Component | Version | License | Copyright | Used for |
|---|---|---|---|---|
| [Cytoscape.js](https://js.cytoscape.org) | 3.30.2 | MIT | Copyright (c) 2016-2024, The Cytoscape Consortium | Graph rendering and interaction |
| [cytoscape-fcose](https://github.com/iVis-at-Bilkent/cytoscape-fcose) | 2.2.0 | MIT | Copyright (c) i-Vis Research Group, Bilkent University | Automatic node layout (organic layout) |
| [cose-base](https://github.com/iVis-at-Bilkent/cose-base) | 2.2.0 | MIT | Copyright (c) i-Vis Research Group, Bilkent University | Automatic node layout (organic layout) |
| [layout-base](https://github.com/iVis-at-Bilkent/layout-base) | 2.0.1 | MIT | Copyright (c) i-Vis Research Group, Bilkent University | Automatic node layout (organic layout) |
| [Font Awesome Free](https://fontawesome.com) | 6 | Icone CC BY 4.0, codice MIT | Fonticons, Inc. | Node type icons (person, phone, email…) |
| [Simple Icons](https://simpleicons.org) |  | CC0 1.0 (pubblico dominio); i loghi restano marchi dei rispettivi titolari | Simple Icons contributors | Social platform logos (Facebook, Instagram, Telegram…) |
| [Panchang (carattere del logo)](https://www.fontshare.com/fonts/panchang) |  | Fontshare Free Font License (solo contorni: il font non è distribuito) | Indian Type Foundry | Typeface of the original OSInt Graph logo (Quaesitor uses a provisional wordmark in a system font) |
| [Flask](https://pypi.org/project/Flask/) | 3.1.3 | BSD-3-Clause |  | Application web server |
| [Werkzeug](https://pypi.org/project/Werkzeug/) | 3.1.9 | BSD-3-Clause |  | Web server toolkit |
| [Jinja2](https://pypi.org/project/Jinja2/) | 3.1.6 | BSD-3-Clause |  | Page templates |
| [itsdangerous](https://pypi.org/project/itsdangerous/) | 2.2.0 | BSD-3-Clause |  | Data signing (Flask dependency) |
| [click](https://pypi.org/project/click/) | 8.5.0 | BSD-3-Clause |  | Command line (Flask dependency) |
| [MarkupSafe](https://pypi.org/project/MarkupSafe/) | 3.0.4 | BSD-3-Clause |  | Safe markup (Jinja2 dependency) |
| [blinker](https://pypi.org/project/blinker/) | 1.9.0 | MIT |  | Signals (Flask dependency) |
| [anyascii](https://pypi.org/project/anyascii/) | 0.3.3 | ISC |  | Transliteration to Latin characters |
| [pypdf](https://pypi.org/project/pypdf/) | 6.20.0 | BSD-3-Clause |  | Reading PDF sources |
| [pdfminer.six](https://pypi.org/project/pdfminer.six/) | 20260107 | MIT |  | PDF text extraction |
| [python-docx](https://pypi.org/project/python-docx/) | 1.2.0 | MIT |  | Reading Word documents |
| [openpyxl](https://pypi.org/project/openpyxl/) | 3.1.5 | MIT |  | Reading and importing Excel files |
| [xlrd](https://pypi.org/project/xlrd/) | 2.0.2 | BSD |  | Reading legacy Excel files (.xls) |
| [lxml](https://pypi.org/project/lxml/) | 6.1.3 | BSD-3-Clause |  | XML processing (python-docx dependency) |
| [et_xmlfile](https://pypi.org/project/et_xmlfile/) | 2.0.0 | MIT |  | XML writing (openpyxl dependency) |
| [Pillow](https://pypi.org/project/pillow/) | 12.3.0 | MIT-CMU (HPND) |  | Images: thumbnails and OCR |
| [pytesseract](https://pypi.org/project/pytesseract/) | 0.3.13 | Apache-2.0 |  | Bridge to Tesseract for OCR |
| [regex](https://pypi.org/project/regex/) | 2026.9.29 | Apache-2.0 |  | Unicode letter and combining-mark classes (\p{L}\p{M}) for identity keys of Indic, Thai and Japanese names (this fork) |
| [faster-whisper](https://pypi.org/project/faster-whisper/) | 1.2.1 | MIT |  | Transcription (Whisper on CTranslate2) (optional: requirements-audio.txt) (not bundled) |
| [CTranslate2](https://pypi.org/project/ctranslate2/) | 4.8.2 | MIT |  | Inference engine of Whisper and of the translation (optional: requirements-audio.txt) (not bundled) |
| [PyAV](https://pypi.org/project/av/) | 18.1.0 | BSD-3-Clause |  | Audio decoding of the videos (optional: requirements-audio.txt) (not bundled) |
| [ONNX Runtime](https://pypi.org/project/onnxruntime/) | 1.31.0 | MIT |  | Diarization models (optional: requirements-audio.txt) (not bundled) |
| [NumPy](https://pypi.org/project/numpy/) | 2.5.4 | BSD-3-Clause |  | Numerics of the diarization (optional: requirements-audio.txt) (not bundled) |
| [SciPy](https://pypi.org/project/scipy/) | 1.18.1 | BSD-3-Clause |  | Clustering of the voices (optional: requirements-audio.txt) (not bundled) |
| [SentencePiece](https://pypi.org/project/sentencepiece/) | 0.2.2 | Apache-2.0 |  | Tokenizer of the translation to Italian (optional: requirements-audio.txt) (not bundled) |
| [tokenizers](https://pypi.org/project/tokenizers/) | 0.23.3 | Apache-2.0 |  | Tokenizer of Whisper (optional: requirements-audio.txt) (not bundled) |
| [huggingface_hub](https://pypi.org/project/huggingface-hub/) | 2.2.0 | Apache-2.0 |  | Download of the Whisper models (optional: requirements-audio.txt) (not bundled) |
| [Whisper models (faster-whisper conversion)](https://huggingface.co/Systran) |  | MIT | OpenAI; conversion by SYSTRAN | Transcription models, downloaded on first use (not bundled) |
| [Silero VAD](https://github.com/snakers4/silero-vad) |  | MIT | Silero Team | Speech detection, downloaded on first use (not bundled) |
| [WeSpeaker speaker models (sherpa-onnx)](https://github.com/wenet-e2e/wespeaker) |  | Apache-2.0 (code); model terms to verify | WeSpeaker team; ONNX export by k2-fsa | Voiceprints, downloaded on first use (not bundled) |
| [Argos Translate package en_it](https://www.argosopentech.com) |  | to verify in the package metadata | Argos Open Technologies | Translation to Italian, downloaded on first use (not bundled) |
| [Python](https://www.python.org) | 3.11.9 | PSF License | Python Software Foundation | Interpreter embedded in the executable |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | 5.3.3 | Apache-2.0 | Tesseract contributors (Google, Ray Smith e altri) | Text recognition in images. Downloaded separately into tools/tesseract (not bundled) |
| [Leptonica](http://www.leptonica.org) | 1.83 | BSD-2-Clause | Copyright (C) 2001 Leptonica | Image library used by Tesseract (downloaded with it) (not bundled) |
| [PyInstaller](https://pyinstaller.org) |  | GPL-2.0 con eccezione per il bootloader | PyInstaller Development Team | Build tool only: not part of the distributed program (not bundled) |

Brand names and logos of the social platforms are trademarks of their respective
owners; they are used only to identify the platform of a profile. OSInt Graph is not
affiliated with, endorsed by or sponsored by any of them.
