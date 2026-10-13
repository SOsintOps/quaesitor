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
* [Can 2.0 open the cases of 1.x?](#can-20-open-the-cases-of-1x)
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
* [Does the video transcription send the audio anywhere?](#does-the-video-transcription-send-the-audio-anywhere)
* [Does it talk to Cognitor?](#does-it-talk-to-cognitor)
* [Where do the node icons come from?](#where-do-the-node-icons-come-from)
* [What do the marks on the corners of a node mean?](#what-do-the-marks-on-the-corners-of-a-node-mean)
* [Where do I put the 4 x 4 grade of a link?](#where-do-i-put-the-4-x-4-grade-of-a-link)
* [Why the 4 x 4 and not the Admiralty 6 x 6?](#why-the-4-x-4-and-not-the-admiralty-6-x-6)
* [Solid or dashed links?](#solid-or-dashed-links)
* [Is the graph my report?](#is-the-graph-my-report)
* [Can chats, Telegram channels and username searches become nodes?](#can-chats-telegram-channels-and-username-searches-become-nodes)
* [Where do I report a problem or ask a question?](#where-do-i-report-a-problem-or-ask-a-question)
* [Where is the rest of the documentation?](#where-is-the-rest-of-the-documentation)
* [Are there related SOsintOps projects?](#are-there-related-sosintops-projects)

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
*   **Name and logo:** use a different name, logo and icon. That is why the fork is called Quaesitor; Quaesitor ships its own logo and icon for this reason: a Q whose tail ends in a graph node.
*   **Origin:** mark the version as modified and do not misrepresent its origin.
*   **Source:** distribute it under the same licence and make the source available to the recipients.

### And while the copy stays internal?

Nothing is triggered: copyleft and the renaming clause apply to distribution. The attribution still stays, because the interface is kept.

## Installation & Running

### How do I install it on Windows?

Double-click `install.bat` in the program folder (or run `.\install.bat` from PowerShell). It finds Python 3.10 or newer, creates `.venv`, installs the libraries, prepares `chatbot.conf` and `services.conf` from the examples, creates the `sources` folder and asks whether to download Tesseract for OCR. Then `start.bat` starts the program and opens the browser on http://127.0.0.1:5000. `update.bat` pulls the repository and updates the libraries; `uninstall.bat` removes `.venv` and asks before touching the cases.

### How do I run it from source on any system?

1.  Create a virtual environment: `python -m venv .venv`.
2.  Activate it: `.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on Linux and macOS.
3.  Install the libraries: `pip install -r requirements.txt`.
4.  Start the program: `python app.py`.

One command per line in PowerShell: `&&` is not accepted there. Another port: set the `PORT` environment variable before starting.

### Does it run in Docker?

Not yet. A `Dockerfile` and a `docker-compose.yml` are queued, with the requirements written down in [Ideas & Roadmap](todo.md): a `python:3.12-slim` image with Tesseract and its language packs, volumes for `data/`, `sources/`, `chatbot.conf` and `services.conf`, the app bound to localhost behind the published port, Ollama outside the image. The program has no authentication: never publish its port beyond localhost without a proxy with login.

### Is there a Windows executable?

Upstream provides the build script, now `scripts/build_app.py`, which compiles the server into a single executable (`pip install --group build` first); `python -m quaesitor.launcher` opens a small launcher window. The `.bat` scripts are the primary Windows install.

### Does it run on Linux?

Yes, and that is how the SOsintOps workstations ship it: Argos (Ubuntu Budgie 24.04 and 26.04) and Speculator (Debian 13) clone this repository, create a virtual environment, install Tesseract from apt and start `app.py` with `DATA_DIR` and `PORT` set. The complete install and every feature (cases, imports, Follow the Money, Epieos from file, document sources with OCR, export, restart) were verified on the Ubuntu 26.04 base of Argos with Python 3.12 and 3.14 and on Debian 13 with Python 3.13. The README has the manual steps. Nothing in the program needs Windows: the automatic Tesseract download and the launcher window are Windows conveniences, on Linux Tesseract comes from apt and the browser is opened by the launcher script.

### Which languages does the OCR read?

All the Tesseract language packs installed on the machine, joined together with English last (for example `ita+rus+eng`: the first language leads the recognition), so accents and non-Latin scripts are read correctly; with only the engine installed Tesseract reads English and drops accents ("citta" for "città"). Install the packs you need (`tesseract-ocr-ita`, `tesseract-ocr-chi-sim`, `tesseract-ocr-rus`, `tesseract-ocr-ara` on Debian and Ubuntu; on Windows the `.traineddata` files go into `tools\tesseract\tessdata`) or set `TESSERACT_LANG` to choose. The languages in use are shown by `/api/sources/status`.

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

The program is portable by design: `data/` and the documents folder `sources/` sit next to it, so the whole folder moves to another computer with its cases. To keep them elsewhere (an encrypted volume, a home folder on Linux), set `DATA_DIR` for the cases and `SOURCES_DIR` for the documents before starting it, as the Argos, Speculator and Wukong launchers do for `DATA_DIR`. On Windows: `set DATA_DIR=D:\cases` and `set SOURCES_DIR=D:\documents` in the console, then `start.bat`.

### Can 2.0 open the cases of 1.x?

No. Since 2.0 what the program saves is English: the field keys and the drop-down values of the investigative types (`serial_number`, "Semi-automatic pistol"), the keys of the nodes added by hand, the names of the links it draws itself; the interface shows them in its language. A case written by 1.x keeps the Italian keys, so 2.0 lists it with "(1.x, rebuild)" and does not open it. Rebuild it by importing its source files again: the import still reads the Italian columns and values (`cognome`, `nascita`, `collegamento`, "Cocaina"), and so does the AI extraction. Keep the 1.x folder if you need to look at the old case meanwhile.

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

**Export Follow the Money** writes the case (or only the visible nodes) as JSON lines. Native types keep their schema, built-in and investigative types are mapped, types without an FtM equivalent become `Note`. Importing the export back into the same case creates nothing new.

### What is the OpenSanctions panel?

An online search against the OpenSanctions API (or your own yente instance): search, match and import an entity with its nested relations. Off by default; it needs an API key in `services.conf`.

### A new version of Follow the Money came out. What do I regenerate?

`quaesitor/generated/ftm_schema.json` and `quaesitor/generated/ontology_ftm.py`, with `scripts/ftm/make_ftm_types.py` on a machine where the `followthemoney` package installs. At runtime the program does not depend on that package.

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

### Does the video transcription send the audio anywhere?

No. Since 1.6.0 the transcription runs on this computer: faster-whisper for the text, Silero VAD and WeSpeaker for the speakers, Argos packages for the Italian translation. The network is used once per model, to download it on first use (a few hundred MB in all, into `~/.quaesitor/models` and the Hugging Face cache); after that the transcription works offline. The feature is optional: answer yes to the transcription in `install.bat`, or run `.venv\Scripts\python.exe -m pip install -r requirements-audio.txt`. The modules come from Cognitor, released by their holder under the GPL as part of Quaesitor.

### Does it talk to Cognitor?

Through a file, since 1.6.0. Cognitor (face recognition with cases and a co-appearance graph) exports a case with **Export (FollowTheMoney)** as a `.cognitor.zip` bundle. Open it from **Import** or drop it on the Follow the Money window; for a bundle above 20 MB type its path in the field of that window. Persons, unknown groups, face photos, "seen together" links with the number of shared photos and video segments, videos with their transcripts and the "speaks in" / "appears in" links arrive in the current case. The photos are copied under `data/media/cognitor/`, the transcripts into the sources folder, where the search finds them. Importing the same case again updates the nodes instead of duplicating them. Face and voice embeddings stay in Cognitor: Follow the Money has no schema for them. An unknown group named in Cognitor after an export becomes a person at the next export; the old "Unknown #N" node stays here, to be merged by hand.

### Where do the node icons come from?

Since 1.7.0 the node types have colour icons. They were generated in October 2026 with ChatGPT and Gemini, from a prompt written by the maintainer of the fork: a colour evolution of a set of flat "incognito" glyphs (hoods, fedoras, masks, dark glasses), one icon per node type, no text. The generators returned nine sheets of icons on a white background, and a tenth, two icons (a microscope and an encrypted phone), was generated for 1.7.1 in the same glossy style. `scripts/icons/split_sheets.py` cuts them into single icons, `scripts/icons/labels.json` records what each cut shows, `scripts/icons/mapping.json` assigns a cut to each node type and `scripts/icons/install.py` copies the chosen ones to `quaesitor/static/icons/entities/`. The sheets themselves are not in the repository. Since 1.7.1 every node type has one, `article` and `call` included, and so do most sub-types: the substance of a drug (pills, leaf, droplet...), the kind of identity document, financial document, judicial act and device each pick a more specific icon, listed in the icon tables of `quaesitor/ontology.py`; a sub-type without one ("Other" and a few others) shows the icon of its type. Font Awesome glyphs remain only as fallback, and a social profile keeps the logo of its platform. To change an icon, point its key in `mapping.json` to another cut, or generate a new sheet with the same prompt, cut it and run `install.py` again. The icons are original images of this fork, distributed under the same licence as the program.

### What do the marks on the corners of a node mean?

Since 2.1.0 the program reads the data of a node and shows what it finds on its corners, as Maltego does with its overlays, each corner with one meaning. Top right is the brand: the network of a payment card, recognised from its first digits even when the number is masked, the chain of a crypto wallet from the form of its address, the provider of an e-mail. Bottom left is the flag of the country: of an IBAN or a BIC, of the international prefix of a phone, of an identity document, of the jurisdiction of a company, of the flag of a vessel, of the nationality of a person imported from Follow the Money. Bottom right is an alert: a card number that fails the Luhn check, an IBAN whose check digits are wrong, a forged or expired document, an expired card, a removed serial number, counterfeit banknotes. The icon itself changes with the kind of item: a rifle or a knife, gold, a watch, a painting, a criminal or a terrorist group, besides the man and the woman of the persons. Nothing of this is saved: it is computed from the cards every time, so a value corrected by hand changes the mark at once. The card of the node lists the marks with their meaning, the key on the graph explains them, and *Corner marks on the nodes*, under the key switch, hides them. A mark is a reading of the data, not a verification: a valid IBAN can belong to anyone. The full list of rules is in [Graph Entities](ontology.md#5-node-appearance).

## Method & Analysis

### Where do I put the 4 x 4 grade of a link?

In the link label or in a field of the card, as the [Link Analysis Guidelines](link-analysis.md#doing-it-in-quaesitor) suggest: write the code (`A1`, `B2`, `C3`) so that the grade travels with the line and appears in the PDF export. Be aware that Quaesitor has no dedicated grade field yet: the program does not check the code, does not filter or colour links by it and does not derive the line style from it. The grade is your judgement, written by hand; keep the label and the line style consistent with it.

### Why the 4 x 4 and not the Admiralty 6 x 6?

Because the method of this fork is the UNODC [*Criminal Intelligence: Manual for Analysts*](https://www.unodc.org/documents/organized-crime/Law-Enforcement/Criminal_Intelligence_for_Analysts.pdf), and the 4 x 4 is the system it recommends: source `A`, `B`, `C` or `X`, information `1` to `4`. It asks a question you can answer for every item (did the source know it personally? is it corroborated?), and its confirmed grades are the ones that decide whether a line is drawn solid. The 6 x 6 (Admiralty) system is not a finer version of the same scale: it grades how plausible the information is, not how close the source was to it, so an item graded on the 6 x 6 must be re-graded, not translated number for number. The conversion is in the Field Notes, [Converting from the 6 x 6 (Admiralty) System](https://github.com/SOsintOps/intelligence-field-notes/blob/main/docs/source-evaluation.md#converting-from-the-6-x-6-admiralty-system); the one SOsintOps tool that keeps the 6 x 6 on purpose, [Elementary CTI](https://github.com/SOsintOps/elementary-CTI), and why, is explained [in the same page](https://github.com/SOsintOps/intelligence-field-notes/blob/main/docs/source-evaluation.md#one-exception-machine-graded-cti-feeds).

### Solid or dashed links?

Solid only for a **confirmed** link, that is one whose information is graded `A1`, `A2`, `B1` or `B2`; dashed for every other grade, and dashed with a label starting with "hypothesis" for a link you infer rather than observe, with the reasoning in the link's notes. A solid line on a `C3` states as fact what is hearsay. When the chart suggests more than one explanation, test them against each other before drawing any of them solid: analysis of competing hypotheses is in the Field Notes, [Analytic Techniques](https://github.com/SOsintOps/intelligence-field-notes/blob/main/docs/analytic-techniques.md), and [Il Conclave](https://github.com/SOsintOps/il-conclave), a skill for Claude Code (in Italian), runs ACH and a premortem as forced procedures on a question you give it.

### Is the graph my report?

No. The report is the product; the graph and the cards, exported to PDF, are its annexes. The report starts with the bottom line, keeps the findings (sourced and graded) apart from the judgements, and states the gaps: the structure is in the Field Notes, [Report Writing](https://github.com/SOsintOps/intelligence-field-notes/blob/main/docs/report-writing.md). [Argos](https://github.com/SOsintOps/Argos) and [Speculator](https://github.com/SOsintOps/Speculator-Project) ship report templates built on that page in their `templates/` folders, a plain Markdown one and Word templates for full and executive reports. For further reading on the craft, the SOsintOps fork of [awesome-intelligence-writing](https://github.com/SOsintOps/awesome-intelligence-writing) collects guides on intelligence writing; for the handling markings (TLP) and the other classification schemes used in intelligence tooling, see the classification module of [Codex Machinae](https://github.com/SOsintOps/codex-machinae).

### Can chats, Telegram channels and username searches become nodes?

Yes, through the import. [TGchat-analytics](https://github.com/SOsintOps/TGchat-analytics) (statistical reports on exported chats, Telegram HTML exports included) and [TelEgrapherX](https://github.com/SOsintOps/TelEgrapherX) (collection and analysis of Telegram groups and channels) tell you who talks to whom and how often; the participants become person or account nodes and the exchanges become links, through the CSV and Excel wizard. The SOsintOps fork of [Maigret](https://github.com/SOsintOps/maigret) searches a username across many sites and saves its reports in several formats, CSV and JSON among them; the accounts it finds become account nodes, through the CSV wizard or the import of JSON exports of OSINT tools. Grade what you import like any other information: a tool's output is a lead, not a confirmed link. For Italian cases, [Acta Diurna](https://github.com/SOsintOps/acta-diurna), a dashboard (in Italian) of news on law-enforcement operations in Italy, is a source of the events and offences that Quaesitor's investigative node types (offences, weapons, drugs, cash, judicial acts such as arrest and seizure reports) are made for.

## Help & Documentation

### Where do I report a problem or ask a question?

In the issues of the SOsintOps repository. Not to the original author: the changes are the fork's.

### Where is the rest of the documentation?

The README section *Documentation* lists every page. The analytic standards, the 5W1H method and OPSEC are in the [Guidelines](guidelines.md); the method behind the graph is in the [Link Analysis Guidelines](link-analysis.md), rewritten from the UNODC [*Criminal Intelligence: Manual for Analysts*](https://www.unodc.org/documents/organized-crime/Law-Enforcement/Criminal_Intelligence_for_Analysts.pdf); the node types are in [Graph Entities](ontology.md); the releases are in the [Version History](versionhistory.md) and what is planned in [Ideas & Roadmap](todo.md). The common method of the SOsintOps tools (analytic standards, source evaluation, estimative language, report writing) is in the [Intelligence Field Notes](https://github.com/SOsintOps/intelligence-field-notes), copied for offline reading in [`field-notes`](field-notes/README.md).

### Are there related SOsintOps projects?

Yes:

* **[Argos](https://github.com/SOsintOps/Argos)** and **[Speculator](https://github.com/SOsintOps/Speculator-Project)**: the OSINT workstations for Ubuntu Budgie and Debian that install and start Quaesitor, and carry the report templates the graph is an annex to.
* **[Wukong](https://github.com/SOsintOps/Wukong)**: the China-focused workstation, for the Chinese names the transliteration dictionary handles.
* **[Exploratores](https://github.com/SOsintOps/Exploratores)**: the browser toolkit for the searches whose results become nodes.
* **[Aethelburg](https://github.com/SOsintOps/Aethelburg-project)**: an analyser of UK company registers, for the ownership chains drawn with Follow the Money relations.
* **[Elementary CTI](https://github.com/SOsintOps/elementary-CTI)**: a ransomware threat-intelligence aggregator.
* **[Acta Diurna](https://github.com/SOsintOps/acta-diurna)**: a dashboard (in Italian) of news on law-enforcement operations in Italy, a source for Italian cases.
* **[Il Conclave](https://github.com/SOsintOps/il-conclave)** and **[Codex Machinae](https://github.com/SOsintOps/codex-machinae)**: analytic procedures (ACH, premortem) run by an AI, and a playbook for building software with AI collaborators.
* **[TGchat-analytics](https://github.com/SOsintOps/TGchat-analytics)**, **[TelEgrapherX](https://github.com/SOsintOps/TelEgrapherX)** and **[Maigret](https://github.com/SOsintOps/maigret)**: forks for chat exports, Telegram channels and username searches, whose results can be imported as nodes.
* **[Intelligence Field Notes](https://github.com/SOsintOps/intelligence-field-notes)**: the method all of them share.
