# Contributing to Quaesitor

Issues and pull requests are welcome on [SOsintOps/quaesitor](https://github.com/SOsintOps/quaesitor). Problems with the fork's additions belong here, not to the original author of OSInt Graph. Security problems follow the [security policy](SECURITY.md) instead of a public issue.

## Ground Rules

- Keep the upstream architecture: Flask on the server, vanilla JavaScript in the browser, no build step.
- Write the documentation in British English, under `docs/`. Interface texts go in `quaesitor/static/i18n.js`, in all six languages.
- Keep the attribution of the original author where it is: the credits line, the credits and licences windows, the headers of the source files (NOTICE, point 2).
- Never commit `chatbot.conf`, `services.conf`, `data/` or `sources/`: they hold keys and case data.
- Never call the Epieos API from tests or scripts: every search costs credits. Use the sample answers of `scripts/epieos/make_sample.py`.
- `quaesitor/generated/` is produced by `scripts/ftm/make_ftm_types.py`: regenerate it, never edit it by hand.

## Layout

| Path | Contents |
|---|---|
| `app.py` | Entry point: `python app.py` starts the server. |
| `quaesitor/` | The program: the Flask app, its blueprints, the archive, the importers, the ontology. |
| `quaesitor/templates/`, `quaesitor/static/` | The page, its scripts, styles, icons, licences and the manual. |
| `quaesitor/audio/` | Video transcription (optional, `requirements-audio.txt`). |
| `tests/` | The test suite. |
| `scripts/` | Build, release, licences, icons, Follow the Money and sample tools. |
| `docs/` | FAQ, guidelines, version history, case study. |
| `examples/` | Sample files to import. |

## Where the Data Live (Decision)

The cases (`data/`) and the documents to index (`sources/`, `fonti/` on installs older than 1.8.0) sit next to the program by default. This is deliberate, inherited from the original program and kept in 1.8.0: the folder is portable, and copying it moves the program with every case to another computer. Users who want them elsewhere set `DATA_DIR` and `SOURCES_DIR` (since 1.9.0); the Linux launchers of Argos, Speculator and Wukong already set `DATA_DIR`. Do not move the defaults into the user profile without revisiting this decision.

## Development Setup

```
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt     # Windows: .venv\Scripts\python.exe
.venv/bin/python -m pip install --group dev            # pytest (pip 25.1 or newer)
.venv/bin/python -m pytest
DATA_DIR=/tmp/quaesitor-test PORT=5002 .venv/bin/python app.py
```

`DATA_DIR` keeps a test archive away from your cases. Run `python scripts/smoke_test.py` against a running server before a pull request that touches the import or the API.

## Pull Requests

One change per pull request, with a short description of what changes for the user. Add or update the tests, and the entry of `docs/versionhistory.md` when the change is visible in the program.
