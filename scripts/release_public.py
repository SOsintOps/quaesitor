# -*- coding: utf-8 -*-
"""Copies the publishable tree of this development repository into the public
repository checkout, leaving out everything that stays private.

    python scripts/release_public.py <path of the public checkout> [--dry-run]

The files are taken from the last commit (HEAD), never from the disk: work in
progress, untracked files and local edits cannot reach the public repository.
The script refuses to run while tracked files have uncommitted changes, so what
is released is exactly what was committed and tested.

What is excluded (never reaches the public repository): CLAUDE.md, docs/evaluation/,
Garbage/, patches/, and everything that is not committed here (data/, sources/,
tools/, .venv/, services.conf, chatbot.conf, build/, dist/, caches). Files tracked
in the public checkout but no longer in the release are deleted there, so the
public tree mirrors the release exactly; files that the public checkout's
.gitignore ignores (its own .venv, data/, sources/, tools/, *.conf, logs) are never
touched. The release is staged in the public checkout and its files are written
back through git, so they get that checkout's line endings (CRLF for the .bat
files). Then, in the public checkout: review `git status`, commit as
"Quaesitor X.Y.Z" and push.
"""
# "Quod tacitum velis, nemini dixeris." (Seneca, attributed)
# What you want kept secret, tell to no one.
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_PREFIXES = ("CLAUDE.md", "docs/evaluation/", "Garbage/", "patches/")


def git(cwd, *args, **kw):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True, **kw).stdout


def git_z(cwd, *args):
    return [p.decode("utf-8") for p in git(cwd, *args, "-z").split(b"\0") if p]


def head_blobs():
    """(path, blob id) of every file in HEAD, symlinks and submodules excluded."""
    out = []
    for entry in git(ROOT, "ls-tree", "-r", "-z", "HEAD").split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        mode, kind, sha = meta.split()
        if kind == b"blob" and mode in (b"100644", b"100755"):
            out.append((path.decode("utf-8"), sha.decode()))
    return out


def read_blobs(shas):
    """Contents of the blobs, in one `git cat-file --batch` run."""
    proc = subprocess.run(["git", "cat-file", "--batch"], cwd=ROOT, capture_output=True, check=True,
                          input=b"".join(s.encode() + b"\n" for s in shas)).stdout
    data, i = {}, 0
    for sha in shas:
        nl = proc.index(b"\n", i)
        size = int(proc[i:nl].split()[2])
        data[sha] = proc[nl + 1:nl + 1 + size]
        i = nl + 1 + size + 1                       # content, then a newline
    return data


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    target = os.path.abspath(sys.argv[1])
    dry = "--dry-run" in sys.argv
    if not os.path.isdir(os.path.join(target, ".git")):
        sys.exit(f"not a git checkout: {target}")
    dirty = git(ROOT, "status", "--porcelain", "--untracked-files=no").decode().strip()
    if dirty:
        sys.exit("uncommitted changes in tracked files: commit or stash them first\n" + dirty)
    files = [(p, s) for p, s in head_blobs() if not p.startswith(EXCLUDE_PREFIXES)]
    wanted = {p for p, _ in files}
    blobs = read_blobs(sorted({s for _, s in files}))
    for rel, sha in files:
        if not dry:
            dst = os.path.join(target, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(blobs[sha])
    # Stale = tracked in the public checkout but not in this release. Untracked
    # and ignored files there (venv, archives, settings, logs) are left alone.
    stale = [f for f in git_z(target, "ls-files") if f not in wanted]
    for rel in stale:
        if not dry:
            try:
                os.remove(os.path.join(target, rel))
            except FileNotFoundError:
                pass
    if not dry:
        z = lambda paths: b"".join(p.encode("utf-8") + b"\0" for p in paths)
        git(target, "add", "--pathspec-from-file=-", "--pathspec-file-nul", input=z(sorted(wanted)))
        if stale:
            git(target, "rm", "-q", "--cached", "--ignore-unmatch", "--pathspec-from-file=-",
                "--pathspec-file-nul", input=z(stale))
        # checkout-index converts the line endings only when it creates the file,
        # and the second add refreshes the index after the rewrite
        for rel in wanted:
            os.remove(os.path.join(target, rel))
        git(target, "checkout-index", "-f", "-z", "--stdin", input=z(sorted(wanted)))
        git(target, "add", "--pathspec-from-file=-", "--pathspec-file-nul", input=z(sorted(wanted)))
    head = git(ROOT, "rev-parse", "--short", "HEAD").decode().strip()
    print(f"{'would copy' if dry else 'copied'} {len(files)} files from {head}, "
          f"{'would remove' if dry else 'removed'} {len(stale)} files no longer in the release, in {target}")
    for rel in stale:
        print("  -", rel)
    print("excluded:", ", ".join(EXCLUDE_PREFIXES))


if __name__ == "__main__":
    main()
