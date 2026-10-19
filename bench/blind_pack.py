#!/usr/bin/env python3
"""Build a blind rating pack: for every repo, the generated READMEs under random labels (A, B, …).

Stdlib only. Usage:
    python bench/blind_pack.py --outputs bench/outputs --out blind-pack [--seed 7]
    python bench/blind_pack.py --unblind blind-pack/key.json --ratings ratings.csv

The pack has one folder per repo with A.md, B.md, … and a ratings.csv template. key.json maps
labels back to conditions: keep it away from the raters. Raters score each README 1–5 on
"I could install and run this project from the README alone" and "this README is accurate",
reading the repo on GitHub (pinned commit in bench/repos.json) to check.
With --unblind, prints the mean rating per condition from the raters' filled-in CSVs.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import statistics
import sys
from pathlib import Path


def build(outputs: Path, out: Path, seed: int):
    rng = random.Random(seed)
    conds = sorted(d.name for d in outputs.iterdir() if d.is_dir())
    repos = sorted(set.intersection(*[{p.stem for p in (outputs / c).glob("*.md")} for c in conds]))
    out.mkdir(parents=True, exist_ok=True)
    key, rows = {}, []
    for repo in repos:
        order = conds[:]
        rng.shuffle(order)
        (out / repo).mkdir(exist_ok=True)
        for label, cond in zip("ABCDEFG", order):
            shutil.copy(outputs / cond / f"{repo}.md", out / repo / f"{label}.md")
            key[f"{repo}/{label}"] = cond
            rows.append({"repo": repo.replace("__", "/"), "label": label, "rater": "", "can_run_it_1to5": "", "accurate_1to5": "", "notes": ""})
    (out / "key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    with open(out / "ratings.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(repos)} repos × {len(conds)} READMEs → {out}. Give raters everything except key.json.")


def unblind(key_path: Path, ratings: list):
    key = json.loads(key_path.read_text(encoding="utf-8"))
    scores = {}
    for path in ratings:
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if not r["can_run_it_1to5"]:
                    continue
                cond = key[f'{r["repo"].replace("/", "__")}/{r["label"]}']
                scores.setdefault(cond, []).append((int(r["can_run_it_1to5"]), int(r["accurate_1to5"])))
    for cond, s in sorted(scores.items()):
        print(f"{cond:<22} n={len(s):<4} can-run {statistics.mean(a for a, _ in s):.2f}  accurate {statistics.mean(b for _, b in s):.2f}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--outputs", type=Path, default=Path(__file__).resolve().parent / "outputs")
    p.add_argument("--out", type=Path)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--unblind", type=Path, metavar="KEY_JSON")
    p.add_argument("--ratings", nargs="*", default=[])
    a = p.parse_args(argv)
    if a.unblind:
        unblind(a.unblind, a.ratings)
    elif a.out:
        build(a.outputs, a.out, a.seed)
    else:
        p.error("pass --out DIR to build a pack, or --unblind key.json --ratings FILE...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
