#!/usr/bin/env python3
"""Recreate each repo's file *paths* (empty files, no content) at its pinned SHA, with the real README at the root.

Why: score_readme.py checks that relative links/images exist next to the README. Scoring a README file
on its own turns every working `docs/x.png` link into an ERROR, which penalises well-illustrated READMEs.
A stub tree from the GitHub trees API fixes that without downloading any third-party code.

Usage: python bench/scorer-validation/build_stub_trees.py READMES_DIR OUT_DIR
  READMES_DIR/{group}/OWNER__REPO.md  ->  OUT_DIR/{group}/OWNER__REPO/<README name>  (+ empty stub files)
Prints one line per repo: entries created, entries skipped (unsafe/invalid names), API truncation flag.
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BAD = re.compile(r'[<>:"|?*\x00-\x1f]')  # names Windows cannot create


def main(argv):
    src, out = Path(argv[1]), Path(argv[2])
    with open(HERE / "repos.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        group, repo, sha = row["group"], row["repo"], row["sha"]
        readme_name = row["url"].rsplit("/", 1)[1]
        root = out / group / repo.replace("/", "__")
        root.mkdir(parents=True, exist_ok=True)
        p = subprocess.run(["gh", "api", f"repos/{repo}/git/trees/{sha}?recursive=1"], capture_output=True)
        made = skipped = 0
        truncated = None
        if p.returncode == 0:
            tree = json.loads(p.stdout.decode("utf-8"))
            truncated = tree.get("truncated")
            for e in tree.get("tree", []):
                rel = e["path"]
                parts = rel.split("/")
                if any(x in ("", ".", "..") for x in parts) or any(BAD.search(x) for x in parts):
                    skipped += 1
                    continue
                target = root.joinpath(*parts)
                try:
                    if e["type"] == "tree":
                        target.mkdir(parents=True, exist_ok=True)
                    elif e["type"] in ("blob", "commit"):
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if not target.exists():
                            target.touch()
                    made += 1
                except OSError:
                    skipped += 1
        readme_src = src / group / f"{repo.replace('/', '__')}.md"
        (root / readme_name).write_bytes(readme_src.read_bytes())
        print(f"{group} {repo}: created={made} skipped={skipped} truncated={truncated} api_ok={p.returncode == 0}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
