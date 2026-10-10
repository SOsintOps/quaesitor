# Frequently Asked Questions (FAQ)

Frequently asked questions about Quaesitor — the project, the licence, installation, data and privacy, the integrations.

## Table of Contents

* [What is Quaesitor?](#what-is-quaesitor)
* [Why was the fork created?](#why-was-the-fork-created)
* [Why is the fork named "Quaesitor"?](#why-is-the-fork-named-quaesitor)
* [Who gets the credit?](#who-gets-the-credit)
* [Is this the official OSInt Graph?](#is-this-the-official-osint-graph)
* [What licence applies?](#what-licence-applies)
* [What must I do if I give a copy to someone else?](#what-must-i-do-if-i-give-a-copy-to-someone-else)
* [And while the copy stays internal?](#and-while-the-copy-stays-internal)
* [How do I install it on Windows?](#how-do-i-install-it-on-windows)
* [How do I run it from source on any system?](#how-do-i-run-it-from-source-on-any-system)
* [Does it run in Docker?](#does-it-run-in-docker)
* [Is there a Windows executable?](#is-there-a-windows-executable)
* [Does it run on Linux?](#does-it-run-on-linux)
* [Which languages does the OCR read?](#which-languages-does-the-ocr-read)
* [Which branch do I use? What is `osintgraph`?](#which-branch-do-i-use-what-is-osintgraph)
* [Where are my cases?](#where-are-my-cases)
* [What leaves my computer?](#what-leaves-my-computer)
* [Does the program use AI? Do I have to?](#does-the-program-use-ai-do-i-have-to)
* [Where do API keys go?](#where-do-api-keys-go)
* [What is Follow the Money and why is it here?](#what-is-follow-the-money-and-why-is-it-here)
* [How do I import a Follow the Money dataset?](#how-do-i-import-a-follow-the-money-dataset)
* [How do I export a case?](#how-do-i-export-a-case)
* [What is the OpenSanctions panel?](#what-is-the-opensanctions-panel)
* [A new version of Follow the Money came out. What do I regenerate?](#a-new-version-of-follow-the-money-came-out-what-do-i-regenerate)
* [What does Epieos do and what does it cost?](#what-does-epieos-do-and-what-does-it-cost)
* [What enters the graph from an Epieos response?](#what-enters-the-graph-from-an-epieos-response)
* [Can I import an Epieos response I already have?](#can-i-import-an-epieos-response-i-already-have)
* [The Epieos search failed. What do the errors mean?](#the-epieos-search-failed-what-do-the-errors-mean)
* [How are Cyrillic, Arabic or Chinese names handled?](#how-are-cyrillic-arabic-or-chinese-names-handled)
* [What is the transliteration dictionary?](#what-is-the-transliteration-dictionary)
* [And Chinese?](#and-chinese)
* [Does it talk to Cognitor?](#does-it-talk-to-cognitor)
* [Where do I report a problem or ask a question?](#where-do-i-report-a-problem-or-ask-a-question)
* [Where is the rest of the documentation?](#where-is-the-rest-of-the-documentation)

## About the Project & Its Name

### What is Quaesitor?

A modified copy of [OSInt Graph](https://github.com/tingon11/OsintGraph), the case graph for OSINT investigations written by Andrea Cumini: people, phones, e-mails, social profiles, vehicles, places and documents as an interactive graph, everything stored locally. Quaesitor adds support for non-Latin names, the Follow the Money data model, the Epieos API and a Windows installer. Nothing else changes.

### Why was the fork created?

Because Andrea Cumini's program was already excellent, and the only thing it lacked was being shaped around one analyst's own needs: names in Cyrillic, Arabic, Chinese and other scripts that must still merge into one node; data exchanged with Aleph and OpenSanctions in the Follow the Money format; reverse lookups through a paid API that must never run by accident; a one-click install on Windows. These are specific needs of the people using this copy, not gaps in the original. Forking was the honest way to get them without asking the author to carry someone else's requirements.

### Why is the fork named "Quaesitor"?

*Quaesitor* is the Latin name of the magistrate who conducted a criminal inquiry in Rome. It fits a tool that organises an investigation, and it sits next to the other Latin names used by SOsintOps. A different name is also required: point 3 of the additional licence terms in [NOTICE](../NOTICE) reserves "OSInt Graph", its logo and its icon to the original author, and any modified version distributed to others must be called something else.

### Who gets the credit?

Andrea Cumini (andrea@osintinfo.net, www.osintinfo.net). The idea, the design, the code, the built-in manual, the screenshots and the six-language interface are his. The fork's own changes are listed in the README; its bugs are the fork's. His attribution in the interface, in the source headers and in the README stays.

### Is this the official OSInt Graph?

No. For the original program, its releases and its author go to [github.com/tingon11/OsintGraph](https://github.com/tingon11/OsintGraph) and [www.osintinfo.net](https://www.osintinfo.net). Do not report Quaesitor's problems to him.

## Licence & Distribution

### What licence applies?

GNU GPL v3 with additional terms under section 7, unchanged from upstream: see [LICENSE](../LICENSE) and [NOTICE](../NOTICE). You may use, study, copy and modify the program.

### What must I do if I give a copy to someone else?

The moment a modified copy leaves the team, four obligations apply:

*   **Attribution:** keep the author attribution visible in the interface (credits line, credits window, licences window), in `NOTICE`, in `THIRD-PARTY-NOTICES.md` and in the source headers.
*   **Name and logo:** use a different name, logo and icon. That is why the fork is called Quaesitor; Quaesitor ships its own provisional wordmark and icon for this reason.
*   **Origin:** mark the version as modified and do not misrepresent its origin.
*   **Source:** distribute it under the same licence and make the source available to the recipients.

### And while the copy stays internal?

Nothing is triggered: copyleft and the renaming clause apply to distribution. The attribution still stays, because the interface is kept.

## Installation & Running

### How do I install it on Windows?

Double-click `installa.bat` in the program folder (or run `.\installa.bat` from PowerShell). It finds Python 3.10 or newer, creates `.venv`, installs the libraries, prepares `chatbot.conf` and `services.conf` from the examples, creates the `fonti` folder and asks whether to download Tesseract for OCR. Then `avvia.bat` starts the program and opens the browser on http://127.0.0.1:5000. `aggiorna.bat` pulls the repository and updates the libraries; `disinstalla.bat` removes `.venv` and asks before touching the cases.

### How do I run it from source on any system?

1.  Create a virtual environment: `python -m venv .venv`.
2.  Activate it: `.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on Linux and macOS.
3.  Install the libraries: `pip install -r requirements.txt`.
4.  Start the program: `python app.py`.

One command per line in PowerShell: `&&` is not accepted there. Another port: set the `PORT` environment variable before starting.

### Does it run in Docker?

Not yet. A `Dockerfile` and a `docker-compose.yml` are queued, with the requirements written down in [Ideas & Roadmap](todo.md): a `python:3.12-slim` image with Tesseract and its language packs, volumes for `data/`, `fonti/`, `chatbot.conf` and `services.conf`, the app bound to localhost behind the published port, Ollama outside the image. The program has no authentication: never publish its port beyond localhost without a proxy with login.

### Is there a Windows executable?

Upstream provides `build_app.py`, which compiles the server into a single executable with a small launcher. The fork has not changed it. The `.bat` scripts are the primary Windows install.

### Does it run on Linux?

Yes, and that is how the SOsintOps workstations ship it: Argos (Ubuntu 24.04 and 26.04) and Speculator (Debian 13) clone this repository, create a virtual environment, install Tesseract from apt and start `app.py` with `DATA_DIR` and `PORT` set. The complete install and every feature (cases, imports, Follow the Money, Epieos from file, document sources with OCR, export, restart) were verified on Ubuntu 26.04 with Python 3.12 and 3.14 and on Debian 13 with Python 3.13. The README has the manual steps. Nothing in the program needs Windows: the automatic Tesseract download and the launcher window are Windows conveniences, on Linux Tesseract comes from apt and the browser is opened by the launcher script.

### Which languages does the OCR read?

All the Tesseract language packs installed on the machine, joined together with English last (for example `ita+rus+eng`: the first language leads the recognition), so accents and non-Latin scripts are read correctly; with only the engine installed Tesseract reads English and drops accents ("citta" for "città"). Install the packs you need (`tesseract-ocr-ita`, `tesseract-ocr-chi-sim`, `tesseract-ocr-rus`, `tesseract-ocr-ara` on Debian and Ubuntu; on Windows the `.traineddata` files go into `tools	esseract	essdata`) or set `TESSERACT_LANG` to choose. The languages in use are shown by `/api/sources/status`.

### Which branch do I use? What is `osintgraph`?

`main` is Quaesitor: install and work from it. `osintgraph` is a mirror of the upstream repository and is never edited: it is updated only by merging the upstream `main`, and upstream changes reach Quaesitor by merging it into `main`. To follow upstream:

```
git remote add upstream https://github.com/tingon11/OsintGraph.git
git fetch upstream
git checkout osintgraph
git merge upstream/main
git checkout main
git merge osintgraph
```

## Data & Privacy

### Where are my cases?

In the `data` folder next to the program, one SQLite archive per case. Imports, Epieos responses and Follow the Money ids live inside the same archive. Back up that folder.

### What leaves my computer?

Nothing, unless you switch something on. Three features talk to the outside; each is off by default, each asks for confirmation when enabled, and each says what it sends:

| Feature | What is sent | Where |
|---|---|---|
| AI (text to nodes, transliteration) | the text or the names you submit | the Ollama or OpenAI-compatible server you configured; a local Ollama keeps it on the machine |
| OpenSanctions lookup | the names you search | `api.opensanctions.org` or your own yente instance |
| Epieos | the e-mail or phone number you search, plus the chosen modules | `api.epieos.com` |

Switched off, the program makes no network call at all.

### Does the program use AI? Do I have to?

It can, and you do not have to. The AI is optional and off by default. It is used for two tasks only: turning free text into proposed nodes that you review before they enter the graph, and transliterating non-Latin names. It works with any Ollama or OpenAI-compatible server you configure in `chatbot.conf`; a local Ollama keeps everything on your machine (the Ollama setup guide is being translated; the built-in manual, chapter 14, covers the configuration). Nothing is sent anywhere while it is off, and the program is complete without it.

### Where do API keys go?

In `services.conf`, which is ignored by git and never sent back to the browser. Environment variables work too (for example `SERVICES_EPIEOS_API_KEY`).

## Follow the Money & OpenSanctions

### What is Follow the Money and why is it here?

[Follow the Money](https://followthemoney.tech) (FtM) is the data model used by Aleph and OpenSanctions: persons, companies, bank accounts, sanctions, vessels and so on, with typed relations such as ownership or directorship. Quaesitor reads and writes it so that a case can exchange data with those systems. The 41 FtM node schemata that have no upstream equivalent are native node types; the 17 edge schemata are typed relations on links.

### How do I import a Follow the Money dataset?

Drop a `.json`, `.jsonl` or `.ftm` file on **Import CSV/Excel**: the Follow the Money import window opens with counts per schema, filters (schemata, text, one-hop neighbours, maximum number, dataset name) and a background import with a progress bar. Up to 200 MB per file. Re-importing the same dataset updates the nodes instead of duplicating them. The Follow the Money guide, with what is lost on the way, is being translated and will join the documentation.

### How do I export a case?

**Export Follow the Money** writes the case (or only the visible nodes) as JSON lines. Native types keep their schema, built-in and Italian types are mapped, types without an FtM equivalent become `Note`. Importing the export back into the same case creates nothing new.

### What is the OpenSanctions panel?

An online search against the OpenSanctions API (or your own yente instance): search, match and import an entity with its nested relations. Off by default; it needs an API key in `services.conf`.

### A new version of Follow the Money came out. What do I regenerate?

`ftm_schema.json` and `ontology_ftm.py`, with `scripts/ftm/make_ftm_types.py` on a machine where the `followthemoney` package installs. At runtime the program does not depend on that package.

## Epieos

### What does Epieos do and what does it cost?

Reverse lookup of an e-mail address or phone number across about thirty services (accounts, breaches, recovery methods). It is a paid API: every search costs one credit, whether it finds something or not. Reading the schema is free. Nothing runs by itself: every search opens a confirmation dialog with the identifier, the modules (each can be unticked) and the remaining credits.

### What enters the graph from an Epieos response?

One account node per service where the identifier is registered, a breach node per leak, phone and e-mail nodes for recovery methods, organisation nodes for LinkedIn companies and schools. Social profiles are identified by the service's user id and labelled with the profile name; no person node is created from a profile. The full response stays in the case. The Epieos guide is being translated and will join the documentation.

### Can I import an Epieos response I already have?

Yes: drop the saved JSON on **Import CSV/Excel**. It is recognised and attached to the node of the identifier, without any call and without spending credits.

### The Epieos search failed. What do the errors mean?

*   **401:** key missing or invalid.
*   **402:** credits exhausted.
*   **403:** pack not available for this key.
*   **429:** rate limit reached; the dialog shows the seconds to wait.
*   **500:** service error.

The dialog stays open so you can retry.

## Non-Latin Names

### How are Cyrillic, Arabic or Chinese names handled?

Each name node keeps its original script and carries a Latin form as an attribute (two-line label, "Transliteration" row in the card), so the same person spelled in two scripts merges into one node. A switch restores separate Latin twin nodes if you prefer the upstream behaviour.

### What is the transliteration dictionary?

A window where you fix transliterations by hand, import and export them as CSV, and collect the names already on the graph. The AI, when enabled, can propose transliterations; the dictionary always wins.

### And Chinese?

Spaced pinyin in the Latin form, search from two characters, and source search on text without spaces.

## Integrations

### Does it talk to Cognitor?

Not directly. Cognitor (face recognition with cases and a co-appearance graph) and Quaesitor share no code and no live link. The practical bridge is a file: Cognitor would export persons, photos and co-appearances in Follow the Money format, which Quaesitor imports natively. That exporter does not exist yet.

## Help & Documentation

### Where do I report a problem or ask a question?

In the issues of the SOsintOps repository. Not to the original author: the changes are the fork's.

### Where is the rest of the documentation?

The README section *Documentation* lists every page. The analytic standards, the 5W1H method and OPSEC are in the [Guidelines](guidelines.md); the method behind the graph is in the [Link Analysis Guidelines](link-analysis.md), rewritten from the UNODC manual for analysts; the node types are in [Graph Entities](ontology.md); the releases are in the [Version History](versionhistory.md) and what is planned in [Ideas & Roadmap](todo.md).
