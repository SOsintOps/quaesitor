# -*- coding: utf-8 -*-
"""Takes the screenshots of the built-in manual (and of the README) from a running copy
of Quaesitor, in English, with the case study of examples/got_kinship.csv (the family
network of Game of Thrones, A Wiki of Ice and Fire, CC BY-SA) and its hypotheses file.

    .venv\\Scripts\\python.exe -m pip install --group docs
    .venv\\Scripts\\python.exe scripts\\screenshots.py [--out <folder>] [--keep]

What it does:
  * copies app.py and quaesitor/ of the last commit (git archive HEAD) to a temporary
    folder and starts the server there, with an empty DATA_DIR and a free port: the
    chatbot.conf and services.conf of this folder (keys, endpoints) are never read;
  * drives the installed Chrome (Playwright, channel "chrome": no browser download),
    1440 x 900, interface in English, animations off;
  * writes the 19 PNG files named in the IMG map of quaesitor/static/manual/manual.html
    into quaesitor/static/manual/img/ (or --out), optimised with Pillow.
Nothing leaves the computer: the AI settings point to a local address and stay off.
"""
# "Ut pictura poesis." (Horace, Ars Poetica)
# As is painting, so is poetry.
import argparse, base64, io, json, os, shutil, signal, socket, subprocess, sys, tarfile, tempfile, time
import urllib.request

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "examples", "got_kinship.csv")
HYP = os.path.join(ROOT, "examples", "got_kinship_hypotheses.csv")
OUT = os.path.join(ROOT, "quaesitor", "static", "manual", "img")
VIEW = {"width": 1440, "height": 900}
NO_MOTION = ("*,*::before,*::after{transition:none!important;animation:none!important;"
             "caret-color:transparent!important}")
NAMES = {
    "first": "01-first-start.png", "over": "02-overview.png", "search": "03-search.png",
    "card": "04-node-card.png", "add": "05-new-node.png", "edge": "06-edit-link.png",
    "edit": "07-edit-values.png", "ctx": "08-context-menu.png", "link": "09-connect-nodes.png",
    "imp1": "10-import-1-file.png", "imp2": "11-import-2-columns.png",
    "imp3": "12-import-3-preview.png", "ai": "13-ai-settings.png", "lic": "14-licences.png",
    "caseEdit": "15-edit-case.png", "manual": "16-manual-changes.png",
    "sideTop": "17-panel-top.png", "sideBottom": "18-panel-bottom.png", "marks": "19-corner-marks.png",
}
TARGET = "cy.nodes('[ntype=\"target\"]')[0]"


def by_label(label):
    """JavaScript expression: the node on the graph with that label."""
    return f"cy.nodes().filter(n => n.data('label') === {json.dumps(label)})[0]"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def program_copy(dest):
    """app.py and quaesitor/ of HEAD, without the settings files of this folder."""
    tar = subprocess.run(["git", "archive", "--format=tar", "HEAD", "app.py", "quaesitor"],
                         cwd=ROOT, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        t.extractall(dest, filter="data")


def start_server(app_dir, data_dir, port):
    env = dict(os.environ, DATA_DIR=data_dir, PORT=str(port), PYTHONIOENCODING="utf-8",
               CHATBOT_ENABLED="false", CHATBOT_ENDPOINT="http://127.0.0.1:11434",
               CHATBOT_MODEL="gemma3:12b", CHATBOT_API_KEY="")
    env.pop("SOURCES_DIR", None)
    log = open(os.path.join(data_dir, "server.log"), "w", encoding="utf-8")
    kw = {} if os.name == "nt" else {"start_new_session": True}
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=app_dir, env=env, stdout=log,
                            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kw)
    base = f"http://127.0.0.1:{port}"
    for _ in range(80):
        try:
            urllib.request.urlopen(base + "/", timeout=2).read(1)
            return proc, base
        except Exception:
            time.sleep(0.5)
    stop_server(proc)
    sys.exit("the server did not start: see " + log.name)


def stop_server(proc):
    if os.name == "nt":
        # no process groups: taskkill /T also stops the reloader's child server
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            proc.terminate()
    try:
        proc.wait(10)
    except subprocess.TimeoutExpired:
        pass


def api(base, path, body):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def import_csv(base, path):
    data = base64.b64encode(open(path, "rb").read()).decode("ascii")
    r = api(base, "/api/import/commit", {"filename": os.path.basename(path), "data": data})
    if not r.get("ok"):
        sys.exit(f"import of {path} failed: {r}")
    return r


def optimise(path):
    """Fewer colours, same look: UI screenshots compress well as palette PNG."""
    im = Image.open(path).convert("RGB")
    im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(
        path, optimize=True)


class Shots:
    def __init__(self, page, out):
        self.page, self.out = page, out

    def save(self, key, selector=None, clip=None):
        path = os.path.join(self.out, NAMES[key])
        self.page.evaluate("document.activeElement && document.activeElement.blur()")
        self.page.wait_for_timeout(250)
        if selector:
            self.page.locator(selector).first.screenshot(path=path)
        else:
            self.page.screenshot(path=path, clip=clip)
        optimise(path)
        print("  ", NAMES[key])

    def ready(self):
        p = self.page
        p.wait_for_function("typeof cy !== 'undefined' && cy && document.querySelector('#caseSel')")
        p.add_style_tag(content=NO_MOTION)
        p.wait_for_timeout(400)

    def settle(self):
        self.page.evaluate("""() => { cy.nodes('.fresh').removeClass('fresh');
            runLayout({fit: true, animate: false}); }""")
        self.page.wait_for_timeout(800)

    def close_modals(self):
        """The windows are shown and hidden with the hidden attribute, as the app does."""
        self.page.evaluate("""() => document.querySelectorAll('[id$="modal"]').forEach(
            m => { m.hidden = true; })""")
        self.page.wait_for_timeout(200)

    def open(self, script, box):
        self.close_modals()
        self.page.evaluate(script)
        self.page.wait_for_selector(box, state="visible")


def take_all(s, page, base):
    # 1. first start: no case, the "New case" window opens by itself
    page.goto(base + "/")
    s.ready()
    page.wait_for_selector("#casemodal-box", state="visible")
    s.save("first", "#casemodal-box")

    # the case of the screenshots: the family network of the case study
    api(base, "/api/cases/add", {
        "name": "Blood of the Dragon",
        "description": "Case study: the family network of Game of Thrones and House of the Dragon "
                       "(A Wiki of Ice and Fire, CC BY-SA)."})
    import_csv(base, CSV)
    import_csv(base, HYP)
    page.reload()
    s.ready()
    page.evaluate("document.querySelector('#loadTargets').click()")
    page.wait_for_function("cy.nodes('[ntype=\"target\"]').length > 0")
    tid = page.evaluate(f"{TARGET}.id()")
    api(base, "/api/note", {"id": tid, "note": "Open question: who are the parents of Jon Snow? The "
                                               "source names Eddard Stark as father and two mothers, "
                                               "Wylla and Ashara Dayne (conflicting records). Hypothesis "
                                               "under test: Rhaegar Targaryen and Lyanna Stark."})
    page.evaluate("() => syncGraph()")
    page.wait_for_timeout(600)
    for sel in (TARGET, by_label("Eddard Stark"), by_label("Rhaegar Targaryen")):
        page.evaluate(f"() => {{ const n = {sel}; if (n) toggleExpand(n); }}")
        page.wait_for_timeout(700)
    # a family tree: one row per generation, labels explained by the key
    page.select_option("#gsLabels", "off")
    page.evaluate("() => { cy.nodes('.fresh').removeClass('fresh'); setLayout('dagre', '#lyLevels'); }")
    page.wait_for_timeout(1200)
    page.evaluate("() => { runLayout({fit: true, animate: false}); buildChartKey(); }")
    page.wait_for_timeout(900)

    # 2. overview, 17-18 panel
    s.save("over")
    s.save("sideTop", "#side")
    page.evaluate("document.querySelector('#side').scrollTop = 1e6")
    page.wait_for_timeout(200)
    s.save("sideBottom", "#side")
    page.evaluate("document.querySelector('#side').scrollTop = 0")

    # 3. search
    page.fill("#search", "Snow")
    page.press("#search", "Enter")
    page.wait_for_selector("#search-results li", state="visible")
    s.save("search", ".search-container")
    page.fill("#search", "")
    page.mouse.click(1420, 880)
    page.wait_for_timeout(200)

    # 8. context menu on the background
    page.evaluate("document.querySelector('#chartkey').hidden = true")   # it covers that corner
    page.mouse.click(1300, 820, button="right")
    page.wait_for_selector("#ctxmenu", state="visible")
    box = page.locator("#ctxmenu").bounding_box()
    s.save("ctx", clip={"x": box["x"] - 24, "y": box["y"] - 24,
                        "width": box["width"] + 48, "height": box["height"] + 48})
    page.keyboard.press("Escape")
    page.evaluate("() => buildChartKey()")

    # the windows below are taller than the screen: a taller viewport shows them whole
    page.set_viewport_size({"width": VIEW["width"], "height": 1150})
    page.wait_for_timeout(300)

    # 4. card, 7. edit values, 5. new node
    s.open(f"() => openModal({TARGET})", "#modal-box")
    s.save("card", "#modal-box")
    s.open(f"() => openEditModal({TARGET})", "#editmodal-box")
    s.save("edit", "#editmodal-box")
    s.open(f"() => openAdd({TARGET})", "#addmodal-box")
    page.select_option("#add-type", "place")
    page.fill("#add-value", "Winterfell")
    page.dispatch_event("#add-value", "input")
    page.evaluate("() => { writeEdgeProps('add', {label: 'raised at', arrow: 'target'}); addPreviewNode(); }")
    page.wait_for_timeout(400)
    s.save("add", "#addmodal-box")

    # 6. edit link: a contested parentage, dashed
    s.open("""() => openEdgeModal(cy.edges('[lstyle="dashed"]').filter(
        e => e.connectedNodes('[ntype="target"]').length)[0])""", "#edgemodal-box")
    s.save("edge", "#edgemodal-box")

    # 9. connect nodes
    pair = f"[{TARGET}.id(), ({by_label('Daenerys Targaryen')} || {by_label('Rhaegar Targaryen')}).id()]"
    s.open(f"""() => openLinkModal({pair}, {{label: 'hypothesis: nephew', curve: 'unbundled-bezier',
            lstyle: 'dashed', width: 3, color: '#7c3aed', arrow: 'both'}})""", "#linkmodal-box")
    s.save("link", "#linkmodal-box")

    # 13. AI settings, 14. licences, 15. edit case, 16. manual changes
    s.open("() => openAiConfig()", "#aimodal-box")
    s.save("ai", "#aimodal-box")
    s.open("() => document.querySelector('#licLink').click()", "#licmodal-box")
    page.wait_for_timeout(800)
    s.save("lic", "#licmodal-box")
    s.open("() => document.querySelector('#caseEdit').click()", "#casemodal-box")
    s.save("caseEdit", "#casemodal-box")
    s.close_modals()
    api(base, "/api/node/add", {"parent": tid, "ntype": "place", "value": "Winterfell",
                                "edge": {"label": "raised at", "arrow": "target"}})
    s.open("() => document.querySelector('#showManual').click()", "#manmodal-box")
    page.wait_for_timeout(600)
    s.save("manual", "#manmodal-box")
    s.close_modals()

    # 10-12. import wizard, in a second empty case, with the hypotheses file
    api(base, "/api/cases/add", {"name": "Hypotheses", "description": ""})
    page.reload()
    s.ready()
    s.open("() => openImport()", "#impmodal-box")
    s.save("imp1", "#impmodal-box")
    page.set_input_files("#imp-file", HYP)
    page.wait_for_selector("#imp-map table", state="visible")
    s.save("imp2", "#impmodal-box")
    page.click("#impmodal-next")
    page.wait_for_selector("#imp-res table", state="visible")
    page.wait_for_timeout(400)
    s.save("imp3", "#impmodal-box")
    s.close_modals()

    # 19. corner marks: what the program reads in a card number, an IBAN, a phone...
    api(base, "/api/cases/add", {"name": "Iron Bank", "description": "Corner marks of the nodes."})
    pid = api(base, "/api/node/add", {"ntype": "name", "surname": "Baelish", "given_name": "Petyr",
                                      "sex": "male", "target": True})["id"]
    for body in (
            {"ntype": "card", "fields": {"number": "4111 1111 1111 1111", "expiry": "12/30"}},
            {"ntype": "card", "fields": {"number": "5555 5555 5555 4440"}},
            {"ntype": "bankaccount", "fields": {"iban": "IT60 X054 2811 1010 0000 0123 456"}},
            {"ntype": "crypto", "fields": {"address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"}},
            {"ntype": "phone", "value": "+44 7700 900123"},
            {"ntype": "email", "value": "petyr.baelish@gmail.com"},
            {"ntype": "document", "fields": {"type": "Passport", "number": "YA1234567", "country": "Russia",
                                             "expiry": "2020-01-01"}},
            {"ntype": "weapon", "fields": {"category": "Assault rifle", "serial_number": "removed"}}):
        api(base, "/api/node/add", dict(body, parent=pid, edge={"label": "uses", "arrow": "target"}))
    page.reload()
    s.ready()
    page.evaluate("document.querySelector('#loadTargets').click()")
    page.wait_for_function("cy.nodes('[ntype=\"target\"]').length > 0")
    page.evaluate(f"() => toggleExpand({TARGET})")
    page.wait_for_timeout(900)
    page.select_option("#gsLabels", "off")
    # a tight ring, zoomed in, left of the key: the marks must be readable
    page.evaluate("""() => { cy.layout({name: 'circle', radius: 150, fit: false, animate: false}).run();
        buildChartKey(); cy.fit(cy.nodes(), 110); cy.panBy({x: -90, y: 0}); }""")
    page.wait_for_timeout(1500)                           # flags and logos load once
    s.save("marks")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--keep", action="store_true", help="keep the temporary program and data")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="quaesitor-shots-")
    app_dir, data_dir = os.path.join(tmp, "app"), os.path.join(tmp, "data")
    os.makedirs(data_dir)
    program_copy(app_dir)
    proc, base = start_server(app_dir, data_dir, free_port())
    print("server", base, "program", app_dir)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="chrome", headless=True)
            ctx = browser.new_context(viewport=VIEW, device_scale_factor=1, locale="en-GB")
            ctx.add_init_script("localStorage.setItem('lang','en'); localStorage.removeItem('edgeStyle');")
            page = ctx.new_page()
            page.on("dialog", lambda d: d.dismiss())
            take_all(Shots(page, a.out), page, base)
            browser.close()
    finally:
        stop_server(proc)
        if not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)
    print("done:", a.out)


if __name__ == "__main__":
    main()
