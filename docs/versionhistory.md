# Version History

Changelog of all releases and improvements to Quaesitor, the SOsintOps fork of OSInt Graph. Version numbers start from the upstream release the fork is based on; bug fixes bump the patch number (x.y.Z), new features the minor one (x.Y.0).

---

## Planned

What is queued and under consideration is in [Ideas & Roadmap](todo.md): Docker packaging, the English translation of the remaining Italian pages, a customising guide, the follow-ups of the Cognitor bridge.

---

## 1.7.3 — 2026

- **Fixed:** [Link Analysis Guidelines](link-analysis.md) no longer say that the 6 x 6 (Admiralty) system "converts easily": the two systems differ by more than the number of grades, and information graded on the 6 x 6 must be re-graded on the 4 x 4 questions, as the [Intelligence Field Notes](https://github.com/SOsintOps/intelligence-field-notes/blob/main/docs/source-evaluation.md#converting-from-the-6-x-6-admiralty-system) explain. *Further Reading* links the UNODC manual for front-line law enforcement.
- **Fixed:** [Guidelines](guidelines.md): tradecraft standard 5 is *customer relevance*, as in ICD 203, and the *Timely* standard speaks of customers; the likelihood table matches the Field Notes and recommends the first row; ICD 203 and the UNODC manual are linked at their first mention; British spelling (*judgement*).
- **Fixed:** The English section of the built-in manual spells the noun *licence*.
- **Docs:** FAQ: new group *Method & Analysis* (where the 4 x 4 grade of a link goes, why the 4 x 4 and not the 6 x 6, solid or dashed links, why the graph is not the report, how chats, Telegram channels and username searches become nodes), with links to the related SOsintOps projects; the related-projects list names more of them. `docs/field-notes/` updated to the Field Notes 0.1.2.
- **Changed:** The 1.5.0 entry no longer names the development repository.

---

## 1.7.2 — 2026

- **Docs:** [Guidelines](guidelines.md) and [Link Analysis Guidelines](link-analysis.md) aligned with the [Intelligence Field Notes](https://github.com/SOsintOps/intelligence-field-notes), the notes on analytic standards, source evaluation, estimative language and report writing now shared by all the SOsintOps tools: the likelihood table says to use one row only, a *Writing the Report* section joins the graph to the written product, and every text in *Further Reading* is linked. `docs/field-notes/` carries an offline copy of the notes.
- **Docs:** FAQ: new entry *Are there related SOsintOps projects?*; the documentation entry points to the Field Notes.
- **Fixed:** FAQ and README named the uninstaller `disinstall.bat`; it is `uninstall.bat` since 1.5.0. The OCR answer of the FAQ showed the Windows path `tools\tesseract\tessdata` with tab characters instead of backslashes. The README names the maintainer as the credits do, Sitticus. *Planned* no longer lists the fork's own name, given in 1.5.0; a definitive logo is still wanted.

---

## 1.7.1 — 2026

- **New:** Colour icons for the two node types that still had a Font Awesome glyph, Follow the Money articles (a newspaper) and calls (a handset).
- **New:** Colour icons for the sub-types. A drug picks its icon from the substance: pills for MDMA, amphetamines, benzodiazepines and pharmaceutical opioids, a leaf for khat, kratom and mescaline, a droplet for GHB, a microscope for an unidentified substance, besides the cannabis, syringe and vial of earlier versions. An identity document picks it from its kind (identity card, driving licence, residence permit, health card, visa and travel document, ID badge), a financial document likewise (invoice, insurance policy, balance sheet, ledger, hidden accounts, transport document, company registry extract, tax return), a judicial act likewise (arrest and custody, search and seizure, interviews, interception, complaints, police reports, notices to the suspect, letters rogatory), and a device too (smartphone, desktop, hard disk, USB stick, router, GPS tracker, and an encrypted phone with a padlock that no longer looks like the ordinary phone). A sub-type without its own icon shows the icon of its type.
- **Docs:** `scripts/icons/labels.json` labels every cut of two more sheets, so the next icons can be chosen by name. [Graph Entities](ontology.md) names the colour icon of every type and, for drugs, documents, judicial acts and devices, which value picks which icon (`scripts/make_ontology_doc.py`).

---

## 1.7.0 — 2026

- **New:** Colour icons for the node types: people, targets, unknown persons, phones, e-mails, profiles, places, vehicles, documents, weapons, drugs, money, companies, vessels and the other Follow the Money types, 78 icons in all. They come from icon sheets generated with ChatGPT and Gemini, cut and assigned by `scripts/icons/`; see the FAQ "Where do the node icons come from?". The Font Awesome glyphs stay as fallback for the types without an icon, and social profiles keep the logo of their platform.

---

## 1.6.1 — 2026

- **Changed:** The credits line and the credits window name the fork's maintainer, Sitticus (osintops.com). The attribution to Andrea Cumini that `NOTICE` requires stays complete and legible on its own line ("Based on OSInt Graph by Andrea Cumini - andrea@osintinfo.net - www.osintinfo.net") and as an "Original project" section of the credits window.
- **Docs:** The third-party notices state the licences of the transcription models: the WeSpeaker models follow the CC BY 4.0 licence of the VoxCeleb dataset; the Argos `en_it` package declares no licence of its own (trained on OPUS data, it includes Stanza models under Apache-2.0).

---

## 1.6.0 — 2026

- **New:** Video transcription, optional. **🎙 Transcribe video** in the toolbar transcribes a video or audio file of this computer with faster-whisper, tells the speakers apart (diarization) and, on request, translates to English or Italian. The video becomes a node with the transcript, every voice a person node "Speaker k (file)" linked to it by "speaks in", and the text goes into the sources folder, where the search finds it. Transcribing the same file again updates the same nodes. Everything runs on this computer; the models download once, on first use. The modules come from Cognitor, released by their holder under the GPL as part of Quaesitor (`audio/`, see `audio/README.md`); the packages are in `requirements-audio.txt`, offered by `install.bat` and updated by `update.bat` where installed.
- **New:** Cognitor bundles. A `.cognitor.zip` written by Cognitor's **Export (FollowTheMoney)** opens in the Follow the Money import: persons, unknown groups and voices, face photos, co-appearances, videos with their transcripts. The face photos are copied under `data/media/cognitor/<case>/` and become photo nodes linked to the persons, and a person shows its first photo as its icon. The transcripts are copied to the sources folder under `cognitor/<case>/` and indexed, so the sources search finds what was said. Every file of the bundle is checked against the sha256 of its manifest; names outside `media/` and `transcripts/` and images that are not images are refused.
- **New:** "Seen together" links (co-appearances from Cognitor) are drawn in amber, thicker with more shared photos and video segments, and carry the counts in their label; "speaks in" links are dashed violet, "appears in" dotted teal.
- **New:** The Follow the Money import reads a file by its path on this computer, next to the upload. The upload stops at 20 MB, which a bundle with photos exceeds; the path does not.
- **Changed:** Follow the Money import fixes. Every node entity gets a row of its own, so a person reached only through another entity (a photo that pictures it) no longer vanishes when that row fails. An `Image` without its file is left out instead of failing. Native types (Video, Document, Audio...) keep `bodyText`, `description`, `summary`, `notes` and `sourceUrl`, which were dropped. A partial birth date (`1980`) stays a field of the card instead of failing the row. Free properties named like a fixed column (`title`, `type`, `service`...) get an `ftm_` prefix instead of overriding the label, the node type or the platform. `notes` and `summary` are joined instead of one overwriting the other.
- **Changed:** The Follow the Money export writes a photo node as an `Image` with its file name and caption, not as a `Note`; re-imported on the same computer, the photo comes back as a photo. A "seen together" link exported and imported again keeps its label instead of nesting it, so the round trip Cognitor -> Quaesitor -> export -> import doubles nothing.
- **New:** A test suite (`tests/`, pytest from `requirements-dev.txt`, run with `.venv\Scripts\python.exe -m pytest`) covers the import fixes and the bundle; `scripts/smoke_test.py` imports the sample bundle too.

---

## 1.5.2 — 2026

- **Changed:** The Windows scripts are in English and renamed: `install.bat`, `start.bat`, `update.bat`, `uninstall.bat` (formerly `installa`, `avvia`, `aggiorna`, `disinstalla`). Same behaviour; prompts answer `y`/`N`.
- **Removed:** The screenshots of the original program (`screen.png`, the eighteen images of the built-in manual, the three in the README): they showed the OSInt Graph interface. The manual keeps the captions as text until Quaesitor's own screenshots are taken.

---

## 1.5.1 — 2026

- **Improved:** OCR uses every Tesseract language pack installed on the machine, English last (or `TESSERACT_LANG`), so accented and non-Latin text is read instead of English-only; the languages in use are reported by `/api/sources/status`.
- **New:** `scripts/smoke_test.py`: end-to-end test of an installed copy through the HTTP API (cases, nodes, CSV, Follow the Money import and export, Epieos from file, document sources with OCR, restart). Used to verify the Linux installs of Argos (Ubuntu Budgie 26.04 base, Python 3.12 and 3.14) and Speculator (Debian 13, Python 3.13): 27 of 27 steps on each.
- **Docs:** README "Linux" install section; FAQ entries on Linux and on OCR languages.

---

## 1.5.0 — 2026

First public release.

- **New:** The interface carries the fork's own name, a provisional text wordmark and a "Q" icon (window title, left panel, favicon, executable name `Quaesitor.exe`, built-in manual, licences window), as `NOTICE` point 3 requires of a distributed modified version. The credits line, the credits window, the licences window and the source headers keep the attribution of Andrea Cumini unchanged; a "Quaesitor fork: SOsintOps" link sits next to the credits line.
- **Changed:** Development moves to a separate, private development repository; the public repository `quaesitor` carries the upstream history and one commit per release, without internal working notes.
- **Docs:** README, FAQ and roadmap no longer point to pages kept in the development repository.

---

## 1.4.0 — 2026

- **Changed:** The fork is named **Quaesitor** (repository `SOsintOps/quaesitor`); the name "OSInt Graph", the logo and the icon stay the original author's.
- **Changed:** Branches: the fork branch `sosintops` is now `main`; the upstream mirror, formerly `main`, is now `osintgraph`.
- **Docs:** README rewritten as Quaesitor's own, in the SOsintOps layout: badges, key features, screenshots, requirements, installation, program sections, documentation, repository, how to use, references, contributing, credits, licence, disclaimer. The upstream README lives in the `osintgraph` branch.
- **Docs:** FAQ (`docs/faq.md`) with table of contents: the project and its name, licence and distribution, installation, data and privacy, AI, Follow the Money and OpenSanctions, Epieos, non-Latin names, integrations, help.
- **Docs:** Link Analysis Guidelines (`docs/link-analysis.md`), rewritten from chapter 6 of the UNODC *Criminal Intelligence: Manual for Analysts* (2011), with the 4 x 4 evaluation system and a mapping of each step onto the program's features.
- **Docs:** This version history, the Guidelines (analytic standards, 5W1H, OPSEC, adapted from Exploratores), Ideas & Roadmap and the Graph Entities catalogue in English, all in the layout shared with the other SOsintOps projects.
- **New:** One Latin proverb on the bonds between people, as a comment, in every hand-written script (Python, Windows batch, JavaScript) and in the header template of the generated ontology.

---

## 1.3.0 — 2026

Third round of 2026-10-09 (evaluation report, section 11).

- **New:** Epieos: `epieos.py` adapter from the API responses to the records of the OSINT-export engine; breach nodes (hibp), "registered on" account nodes (holehe, phonechecker), organisation nodes (LinkedIn companies and schools); social profiles identified by the service's user id, labelled with the profile name, no person node created from a profile.
- **New:** Routes `/api/epieos/config`, `/schema`, `/search`, `/import`, `/searches`; credits and rate limits read from the response headers; 401/402/403/429/500 explained; a repeated search replaces the previous import.
- **New:** Sidebar group with switch (warning on enabling), configuration with schema reading, status with remaining credits, search box, saved searches; **Epieos** button on e-mail and phone cards; confirmation dialog with modules and credits; routing of saved JSON responses dropped on the import; six languages.
- **Docs:** Epieos guide; `docs/ontology.md` (generated catalogue of all node types with fields, identity and FtM equivalence; English since 1.4.0); report section 11.

---

## 1.2.0 — 2026

Second round of 2026-10-09 (evaluation report, section 10).

- **New:** All 41 non-built-in Follow the Money node schemata as native types (727 fields, Italian labels, fr/de/es/ar from FtM, six groups, hidden `ftmId` identity, `ftm` prefix for four name clashes), generated by `scripts/ftm/make_ftm_types.py` into `ontology_ftm.py` and `ftm_schema.json`.
- **New:** Whole-dataset FtM import: inspection, filters, background batches, `ftm_ids` table, update on re-import, 409 on a concurrent import.
- **New:** Typed relations: the 17 FtM edge schemata with their fields on links, automatic label, picker in the link editor and the add-link forms.
- **New:** Export of a case as FtM JSON lines; lossy cases declared; ids registered.
- **New:** OpenSanctions search, match and nested import; settings in `services.conf`; off by default.
- **New:** Windows scripts `installa.bat`, `avvia.bat`, `aggiorna.bat`, `disinstalla.bat`.
- **Changed:** Latin form of non-Latin names as a node attribute (two-line label, "Transliteration" row); the "Separate Latin nodes" switch restores the twin nodes.
- **Docs:** Follow the Money guide; report section 10; Docker queued with its requirements.

---

## 1.1.0 — 2026

First round of 2026-10-09 (evaluation report, sections 2 to 9).

- **New:** `sighting` node type and the first Follow the Money node types; native FtM import.
- **New:** Transliteration dictionary window: manual editing, CSV import and export, collection from the graph, AI proposals.
- **New:** Chinese: spaced pinyin, search from two characters, source search on text without spaces.
- **Fixed:** Identity keys keep combining marks: Devanagari, Thai and kana with dakuten no longer collapse different names into one node.
- **Fixed:** Invalid escape sequence warning in `sources.py`.
- **Docs:** Evaluation report: evaluation of OSInt Graph as case layer, Follow the Money and non-Latin scripts; Ollama setup guide; PowerShell-safe test instructions.

---

## 1.0.0 — 2026

- **Upstream:** OSInt Graph by Andrea Cumini, first public release of 2026-10-07 (upstream tag `1.0.0`, commit `4125363`). Everything in this version is his work: the fork starts here and the branch `osintgraph` stays a mirror of it.
