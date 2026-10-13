# -*- coding: utf-8 -*-
"""End-to-end smoke test of an installed Quaesitor, through its HTTP API.

Starts the server from an installed copy (the way the Argos and Speculator
launchers do: DATA_DIR and PORT in the environment), then exercises the
features that depend on the platform: cases, nodes, CSV import, Follow the
Money import and export, Epieos import from file, document sources with OCR
(txt, docx, pdf, png), restart and persistence. Prints a summary and exits
non-zero if a step fails. Nothing leaves the machine.

    python scripts/smoke_test.py --app-dir <install dir> --python <venv python>
                                 --data-dir <archive dir> --port 5000 [--keep]
"""
# "Experientia docet." (Tacitus, Histories)
# Experience teaches.
import argparse, base64, json, os, shutil, signal, subprocess, sys, tempfile, time, urllib.request, urllib.error

RESULTS = []


def step(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'OK' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""), flush=True)
    return ok


def api(base, path, body=None, method=None, raw=False):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            blob = r.read()
            return r.status, (blob if raw else json.loads(blob or b"{}"))
    except urllib.error.HTTPError as e:
        blob = e.read()
        try:
            return e.code, json.loads(blob)
        except Exception:
            return e.code, {"raw": blob[:200].decode("utf-8", "replace")}


def wait_http(base, seconds):
    for _ in range(seconds * 2):
        try:
            urllib.request.urlopen(base + "/", timeout=2).read(1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def start(python, app_dir, data_dir, port, log):
    env = dict(os.environ, DATA_DIR=data_dir, PORT=str(port))
    return subprocess.Popen([python, "app.py"], cwd=app_dir, env=env, stdout=log, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True)


def stop(proc):
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode("ascii")


def make_fixtures(folder, python):
    """txt, docx, pdf and png with known words; the png needs OCR."""
    os.makedirs(folder, exist_ok=True)
    open(os.path.join(folder, "nota.txt"), "w", encoding="utf-8").write(
        "Verbale di perquisizione presso l'abitazione di Mario Rossi, via Garibaldi 12.\n")
    code = r'''
import os, sys
folder = sys.argv[1]
from docx import Document
d = Document(); d.add_paragraph("Verbale di sequestro di un telefono cellulare Samsung."); d.save(os.path.join(folder, "verbale.docx"))
# minimal text PDF, one page, Helvetica
txt = "Rogatoria internazionale per il conto bancario IT60X0542811101000000123456"
objs = []
objs.append("<< /Type /Catalog /Pages 2 0 R >>")
objs.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
objs.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>")
stream = "BT /F1 14 Tf 50 780 Td (" + txt + ") Tj ET"
objs.append("<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
out = "%PDF-1.4\n"; offs = []
for i, o in enumerate(objs, 1):
    offs.append(len(out)); out += "%d 0 obj\n%s\nendobj\n" % (i, o)
xref = len(out)
out += "xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + "".join("%010d 00000 n \n" % o for o in offs)
out += "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
open(os.path.join(folder, "rogatoria.pdf"), "w", encoding="latin-1").write(out)
from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGB", (1400, 300), "white"); dr = ImageDraw.Draw(img)
font = None
for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"):
    if os.path.exists(p):
        font = ImageFont.truetype(p, 56); break
if font is None:
    font = ImageFont.load_default(size=56)
dr.text((40, 60), "Procura della Repubblica di Napoli", fill="black", font=font)
dr.text((40, 160), "citta perche attivita", fill="black", font=font)
img.save(os.path.join(folder, "scansione.png"))
img2 = Image.new("RGB", (1400, 200), "white"); dr = ImageDraw.Draw(img2)
dr.text((40, 60), "città perché attività", fill="black", font=font)
img2.save(os.path.join(folder, "accenti.png"))
print("fixtures ok")
'''
    r = subprocess.run([python, "-c", code, folder], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()[-300:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-dir", required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--keep", action="store_true", help="keep the archive and fixtures")
    a = ap.parse_args()
    app_dir = os.path.abspath(a.app_dir)
    data_dir = os.path.abspath(a.data_dir)
    base = f"http://127.0.0.1:{a.port}"
    shutil.rmtree(data_dir, ignore_errors=True)
    os.makedirs(data_dir, exist_ok=True)
    fixtures = os.path.join(data_dir, "_fonti_test")
    logpath = os.path.join(data_dir, "smoke_server.log")
    log = open(logpath, "ab")
    print(f"app={app_dir}\npython={a.python}\ndata={data_dir}\nport={a.port}", flush=True)

    proc = start(a.python, app_dir, data_dir, a.port, log)
    try:
        if not step("server answers within 40 s", wait_http(base, 40)):
            raise SystemExit(1)
        st, body = api(base, "/", raw=True)
        step("GET / is Quaesitor", st == 200 and b"<title>Quaesitor</title>" in body)
        st, s = api(base, "/api/sources/status")
        step("OCR available", s.get("ocr_available"), f"reason={s.get('ocr_reason')!r} can_install={s.get('ocr_can_install')}")

        st, c = api(base, "/api/cases/add", {"name": "linux smoke"})
        step("create case", st == 200 and c.get("ok"), str(c.get("case", {}).get("id")))

        st, n1 = api(base, "/api/node/add", {"ntype": "name", "cognome": "Rossi", "nome": "Mario"})
        step("add person node", st == 200 and n1.get("ok"), n1.get("id", n1.get("error")))
        st, n2 = api(base, "/api/node/add", {"ntype": "email", "value": "mario.rossi@example.com", "parent": n1.get("id", "")})
        step("add e-mail node linked", st == 200 and n2.get("ok"), n2.get("id", n2.get("error")))
        st, n3 = api(base, "/api/node/add", {"ntype": "company", "value": "Delta Srl", "name": "Delta Srl", "parent": n1.get("id", "")})
        step("add FtM company node", st == 200 and n3.get("ok"), n3.get("id", n3.get("error")))
        st, n4 = api(base, "/api/node/add", {"ntype": "name", "cognome": "Петров", "nome": "Иван", "parent": n1.get("id", "")})
        step("add Cyrillic name (transliteration)", st == 200 and n4.get("ok"), str(n4.get("label") or n4.get("error")))

        csv = os.path.join(app_dir, "examples", "sample_import_en.csv")
        st, p = api(base, "/api/import/preview", {"filename": "sample_import_en.csv", "data": b64(csv)})
        step("CSV preview", st == 200 and p.get("ok") and p.get("total", 0) > 0, f"rows={p.get('total')} cols={p.get('columns')}")
        st, r = api(base, "/api/import/commit", {"filename": "sample_import_en.csv", "data": b64(csv)})
        step("CSV import", st == 200 and r.get("nodes", 0) > 0, f"nodes={r.get('nodes')} links={r.get('links')} errors={len(r.get('errors', []))}")

        ftmf = os.path.join(app_dir, "scripts", "ftm", "sample.ftm.jsonl")
        st, i = api(base, "/api/ftm/inspect", {"filename": "sample.ftm.jsonl", "data": b64(ftmf)})
        step("FtM inspect", st == 200 and i.get("ok"), f"schemas={list(i.get('schemas', {}))[:6]}")
        st, r = api(base, "/api/ftm/import", {"filename": "sample.ftm.jsonl", "data": b64(ftmf), "dataset": "sample"})
        prog = {}
        for _ in range(120):
            st2, prog = api(base, "/api/ftm/progress")
            if not prog.get("running") and (prog.get("finished") or prog.get("done") is not None and prog.get("stage") in ("done", "finished", "")):
                break
            time.sleep(0.5)
        step("FtM import", st == 200 and not prog.get("error"), json.dumps({k: prog.get(k) for k in ("stage", "done", "total", "error", "nodes", "links", "finished") if k in prog}))

        ep = os.path.join(app_dir, "scripts", "epieos", "sample_email.json")
        eptxt = open(ep, encoding="utf-8").read()
        try:
            q = next((m.get("query") for m in json.loads(eptxt).get("result", {}).values() if isinstance(m, dict) and m.get("query")), None)
        except Exception:
            q = None
        q = q or "john.doe@example.com"
        st, ne = api(base, "/api/node/add", {"ntype": "email", "value": q})
        st, r = api(base, "/api/imports/add", {"anchor": ne.get("id", ""), "filename": f"search_{q}.json", "content": eptxt})
        step("Epieos import from file", st == 200 and r.get("ok", r.get("count") is not None or "id" in r), str({k: r.get(k) for k in list(r)[:4]}))

        ok, detail = make_fixtures(fixtures, a.python)
        step("fixtures (txt, docx, pdf, png)", ok, detail)
        st, r = api(base, "/api/sources/scan", {"folder": fixtures})
        step("sources scan started", st == 200 and r.get("started"), str(r))
        prog = {}
        for _ in range(240):
            st2, prog = api(base, "/api/sources/progress")
            if prog.get("finished") or (not prog.get("running") and prog.get("total")):
                break
            time.sleep(0.5)
        step("sources scan finished", prog.get("finished") and not prog.get("error"), f"done={prog.get('done')} total={prog.get('total')} summary={prog.get('summary')}")
        for term, where in (("perquisizione", "txt"), ("sequestro", "docx"), ("rogatoria", "pdf"), ("Procura", "png/OCR"), ("perche", "png/OCR plain"), ("perché", "png/OCR accented")):
            st, r = api(base, "/api/sources/search", {"q": term, "mode": "partial"})
            hits = r.get("files") or r.get("results") or r.get("items") or []
            step(f"search '{term}' in {where}", st == 200 and len(hits) > 0, f"hits={len(hits)}" if st == 200 else str(r))

        # Cognitor bundle (1.6.0): read from a path of this computer, photos and transcripts
        bundle = os.path.join(app_dir, "tests", "fixtures", "cognitor_sample.cognitor.zip")
        st, i = api(base, "/api/ftm/inspect", {"path": bundle})
        step("Cognitor bundle inspect", st == 200 and i.get("bundle") and i.get("images") == 6,
             f"case={i.get('case_name')} images={i.get('images')} transcripts={i.get('transcripts')}")
        st, r = api(base, "/api/ftm/import", {"path": bundle})
        prog = {}
        for _ in range(120):
            st2, prog = api(base, "/api/ftm/progress")
            if prog.get("finished") and not prog.get("running"):
                break
            time.sleep(0.5)
        step("Cognitor bundle import", st == 200 and not prog.get("error") and prog.get("images") == 6,
             json.dumps({k: prog.get(k) for k in ("nodes", "links", "images", "transcripts", "error")}))
        for _ in range(120):
            st2, sp = api(base, "/api/sources/progress")
            if not sp.get("running"):
                break
            time.sleep(0.5)
        st, g = api(base, "/api/graph")
        pics = [n for n in g.get("nodes", []) if n.get("pic")]
        step("Cognitor persons show their photo", st == 200 and len(pics) >= 2, f"persons with photo={len(pics)}")

        st, blob = api(base, "/api/ftm/export", raw=True)
        lines = [l for l in blob.decode("utf-8", "replace").splitlines() if l.strip()] if st == 200 else []
        step("FtM export", st == 200 and len(lines) > 0, f"entities={len(lines)}")
        st, g = api(base, "/api/graph")
        n_before = len(g.get("nodes", []))
        step("graph", st == 200 and n_before > 0, f"nodes={n_before} edges={len(g.get('edges', []))}")

        stop(proc)
        proc = start(a.python, app_dir, data_dir, a.port, log)
        step("restart", wait_http(base, 40))
        st, g = api(base, "/api/graph")
        step("archive persists after restart", st == 200 and len(g.get("nodes", [])) == n_before, f"nodes={len(g.get('nodes', []))}")
    finally:
        stop(proc)
        log.close()
    txt = open(logpath, encoding="utf-8", errors="replace").read()
    tb = txt.count("Traceback")
    step("no traceback in server log", tb == 0, f"tracebacks={tb} log={logpath}")
    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} steps OK" + (f"; FAILED: {failed}" if failed else ""))
    if not a.keep and not failed:
        shutil.rmtree(fixtures, ignore_errors=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
