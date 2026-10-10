# -*- coding: utf-8 -*-
"""Copies the publishable tree of this development repository into the public
repository checkout, leaving out everything that stays private.

    python scripts/release_public.py <path of the public checkout> [--dry-run]

What is excluded (never reaches the public repository): CLAUDE.md, docs/evaluation/,
Garbage/, patches/, .git/, and everything git ignores here (data/, fonti/, tools/,
.venv/, services.conf, chatbot.conf, build/, dist/, caches). Everything else tracked
by git is copied. Files tracked in the public checkout but no longer in the source
tree are deleted there, so the public tree mirrors the release exactly; files that
the public checkout's .gitignore ignores (its own .venv, data/, fonti/, tools/,
*.conf, logs) are never touched. Then, in the public checkout: review `git status`,
commit as "Quaesitor X.Y.Z" and push.
"""
# "Quod tacitum velis, nemini dixeris." (Seneca, attributed)
# What you want kept secret, tell to no one.
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_PREFIXES = ("CLAUDE.md", "docs/evaluation/", "Garbage/", "patches/")


def git_z(cwd, *args):
    out = subprocess.run(["git", *args, "-z"], cwd=cwd, capture_output=True, check=True).stdout
    return [p.decode("utf-8") for p in out.split(b"\0") if p]


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    target = os.path.abspath(sys.argv[1])
    dry = "--dry-run" in sys.argv
    if not os.path.isdir(os.path.join(target, ".git")):
        sys.exit(f"not a git checkout: {target}")
    files = [f for f in git_z(ROOT, "ls-files") if not f.startswith(EXCLUDE_PREFIXES)]
    wanted = set(files)
    copied = 0
    for rel in files:
        src = os.path.join(ROOT, rel); dst = os.path.join(target, rel)
        if not dry:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        copied += 1
    # Stale = tracked in the public checkout but not in this release. Untracked
    # and ignored files there (venv, archives, settings, logs) are left alone.
    stale = [f for f in git_z(target, "ls-files") if f not in wanted]
    for rel in stale:
        if not dry:
            try:
                os.remove(os.path.join(target, rel))
            except FileNotFoundError:
                pass
    print(f"{'would copy' if dry else 'copied'} {copied} files, "
          f"{'would remove' if dry else 'removed'} {len(stale)} files no longer in the release, in {target}")
    for rel in stale:
        print("  -", rel)
    print("excluded:", ", ".join(EXCLUDE_PREFIXES))


if __name__ == "__main__":
    main()
