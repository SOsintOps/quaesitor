# Security Policy

## Supported Versions

Only the latest release on `main` receives fixes. Update with `update.bat` on Windows, or `git pull` followed by `pip install -r requirements.txt` elsewhere.

## The Security Model

Quaesitor is a single-user program that runs on the analyst's own computer.

- **No authentication.** Whoever reaches the port can read and change every case. The server listens on `127.0.0.1` only; never expose its port beyond localhost, and never publish it from a container or a virtual machine without a reverse proxy with login in front of it.
- **Development server.** Started from source, the program runs on the Flask development server with debug mode on, which is meant for a local machine and never for a network. The executable built with `scripts/build_app.py` turns debug mode off.
- **Data on disk, unencrypted.** Cases live in `data/` (or in the folder named by `DATA_DIR`) and the documents to index in `sources/`. Protect them with the disk encryption of the operating system.
- **Keys in plain text.** `chatbot.conf` and `services.conf` hold the API keys of the AI provider, OpenSanctions and Epieos. They are ignored by git and must never be committed or shared.
- **Online services.** Nothing leaves the computer unless the analyst turns on a service: the AI chatbot, OpenSanctions or Epieos. Each search sends its query to that service, and Epieos charges credits for every search.

## Reporting a Vulnerability

Do not open a public issue for a vulnerability. Use the private report of GitHub instead: **Security → Report a vulnerability** on the [SOsintOps/quaesitor](https://github.com/SOsintOps/quaesitor/security/advisories/new) repository. Describe the version, the steps to reproduce the problem and its impact.

Expect a first answer within two weeks. Problems in the original OSInt Graph that the fork has not changed are reported to its author as well, once fixed here.
