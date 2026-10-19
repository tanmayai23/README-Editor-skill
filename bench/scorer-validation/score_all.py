#!/usr/bin/env python3
"""Score every README in READMES_DIR/{good,neglected}/*.md with score_readme.py and write results.csv.

Usage: python bench/scorer-validation/score_all.py SRC_DIR [--layout flat|tree] [--out results.csv] [--findings OUT.json]
  --layout flat  SRC_DIR/{group}/OWNER__REPO.md            (README scored on its own)
  --layout tree  SRC_DIR/{group}/OWNER__REPO/<README name> (stub tree from build_stub_trees.py; default)

README text is third-party content and is not committed; fetch it with select_repos.py.
The scorer runs WITHOUT --repo (no code checkout), so the 'drift' category is absent.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCORER = HERE.parent.parent / "readme-forge" / "scripts" / "score_readme.py"
CATS = ["identity", "getting-started", "structure", "visuals", "community", "quality"]


def main(argv):
    src = Path(argv[1])
    findings_out = Path(argv[argv.index("--findings") + 1]) if "--findings" in argv else None
    layout = argv[argv.index("--layout") + 1] if "--layout" in argv else "tree"
    out_csv = HERE / (argv[argv.index("--out") + 1] if "--out" in argv else "results.csv")
    repos = {}
    with open(HERE / "repos.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            repos[(row["group"], row["repo"])] = row
    out_rows, all_findings = [], {}
    for (group, repo) in repos:
        if layout == "flat":
            path = src / group / f"{repo.replace('/', '__')}.md"
        else:
            path = src / group / repo.replace("/", "__") / repos[(group, repo)]["url"].rsplit("/", 1)[1]
        row = {"group": group, "repo": repo, "status": "ok", "score": "", "grade": "", "lines": ""}
        if not path.is_file():
            row["status"] = "missing-readme-file"
            out_rows.append(row)
            continue
        row["lines"] = len(path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n").splitlines())
        p = subprocess.run([sys.executable, "-I", str(SCORER), str(path), "--json"], capture_output=True)
        if p.returncode != 0:
            row["status"] = "crash: " + p.stderr.decode("utf-8", "replace").strip().splitlines()[-1][:200]
            out_rows.append(row)
            continue
        d = json.loads(p.stdout.decode("utf-8"))
        row["score"], row["grade"] = d["score"], d["grade"]
        for c in CATS:
            row[c] = d["categories"].get(c, {}).get("score", "")
        out_rows.append(row)
        all_findings[f"{group}/{repo}"] = d["findings"]
    fields = ["group", "repo", "status", "lines", "score", "grade"] + CATS
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)
    if findings_out:
        findings_out.write_text(json.dumps(all_findings, indent=1, ensure_ascii=False), encoding="utf-8")
    bad = [r for r in out_rows if r["status"] != "ok"]
    print(f"scored {len(out_rows) - len(bad)}/{len(out_rows)}; problems: {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
