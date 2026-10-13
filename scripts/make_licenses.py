# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Collects the licences of ALL the components of the program in quaesitor/static/licenses/
(one text file per licence + index.json) and writes THIRD-PARTY-NOTICES.md.

The texts are taken from the Python packages installed in the venv, from the files in
quaesitor/static/vendor and from the Python interpreter, so they are the real ones of the
versions in use. Run it again whenever a dependency is updated:

    .venv\\Scripts\\python.exe scripts\\make_licenses.py
"""
# "Manus manum lavat." (Seneca, Apocolocyntosis)
# One hand washes the other.
import io
import json
import os
import re
import sys
from importlib.metadata import distribution, PackageNotFoundError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "quaesitor")          # templates/ and static/ of the program
OUT = os.path.join(RES, "static", "licenses")
os.makedirs(OUT, exist_ok=True)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def wr(name, text):
    with io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text.strip("\n") + "\n")
    return name


def pkg_license(name):
    """Licence text from the dist-info of the installed package."""
    try:
        d = distribution(name)
    except PackageNotFoundError:
        sys.exit(f"{name} non installato nel venv: pip install {name}")
    cands = [f for f in (d.files or [])
             if re.search(r"licen[cs]e|copying", str(f), re.I) and "ICON" not in str(f)]
    cands.sort(key=lambda f: (0 if str(f).lower().endswith(("licence.rst", "license.txt", "license")) else 1, len(str(f))))
    if not cands:
        sys.exit(f"{name}: nessun file di licenza nel pacchetto")
    return d.version, rd(str(d.locate_file(cands[0])))


MIT = """MIT License

Copyright (c) {holder}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

entries = []


def add(id_, name, version, license_, holder, url, role_it, role_en, file, group, bundled=True):
    entries.append({"id": id_, "name": name, "version": version, "license": license_,
                    "copyright": holder, "url": url, "role": {"it": role_it, "en": role_en},
                    "file": file, "group": group, "bundled": bundled})


# ------------------------------------------------------------ the program ---
add("osint-graph", "Quaesitor (fork of OSInt Graph)", "", "GNU GPL v3 with additional terms (attribution, name and logo)",
    "Copyright (C) 2025-2026 Andrea Cumini", "https://www.osintinfo.net",
    "Il programma: licenza e termini aggiuntivi", "The program: license and additional terms",
    wr("NOTICE.txt", rd(os.path.join(ROOT, "NOTICE"))), "program")
add("gpl-3.0", "GNU General Public License", "version 3", "GPL-3.0",
    "Free Software Foundation", "https://www.gnu.org/licenses/gpl-3.0.html",
    "Testo integrale della licenza del programma", "Full text of the program's license",
    wr("GPL-3.0.txt", rd(os.path.join(ROOT, "LICENSE"))), "program")

# ------------------------------------------------ JavaScript libraries -----
cy_src = rd(os.path.join(RES, "static", "vendor", "cytoscape.min.js"))
m = re.match(r"/\*\*(.*?)\*/", cy_src, re.S)
cy_text = re.sub(r"^\s*\* ?", "", m.group(1), flags=re.M).strip() if m else MIT.format(holder="2016-2024, The Cytoscape Consortium")
cy_ver = re.search(r"cytoscape\s+([\d.]+)", rd(os.path.join(RES, "templates", "index.html")))
add("cytoscape", "Cytoscape.js", cy_ver.group(1) if cy_ver else "", "MIT",
    "Copyright (c) 2016-2024, The Cytoscape Consortium", "https://js.cytoscape.org",
    "Disegno e interazione del grafo", "Graph rendering and interaction",
    wr("cytoscape.txt", cy_text), "js")
for id_, name, ver in (("cytoscape-fcose", "cytoscape-fcose", "2.2.0"),
                       ("cose-base", "cose-base", "2.2.0"),
                       ("layout-base", "layout-base", "2.0.1")):
    add(id_, name, ver, "MIT", "Copyright (c) i-Vis Research Group, Bilkent University",
        f"https://github.com/iVis-at-Bilkent/{id_}",
        "Disposizione automatica dei nodi (layout organico)", "Automatic node layout (organic layout)",
        wr(f"{id_}.txt", MIT.format(holder="i-Vis Research Group, Bilkent University")), "js")

for id_, name, ver, copy, holder, url in (
        ("cytoscape-dagre", "cytoscape-dagre", "2.5.0", "Copyright (c) 2016-2018, 2020, 2022, The Cytoscape Consortium", "2016-2018, 2020, 2022, The Cytoscape Consortium",
         "https://github.com/cytoscape/cytoscape.js-dagre"),
        ("dagre", "dagre", "0.8.5", "Copyright (c) 2012-2014 Chris Pettitt", "2012-2014 Chris Pettitt",
         "https://github.com/dagrejs/dagre"),
        ):
    add(id_, name, ver, "MIT", copy, url,
        "Disposizione ad albero per livelli, secondo le frecce", "Tree layout by levels, following the arrows",
        wr(f"{id_}.txt", MIT.format(holder=holder)), "js")

# ---------------------------------------------------------- icons and font ---
add("font-awesome", "Font Awesome Free", "6", "Icone CC BY 4.0, codice MIT",
    "Fonticons, Inc.", "https://fontawesome.com",
    "Icone di ripiego dei tipi di nodo e dell'interfaccia", "Fallback node type icons and interface icons",
    wr("font-awesome.txt", rd(os.path.join(RES, "static", "vendor", "fa", "LICENSE.txt"))), "assets")
add("entity-icons", "Quaesitor node icons", "1.7.1", "GPL-3.0-or-later (as the program)",
    "Ramingo (SOsintOps)", "https://github.com/SOsintOps/quaesitor",
    "Icone a colori dei tipi di nodo, generate con ChatGPT e Gemini (quaesitor/static/icons/entities)",
    "Colour node type icons, generated with ChatGPT and Gemini (quaesitor/static/icons/entities)",
    wr("entity-icons.txt", """Quaesitor node icons - quaesitor/static/icons/entities/

Colour icons of the node types, generated in October 2026 with ChatGPT and Gemini
from a prompt written by the maintainer of the fork, cut and assigned with the
scripts in scripts/icons/. They are part of Quaesitor and are distributed under
the same licence as the program (GNU GPL v3 or later). See the FAQ, "Where do the
node icons come from?".
"""), "assets")
add("simple-icons", "Simple Icons", "", "CC0 1.0 (pubblico dominio); i loghi restano marchi dei rispettivi titolari",
    "Simple Icons contributors", "https://simpleicons.org",
    "Loghi delle piattaforme social (Facebook, Instagram, Telegram…)", "Social platform logos (Facebook, Instagram, Telegram…)",
    wr("simple-icons.txt", """Simple Icons - https://simpleicons.org

The SVG icons are released under the CC0 1.0 Universal Public Domain
Dedication <https://creativecommons.org/publicdomain/zero/1.0/>: to the
extent possible under law, the authors have waived all copyright and related
rights to the icons.

The brands' names and logos remain the property and trademarks of their
respective owners. OSInt Graph uses them only to identify the platform a
profile belongs to. OSInt Graph is not affiliated with, endorsed by or
sponsored by any of these companies.
"""), "assets")
add("panchang", "Panchang (carattere del logo)", "", "Fontshare Free Font License (solo contorni: il font non è distribuito)",
    "Indian Type Foundry", "https://www.fontshare.com/fonts/panchang",
    "Carattere del logo originale di OSInt Graph (Quaesitor ha un logo proprio, in Bodoni Moda)", "Typeface of the original OSInt Graph logo (Quaesitor has a logo of its own, set in Bodoni Moda)",
    wr("panchang.txt", """Panchang - a typeface by Indian Type Foundry (ITF)
https://www.fontshare.com/fonts/panchang

The logo and the icon of OSInt Graph (quaesitor/static/logo.svg, quaesitor/static/icon.svg and
the same artwork inside the pages) are vector outlines set in Panchang. They
contain outlines only: the font files are NOT distributed with this program.
Panchang is available from Fontshare under the Fontshare Free Font License,
which allows its use in logos and graphics but not the redistribution of the
font files. ITF owns the trademarks and the copyright of the typeface.
"""), "assets")

add("bodoni-moda", "Bodoni Moda (carattere del logo)", "", "SIL Open Font License 1.1 (solo contorni: il font non è distribuito)",
    "The Bodoni Moda Project Authors", "https://github.com/indestructible-type/Bodoni",
    "Carattere della parola Quaesitor nel logo, convertita in tracciati", "Typeface of the word Quaesitor in the logo, converted to outlines",
    wr("bodoni-moda.txt", """Bodoni Moda - https://github.com/indestructible-type/Bodoni
The word "Quaesitor" in the logo (quaesitor/static/logo.svg, quaesitor/static/logo-light.svg and the
same artwork inside the pages) is set in Bodoni Moda and converted to outlines:
the font files are not distributed with this program.

Copyright 2020 The Bodoni Moda Project Authors (https://github.com/indestructible-type/Bodoni)

This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is copied below, and is also available with a FAQ at:
https://openfontlicense.org/


-----------------------------------------------------------
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
-----------------------------------------------------------

PREAMBLE
The goals of the Open Font License (OFL) are to stimulate worldwide
development of collaborative font projects, to support the font creation
efforts of academic and linguistic communities, and to provide a free and
open framework in which fonts may be shared and improved in partnership
with others.

The OFL allows the licensed fonts to be used, studied, modified and
redistributed freely as long as they are not sold by themselves. The
fonts, including any derivative works, can be bundled, embedded, 
redistributed and/or sold with any software provided that any reserved
names are not used by derivative works. The fonts and derivatives,
however, cannot be released under any other type of license. The
requirement for fonts to remain under this license does not apply
to any document created using the fonts or their derivatives.

DEFINITIONS
"Font Software" refers to the set of files released by the Copyright
Holder(s) under this license and clearly marked as such. This may
include source files, build scripts and documentation.

"Reserved Font Name" refers to any names specified as such after the
copyright statement(s).

"Original Version" refers to the collection of Font Software components as
distributed by the Copyright Holder(s).

"Modified Version" refers to any derivative made by adding to, deleting,
or substituting -- in part or in whole -- any of the components of the
Original Version, by changing formats or by porting the Font Software to a
new environment.

"Author" refers to any designer, engineer, programmer, technical
writer or other person who contributed to the Font Software.

PERMISSION & CONDITIONS
Permission is hereby granted, free of charge, to any person obtaining
a copy of the Font Software, to use, study, copy, merge, embed, modify,
redistribute, and sell modified and unmodified copies of the Font
Software, subject to the following conditions:

1) Neither the Font Software nor any of its individual components,
in Original or Modified Versions, may be sold by itself.

2) Original or Modified Versions of the Font Software may be bundled,
redistributed and/or sold with any software, provided that each copy
contains the above copyright notice and this license. These can be
included either as stand-alone text files, human-readable headers or
in the appropriate machine-readable metadata fields within text or
binary files as long as those fields can be easily viewed by the user.

3) No Modified Version of the Font Software may use the Reserved Font
Name(s) unless explicit written permission is granted by the corresponding
Copyright Holder. This restriction only applies to the primary font name as
presented to the users.

4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font
Software shall not be used to promote, endorse or advertise any
Modified Version, except to acknowledge the contribution(s) of the
Copyright Holder(s) and the Author(s) or with their explicit written
permission.

5) The Font Software, modified or unmodified, in part or in whole,
must be distributed entirely under this license, and must not be
distributed under any other license. The requirement for fonts to
remain under this license does not apply to any document created
using the Font Software.

TERMINATION
This license becomes null and void if any of the above conditions are
not met.

DISCLAIMER
THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE
COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
OTHER DEALINGS IN THE FONT SOFTWARE.
"""), "assets")

# ---------------------------------------------------------- Python packages --
PY = [
    ("Flask", "Flask", "Server web dell'applicazione", "Application web server"),
    ("Werkzeug", "Werkzeug", "Libreria di base del server web", "Web server toolkit"),
    ("Jinja2", "Jinja2", "Modelli delle pagine", "Page templates"),
    ("itsdangerous", "itsdangerous", "Firma dei dati (dipendenza di Flask)", "Data signing (Flask dependency)"),
    ("click", "click", "Riga di comando (dipendenza di Flask)", "Command line (Flask dependency)"),
    ("MarkupSafe", "MarkupSafe", "Testo sicuro nelle pagine (dipendenza di Jinja2)", "Safe markup (Jinja2 dependency)"),
    ("blinker", "blinker", "Segnali (dipendenza di Flask)", "Signals (Flask dependency)"),
    ("anyascii", "anyascii", "Traslitterazione in caratteri latini", "Transliteration to Latin characters"),
    ("pypdf", "pypdf", "Lettura dei PDF nelle fonti", "Reading PDF sources"),
    ("pdfminer.six", "pdfminer.six", "Estrazione del testo dai PDF", "PDF text extraction"),
    ("python-docx", "python-docx", "Lettura dei documenti Word nelle fonti", "Reading Word documents"),
    ("openpyxl", "openpyxl", "Lettura e importazione di file Excel", "Reading and importing Excel files"),
    ("xlrd", "xlrd", "Lettura dei vecchi file Excel (.xls)", "Reading legacy Excel files (.xls)"),
    ("lxml", "lxml", "Elaborazione XML (dipendenza di python-docx)", "XML processing (python-docx dependency)"),
    ("et_xmlfile", "et_xmlfile", "Scrittura XML (dipendenza di openpyxl)", "XML writing (openpyxl dependency)"),
    ("pillow", "Pillow", "Immagini: miniature e OCR", "Images: thumbnails and OCR"),
    ("pytesseract", "pytesseract", "Collegamento con Tesseract per l'OCR", "Bridge to Tesseract for OCR"),
    ("regex", "regex", "Classi Unicode \\p{L}\\p{M} per le chiavi dei nomi indiani, thai e giapponesi (questo fork)",
     "Unicode letter and combining-mark classes (\\p{L}\\p{M}) for identity keys of Indic, Thai and Japanese names (this fork)"),
]
for pkg, shown, rit, ren in PY:
    ver, text = pkg_license(pkg)
    lic = {"Flask": "BSD-3-Clause", "Werkzeug": "BSD-3-Clause", "Jinja2": "BSD-3-Clause",
           "itsdangerous": "BSD-3-Clause", "click": "BSD-3-Clause", "MarkupSafe": "BSD-3-Clause",
           "blinker": "MIT", "anyascii": "ISC", "pypdf": "BSD-3-Clause", "pdfminer.six": "MIT",
           "python-docx": "MIT", "openpyxl": "MIT", "xlrd": "BSD", "lxml": "BSD-3-Clause",
           "et_xmlfile": "MIT", "pillow": "MIT-CMU (HPND)", "pytesseract": "Apache-2.0",
           "regex": "Apache-2.0"}[pkg]
    add(pkg.lower().replace(".", "-"), shown, ver, lic, "", f"https://pypi.org/project/{pkg}/",
        rit, ren, wr(f"{pkg.lower().replace('.', '-')}.txt", text), "python")

# --------------------------------- video transcription, optional (1.6.0) --
# requirements-audio.txt: installed only if the user chooses transcription.
# The script wants them installed in the venv, like the other packages.
AUDIO = [
    ("faster-whisper", "faster-whisper", "MIT", "Trascrizione (Whisper su CTranslate2)", "Transcription (Whisper on CTranslate2)"),
    ("ctranslate2", "CTranslate2", "MIT", "Esecuzione di Whisper e della traduzione", "Inference engine of Whisper and of the translation"),
    ("av", "PyAV", "BSD-3-Clause", "Lettura dell'audio dei video", "Audio decoding of the videos"),
    ("onnxruntime", "ONNX Runtime", "MIT", "Modelli della diarizzazione", "Diarization models"),
    ("numpy", "NumPy", "BSD-3-Clause", "Calcolo numerico della diarizzazione", "Numerics of the diarization"),
    ("scipy", "SciPy", "BSD-3-Clause", "Raggruppamento delle voci", "Clustering of the voices"),
    ("sentencepiece", "SentencePiece", "Apache-2.0", "Testo per la traduzione in italiano", "Tokenizer of the translation to Italian"),
    ("tokenizers", "tokenizers", "Apache-2.0", "Testo per Whisper", "Tokenizer of Whisper"),
    ("huggingface-hub", "huggingface_hub", "Apache-2.0", "Download dei modelli Whisper", "Download of the Whisper models"),
]
for pkg, shown, lic, rit, ren in AUDIO:
    try:
        d = distribution(pkg)
    except PackageNotFoundError:
        sys.exit(f"{pkg} non installato: la trascrizione e' facoltativa ma lo script la documenta: "
                 "pip install -r requirements-audio.txt")
    try:
        ver, text = pkg_license(pkg)
    except SystemExit:                          # wheel without a licence file (e.g. ctranslate2)
        ver, text = d.version, (f"{shown} {d.version} - https://pypi.org/project/{pkg}/\n\n"
                                f"Licensed under the {lic} licence. The installed wheel ships no licence file;\n"
                                "the full text is in the source repository of the project.\n")
    add(pkg.lower(), shown, ver, lic, "", f"https://pypi.org/project/{pkg}/",
        rit + " (facoltativo: requirements-audio.txt)", ren + " (optional: requirements-audio.txt)",
        wr(f"{pkg.lower()}.txt", text), "python", bundled=False)
for mid, shown, lic, holder, url, rit, ren in [
        ("whisper-models", "Whisper models (faster-whisper conversion)", "MIT", "OpenAI; conversion by SYSTRAN",
         "https://huggingface.co/Systran", "Modelli di trascrizione, scaricati al primo uso",
         "Transcription models, downloaded on first use"),
        ("silero-vad", "Silero VAD", "MIT", "Silero Team", "https://github.com/snakers4/silero-vad",
         "Rilevamento del parlato, scaricato al primo uso", "Speech detection, downloaded on first use"),
        # WeSpeaker docs/pretrained.md: a pretrained model follows the licence of its dataset;
        # the models used here are trained on VoxCeleb (CC BY 4.0). Checked on 2026-10-12.
        ("wespeaker", "WeSpeaker speaker models, VoxCeleb (sherpa-onnx)", "CC-BY-4.0 (VoxCeleb dataset)",
         "WeSpeaker team; ONNX export by k2-fsa", "https://github.com/wenet-e2e/wespeaker",
         "Impronte delle voci, scaricate al primo uso", "Voiceprints, downloaded on first use"),
        # the package (metadata.json, README.md) and the argospm index declare no licence:
        # trained on OPUS data, it includes Stanza models (Apache-2.0). Checked on 2026-10-12.
        ("argos-en-it", "Argos Translate package en_it", "none declared by the package; includes Stanza models (Apache-2.0)",
         "Argos Open Technologies; training data from OPUS", "https://www.argosopentech.com",
         "Traduzione in italiano, scaricata al primo uso", "Translation to Italian, downloaded on first use")]:
    add(mid, shown, "", lic, holder, url, rit, ren, wr(f"{mid}.txt", f"""{shown} - {url}

Not distributed with Quaesitor: downloaded on first use by the video transcription
(audio/, requirements-audio.txt) into ~/.quaesitor/models or the Hugging Face cache.
Licence: {lic}. Copyright: {holder}.
"""), "tools", bundled=False)

py_lic = os.path.join(sys.base_prefix, "LICENSE.txt")
add("python", "Python", ".".join(map(str, sys.version_info[:3])), "PSF License",
    "Python Software Foundation", "https://www.python.org",
    "Interprete incorporato nell'eseguibile", "Interpreter embedded in the executable",
    wr("python.txt", rd(py_lic)) if os.path.exists(py_lic) else "", "python")

# ------------------------------------------------- external components/tools --
_, apache = pkg_license("pytesseract")
add("tesseract", "Tesseract OCR", "5.3.3", "Apache-2.0",
    "Tesseract contributors (Google, Ray Smith e altri)", "https://github.com/tesseract-ocr/tesseract",
    "Riconoscimento del testo nelle immagini. Scaricato a parte in tools/tesseract (non incluso nel programma)",
    "Text recognition in images. Downloaded separately into tools/tesseract",
    wr("apache-2.0.txt", apache), "tools", bundled=False)
add("leptonica", "Leptonica", "1.83", "BSD-2-Clause", "Copyright (C) 2001 Leptonica",
    "http://www.leptonica.org",
    "Libreria di immagini usata da Tesseract (scaricata con Tesseract)", "Image library used by Tesseract (downloaded with it)",
    wr("leptonica.txt", """Leptonica - http://www.leptonica.org

Leptonica is distributed under a BSD 2-clause style license (see the file
leptonica-license.txt in the Tesseract installation). It is not part of
OSInt Graph: it is downloaded together with Tesseract into tools/tesseract.
"""), "tools", bundled=False)
add("pyinstaller", "PyInstaller", "", "GPL-2.0 con eccezione per il bootloader",
    "PyInstaller Development Team", "https://pyinstaller.org",
    "Solo per compilare l'eseguibile: non fa parte del programma distribuito",
    "Build tool only: not part of the distributed program",
    wr("pyinstaller.txt", """PyInstaller - https://pyinstaller.org

PyInstaller is used only to build the Windows executable of OSInt Graph. It
is licensed under the GNU GPL version 2 with a special exception for the
bootloader, which allows the generated executable to be distributed under
the license of the program itself (here: GNU GPL version 3).
"""), "tools", bundled=False)

with io.open(os.path.join(OUT, "index.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(entries, f, ensure_ascii=False, indent=1)

# --------------------------------------------------- THIRD-PARTY-NOTICES.md --
lines = ["# Third-party notices", "",
         "Quaesitor, a fork of OSInt Graph by Andrea Cumini, is free software under the GNU GPL version 3 (see LICENSE and NOTICE).",
         "It includes or uses the following third-party components. The full license",
         "texts are in `quaesitor/static/licenses/` and can be read from the program itself",
         "(link «Licenze» in the left panel).", "",
         "| Component | Version | License | Copyright | Used for |", "|---|---|---|---|---|"]
for e in entries:
    if e["group"] == "program":
        continue
    lines.append(f"| [{e['name']}]({e['url']}) | {e['version']} | {e['license']} | {e['copyright']} | "
                 f"{e['role']['en']}{'' if e['bundled'] else ' (not bundled)'} |")
lines += ["", "Brand names and logos of the social platforms are trademarks of their respective",
          "owners; they are used only to identify the platform of a profile. OSInt Graph is not",
          "affiliated with, endorsed by or sponsored by any of them.", ""]
with io.open(os.path.join(ROOT, "THIRD-PARTY-NOTICES.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print(f"{len(entries)} componenti -> quaesitor/static/licenses/ e THIRD-PARTY-NOTICES.md")
