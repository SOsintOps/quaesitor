# -*- coding: utf-8 -*-
# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""OSInt Graph launcher: a small borderless panel, always on top,
with three buttons:

    ▶  starts the server        ■  stops it        🌐  opens the browser

The dot shows the state: grey = stopped, yellow = starting, green = the
server responds. The panel is moved by dragging the handle on the left;
✕ closes the launcher (and stops the server, if the launcher started it).

What it starts, in order:
  1) app.py in the program folder, with the project's Python (.venv) if present;
  2) otherwise the compiled executable (Quaesitor.exe / Quaesitor).

Port: PORT variable or --port option (default 5000, like app.py).
The server output goes to launcher.log, next to the launcher.

Usage:   .venv\\Scripts\\pythonw.exe -m quaesitor.launcher      (no console window)
"""
# "Ubi concordia, ibi victoria." (Publilius Syrus)
# Where there is harmony, there is victory.
import os
import socket
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser

try:
    from .paths import BASE_DIR as ROOT   # the program folder, above the package
except ImportError:                       # started as a file, not with -m
    ROOT = (os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IS_WIN = os.name == "nt"


def _port():
    argv = sys.argv[1:]
    if "--port" in argv:
        i = argv.index("--port")
        if i + 1 < len(argv) and argv[i + 1].isdigit():
            return int(argv[i + 1])
    p = os.environ.get("PORT", "5000")
    return int(p) if p.isdigit() else 5000


PORT = _port()
URL = f"http://127.0.0.1:{PORT}"
LOG = os.path.join(ROOT, "launcher.log")

# panel colours
BG, FG, MUTED, HOVER = "#0f172a", "#e2e8f0", "#64748b", "#1e293b"
DOT = {"stopped": "#64748b", "starting": "#f59e0b", "running": "#22c55e"}


def server_command():
    """Command that starts the server (see the order in the docstring)."""
    app = os.path.join(ROOT, "app.py")
    if os.path.isfile(app):
        venv = os.path.join(ROOT, ".venv", "Scripts" if IS_WIN else "bin",
                            "python.exe" if IS_WIN else "python")
        py = venv if os.path.isfile(venv) else sys.executable
        if IS_WIN and py.lower().endswith("pythonw.exe"):
            py = py[:-5] + ".exe"                     # output is needed for the log
        return [py, app]
    for name in ("Quaesitor.exe", "Quaesitor"):
        exe = os.path.join(ROOT, name)
        if os.path.isfile(exe):
            return [exe]
    return None


def server_alive(timeout=0.6):
    """Does the server accept connections on the port? (plain TCP connection:
    unlike an HTTP request it does not fill the server log)"""
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=timeout):
            return True
    except OSError:
        return False


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.proc = None
        self.logf = None
        self.state = "stopped"
        self._drag = (0, 0)

        self.overrideredirect(True)          # no borders or title bar
        self.attributes("-topmost", True)
        self.configure(bg=BG)

        bar = tk.Frame(self, bg=BG, padx=4, pady=3)
        bar.pack(fill="both", expand=True)

        grip = tk.Label(bar, text="⋮⋮", bg=BG, fg=MUTED, cursor="fleur",
                        font=("Segoe UI", 9))
        grip.pack(side="left", padx=(2, 4))
        self.dot = tk.Canvas(bar, width=10, height=10, bg=BG, highlightthickness=0)
        self.dot_id = self.dot.create_oval(1, 1, 9, 9, fill=DOT["stopped"], outline="")
        self.dot.pack(side="left", padx=(0, 6))

        self.b_start = self._btn(bar, "▶", self.start, "Avvia il server")
        self.b_stop = self._btn(bar, "■", self.stop, "Ferma il server")
        self.b_open = self._btn(bar, "🌐", self.open_browser, f"Apri {URL}")
        tk.Frame(bar, width=1, bg=HOVER).pack(side="left", fill="y", padx=4, pady=2)
        self._btn(bar, "✕", self.quit_app, "Chiudi il launcher")

        # dragging from the handle and the dot
        for w in (grip, self.dot, bar):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

        self.tip = None
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{sw - w - 24}+{sh - h - 64}")    # bottom right

        self._refresh_buttons()
        self._poll()

    # ---------------------------------------------------------------- widget
    def _btn(self, parent, text, cmd, tip):
        b = tk.Label(parent, text=text, bg=BG, fg=FG, width=2, cursor="hand2",
                     font=("Segoe UI Symbol", 11))
        b.pack(side="left", padx=1)
        b.enabled = True
        b.bind("<Enter>", lambda e: (b.enabled and b.configure(bg=HOVER), self._show_tip(b, tip)))
        b.bind("<Leave>", lambda e: (b.configure(bg=BG), self._hide_tip()))
        b.bind("<ButtonRelease-1>", lambda e: b.enabled and cmd())
        return b

    def _enable(self, b, on):
        b.enabled = on
        b.configure(fg=FG if on else MUTED, cursor="hand2" if on else "arrow")

    def _show_tip(self, w, text):
        self._hide_tip()
        self.tip = tk.Toplevel(self)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        tk.Label(self.tip, text=text, bg="#334155", fg=FG, padx=6, pady=2,
                 font=("Segoe UI", 8)).pack()
        self.tip.update_idletasks()
        x = w.winfo_rootx() + w.winfo_width() // 2 - self.tip.winfo_reqwidth() // 2
        y = self.winfo_rooty() - self.tip.winfo_reqheight() - 4
        self.tip.geometry(f"+{x}+{y}")

    def _hide_tip(self):
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None

    def _drag_start(self, e):
        self._drag = (e.x_root - self.winfo_x(), e.y_root - self.winfo_y())

    def _drag_move(self, e):
        self.geometry(f"+{e.x_root - self._drag[0]}+{e.y_root - self._drag[1]}")

    # ---------------------------------------------------------------- state
    def _set_state(self, st):
        self.state = st
        self.dot.itemconfigure(self.dot_id, fill=DOT[st])
        self._refresh_buttons()

    def _refresh_buttons(self):
        ours = self.proc is not None and self.proc.poll() is None
        self._enable(self.b_start, self.state == "stopped")
        self._enable(self.b_stop, ours)
        self._enable(self.b_open, self.state == "running")

    def _poll(self):
        """Every second, check whether the server responds (even if started
        elsewhere) and whether the process started by the launcher is still alive."""
        def check():
            alive = server_alive()
            self.after(0, lambda: self._apply_poll(alive))
        threading.Thread(target=check, daemon=True).start()
        self.after(1000, self._poll)

    def _apply_poll(self, alive):
        ours = self.proc is not None and self.proc.poll() is None
        if alive:
            if self.state != "running":
                self._set_state("running")
        elif ours:
            if self.state != "starting":
                self._set_state("starting")
        else:
            if self.proc is not None:                 # the server exited by itself
                self._close_log()
                self.proc = None
            if self.state != "stopped":
                self._set_state("stopped")
        self._refresh_buttons()

    # ---------------------------------------------------------------- actions
    def start(self):
        if self.proc is not None and self.proc.poll() is None:
            return
        cmd = server_command()
        if not cmd:
            self._show_tip(self.b_start, "app.py / Quaesitor non trovati")
            self.after(2500, self._hide_tip)
            return
        env = dict(os.environ, PORT=str(PORT), PYTHONUNBUFFERED="1",
                   PYTHONIOENCODING="utf-8")
        self.logf = open(LOG, "a", encoding="utf-8", errors="replace")
        flags = subprocess.CREATE_NO_WINDOW if IS_WIN else 0
        self.proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=self.logf,
                                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                     creationflags=flags,
                                     start_new_session=not IS_WIN)
        self._set_state("starting")

    def stop(self):
        p = self.proc
        if p is None or p.poll() is not None:
            return
        # in development Flask uses the reloader, which spawns a child process:
        # the whole tree must be closed, not just the started process
        try:
            if IS_WIN:
                subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"],
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                import signal
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
        self.proc = None
        self._close_log()
        self._set_state("stopped")

    def open_browser(self):
        webbrowser.open(URL)                     # system default browser

    def _close_log(self):
        if self.logf is not None:
            try:
                self.logf.close()
            except Exception:
                pass
            self.logf = None

    def quit_app(self):
        self.stop()
        self.destroy()


def main():
    if IS_WIN:
        try:                                     # sharp text on HiDPI screens
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    Launcher().mainloop()


if __name__ == "__main__":
    main()
