# -*- coding: utf-8 -*-
"""Copies the publishable tree of this development repository into the public
repository checkout, leaving out everything that stays private.

    python scripts/release_public.py <path of the public checkout> [--dry-run]

What is excluded (never reaches the public repository): CLAUDE.md, docs/evaluation/,
Garbage/, .git/, and everything git ignores here (data/, fonti/, tools/, .venv/,
services.conf, chatbot.conf, build/, dist/, caches). Everything else tracked by git
is copied; files present in the public checkout but no longer in the source tree
are deleted there, so the public tree mirrors the release exactly. Then, in the
public checkout: review `git status`, commit as "Quaesitor X.Y.Z" and push.
"""
# "Quod tacitum velis, nemini dixeris." (Seneca, attributed)
# What you want kept secret, tell to no one.
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_PREFIXES = ("CLAUDE.md", "docs/evaluation/", "Garbage/", "patches/")
KEEP_IN_TARGET = (".git/",)


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [p.decode("utf-8") for p in out.split(b"\0") if p]


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    target = os.path.abspath(sys.argv[1])
    dry = "--dry-run" in sys.argv
    if not os.path.isdir(os.path.join(target, ".git")):
        sys.exit(f"not a git checkout: {target}")
    files = [f for f in tracked_files() if not f.startswith(EXCLUDE_PREFIXES)]
    wanted = set(files)
    copied = 0
    for rel in files:
        src = os.path.join(ROOT, rel); dst = os.path.join(target, rel)
        if not dry:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        copied += 1
    removed = 0
    for dirpath, dirnames, filenames in os.walk(target):
        rel_dir = os.path.relpath(dirpath, target).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""
        dirnames[:] = [d for d in dirnames if not (rel_dir == "" and d == ".git")]
        for fn in filenames:
            rel = (rel_dir + "/" + fn) if rel_dir else fn
            if rel not in wanted:
                if not dry:
                    os.remove(os.path.join(dirpath, fn))
                removed += 1
    print(f"{'would copy' if dry else 'copied'} {copied} files, {'would remove' if dry else 'removed'} {removed} stale files in {target}")
    print("excluded:", ", ".join(EXCLUDE_PREFIXES))


if __name__ == "__main__":
    main()
