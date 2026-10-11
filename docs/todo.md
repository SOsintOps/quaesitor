# Ideas & Roadmap

This file collects ideas, requirements and potential improvements to be evaluated for future implementation. Items are added here as they are identified; they are moved to the [version history](versionhistory.md) once implemented.

---

## Pending

### Packaging

- **Docker:** a `Dockerfile` (python:3.12-slim, `tesseract-ocr` with the ita, eng, chi_sim, rus and ara language packs, the app bound to 127.0.0.1 behind the published port) and a `docker-compose.yml` with volumes for `data/`, `fonti/`, `chatbot.conf` and `services.conf`. Ollama stays outside the image (host or second service). The native folder picker is unavailable in a container; the manual path entry already covers it. The program has no authentication: never publish the port beyond localhost without a proxy with login. The venv plus the four `.bat` files remain the primary Windows installation. Decided on 2026-10-09, not started.

### Name and Identity of the Fork

- **Definitive logo:** the interface carries a provisional text wordmark and a "Q" icon since 1.5.0; a designed logo and icon are still wanted. The author's credits line, credits window and licences window stay as they are.

### Documentation

- **Screenshots:** take Quaesitor's own screenshots for the built-in manual (the `IMG` map in `static/manual/manuale.html` lists the eighteen views, `fig()` renders them again once the files are back) and for the README.
- **English translation** of the Follow the Money guide, the Epieos guide and the Ollama setup guide, written in Italian during development and kept in the development repository until translated.
- **Customising guide:** an equivalent of the Exploratores *Customise* page for this program: how to add an investigative node type (`ontology.py` and `ontology_i18n.py`), regenerate the Follow the Money ontology after a new release of the `followthemoney` package, add an interface language (`static/i18n.js`), configure `chatbot.conf` and `services.conf`, and adapt the OSINT-export import (`handle_record`) to a new tool.

### Integrations

- **Cognitor:** an exporter on the Cognitor side writing persons, photos and co-appearances in Follow the Money format (`Person`, `Image`, `UnknownLink` or `Associate`), so that a face-recognition case can be imported here without a bridge. Embeddings and unknown clusters have no FtM schema; an extension of the ontology is to be proposed upstream.

### Verification on a Real Account

- **Epieos:** one real search on a known identifier to compare the nodes created with the Epieos web page (everything so far was verified against a local fake server built from the OpenAPI specification).
- **OpenSanctions:** one real call to `api.opensanctions.org` with a key (verified so far against a local fake yente).

### Open Ideas

- A romanised shadow index for cross-script search in sources ("petrov" finding "Петров"); the dictionary window covers the node side of that need.
- Chinese, Japanese or Korean interface languages.
- Rendering of CJK labels on the canvas, to be checked on a machine with CJK fonts.
