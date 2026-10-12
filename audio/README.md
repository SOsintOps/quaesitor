# audio/ — video transcription

The five modules of this folder come from [Cognitor](https://github.com/SOsintOps/cognitor), the face-recognition program of the same holder, at commit `fb93e01` (2026-10-12). The holder released them under the GNU GPL v3 or later as part of Quaesitor (point 6 of the Cognitor licence). The copy in Cognitor keeps the Cognitor licence; the copy here follows the GPL, like the rest of Quaesitor.

| module | what it does |
|---|---|
| `transcribe.py` | transcription with faster-whisper; writes `transcript.json` and `transcript.txt` |
| `diarize.py` | who speaks when: Silero VAD and WeSpeaker on onnxruntime, segments labelled `PARLANTE 1..N` |
| `voci.py` | voiceprints: catalogue of the WeSpeaker models, centroid per speaker, comparison |
| `translate.py` | translation of the transcript: Whisper for English, Argos packages on CTranslate2 for Italian |
| `acceleratore.py` | choice of the ONNX Runtime provider (CUDA or CPU) |

The packages are optional and listed in `requirements-audio.txt`; `audio.available()` tells whether they are installed. `transcripts.py` (outside this folder, Quaesitor's own code) turns a transcript into Follow the Money entities, and `app.py` runs the job (`/api/transcribe`).

## Changes made in the copy

Keep this list current: it is what a future realignment with Cognitor has to preserve.

1. A GPL header with the origin of the file, at the top of every module.
2. Model folder: `QUAESITOR_MODELS_DIR`, default `~/.quaesitor/models` (Cognitor: `COGNITOR_MODELS_DIR`, `~/.cognitor/models`). Setting `QUAESITOR_MODELS_DIR` to `~/.cognitor/models` shares the diarization and translation models already downloaded by Cognitor; the Whisper models are shared anyway, through the Hugging Face cache.
3. `transcribe.transcribe_video()` takes `log=print` and sends its progress lines there, so that a job of the Flask server reads them without redirecting stdout.
4. `voci.collega_parlante()` and `voci.scollega_parlante()` are removed: they write in Cognitor's case folders (`facestore`, `graphstore`, `joblog`), which do not exist here.
5. The header line of `transcript.txt` names Quaesitor instead of Cognitor.

Unchanged on purpose: the Italian messages and identifiers of the modules (as in Cognitor), and the label `PARLANTE k` inside `transcript.json`, so that the files stay readable by both programs. The graph shows the speakers as "Speaker k (file)".

The tests of these modules come from Cognitor too (`tests/test_audio_*.py`), with the imports adapted.

## Realigning with Cognitor

Copy the five files again from the Cognitor commit wanted, re-apply the changes above, update the commit in the headers and in this page, then run `.venv\Scripts\python.exe -m pytest`.
