#!/usr/bin/env python3
"""Check out every benchmark repo in bench/repos.json at its pinned SHA (stdlib + git).

Usage: python bench/fetch_repos.py --dest DIR [--strip-readme] [--repos bench/repos.json]

Each repo lands in DIR/<owner>__<repo> via `git init; git fetch --depth 1 origin SHA; git checkout FETCH_HEAD`.
Idempotent: a checkout already at the pinned SHA is left alone (only the README strip is re-applied).
--strip-readme deletes root README* files so the benchmark generates READMEs from code only.
The cloned content is untrusted: this script never runs anything from it (git hooks are disabled).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# no hooks, no LFS smudge, no credential prompts: fetching must never execute repo-controlled code
GIT = ["git", "-c", "core.hooksPath=/dev/null", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.process=",
       "-c", "filter.lfs.required=false", "-c", "core.longpaths=true", "-c", "advice.detachedHead=false"]
ENV_EXTRA = {"GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1"}


def git(args, cwd):
    import os
    env = dict(os.environ, **ENV_EXTRA)
    return subprocess.run(GIT + args, cwd=cwd, capture_output=True, text=True, env=env)


def head(path):
    p = git(["rev-parse", "HEAD"], path)
    return p.stdout.strip() if p.returncode == 0 else None


def fetch(repo, sha, dest):
    if dest.is_dir() and head(dest) == sha:
        return "already at pinned sha"
    dest.mkdir(parents=True, exist_ok=True)
    if not (dest / ".git").is_dir():
        p = git(["init", "-q"], dest)
        if p.returncode:
            raise RuntimeError(p.stderr.strip())
    url = f"https://github.com/{repo}.git"
    remotes = git(["remote"], dest).stdout.split()
    git(["remote", "set-url" if "origin" in remotes else "add", "origin", url], dest)
    for args in (["fetch", "-q", "--depth", "1", "--no-tags", "origin", sha], ["checkout", "-q", "--force", "FETCH_HEAD"]):
        p = git(args, dest)
        if p.returncode:
            raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    if head(dest) != sha:
        raise RuntimeError(f"HEAD is {head(dest)}, expected {sha}")
    return "fetched"


def strip_readmes(dest):
    removed = []
    for f in dest.iterdir():
        if f.is_file() and f.name.lower().startswith("readme"):
            f.unlink()
            removed.append(f.name)
    return removed


def main(argv):
    if "--dest" not in argv:
        print(__doc__)
        return 2
    dest_root = Path(argv[argv.index("--dest") + 1]).resolve()
    repos_file = Path(argv[argv.index("--repos") + 1]) if "--repos" in argv else HERE / "repos.json"
    strip = "--strip-readme" in argv
    repos = json.loads(repos_file.read_text(encoding="utf-8"))["repos"]
    dest_root.mkdir(parents=True, exist_ok=True)
    failed = 0
    for r in repos:
        dest = dest_root / r["repo"].replace("/", "__")
        try:
            status = fetch(r["repo"], r["sha"], dest)
            extra = f"; removed {', '.join(strip_readmes(dest)) or 'nothing'}" if strip else ""
            print(f"ok    {r['repo']}@{r['sha'][:10]}: {status}{extra}")
        except Exception as e:  # report and continue with the rest
            failed += 1
            print(f"FAIL  {r['repo']}@{r['sha'][:10]}: {e}")
    print(f"{len(repos) - failed}/{len(repos)} repos ready in {dest_root}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
