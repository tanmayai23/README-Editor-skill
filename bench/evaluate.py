#!/usr/bin/env python3
"""Score and fact-check every generated README in the benchmark, then summarise per condition.

Stdlib only. Usage:
    python bench/evaluate.py --repos DIR --outputs bench/outputs [--csv bench/results/results.csv] [--md bench/results/summary.md]

Layout:
    DIR/<owner>__<repo>/                    the pinned checkout (README stripped), from fetch_repos.py
    bench/outputs/<condition>/<owner>__<repo>.md   one generated README per condition and repo

For each README it runs readme-forge's verify_readme.py (claims checked against the checkout)
and score_readme.py (rubric score). A claim the verifier marks not_found is counted as a
hallucination: a command, script, flag, env var or path the README states that the code does not have.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERIFY = ROOT / "readme-forge" / "scripts" / "verify_readme.py"
SCORE = ROOT / "readme-forge" / "scripts" / "score_readme.py"
KINDS = ("command", "script", "flag", "env_var", "path", "package_manager")


def run_json(args):
    p = subprocess.run([sys.executable, *map(str, args), "--json"], capture_output=True, text=True, encoding="utf-8")
    try:
        return json.loads(p.stdout)
    except ValueError:
        raise RuntimeError(f"{' '.join(map(str, args))} failed:\n{p.stderr[-2000:]}")


def evaluate(readme: Path, repo: Path) -> dict:
    v = run_json([VERIFY, readme, "--repo", repo])
    s = run_json([SCORE, readme, "--repo", repo])
    row = {"verified": v["summary"]["verified"], "not_found": v["summary"]["not_found"],
           "unverifiable": v["summary"]["unverifiable"], "checked": v["summary"]["checked"],
           "accuracy": v["summary"]["accuracy"], "score": s.get("score"),
           "todos": readme.read_text(encoding="utf-8", errors="ignore").count("TODO"),
           "lines": readme.read_text(encoding="utf-8", errors="ignore").count("\n") + 1}
    for k in KINDS:
        bk = v.get("by_kind", {}).get(k, {})
        row[f"{k}_verified"] = bk.get("verified", 0)
        row[f"{k}_not_found"] = bk.get("not_found", 0)
    row["not_found_claims"] = [f'{c["line"]}: [{c["kind"]}] {c["text"]}' for c in v["claims"] if c["status"] == "not_found"]
    return row


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def summarise(rows):
    by = {}
    for r in rows:
        by.setdefault(r["condition"], []).append(r)
    out = []
    for cond, rs in sorted(by.items()):
        ver = sum(r["verified"] for r in rs)
        nf = sum(r["not_found"] for r in rs)
        cmd_ok = sum(r["command_verified"] + r["script_verified"] + r["flag_verified"] + r["package_manager_verified"] for r in rs)
        cmd_bad = sum(r["command_not_found"] + r["script_not_found"] + r["flag_not_found"] + r["package_manager_not_found"] for r in rs)
        out.append({
            "condition": cond, "readmes": len(rs),
            "claims_checked": ver + nf, "hallucinations": nf,
            "claim_accuracy": pct(ver, ver + nf),
            "command_accuracy": pct(cmd_ok, cmd_ok + cmd_bad),
            "env_accuracy": pct(sum(r["env_var_verified"] for r in rs), sum(r["env_var_verified"] + r["env_var_not_found"] for r in rs)),
            "path_accuracy": pct(sum(r["path_verified"] for r in rs), sum(r["path_verified"] + r["path_not_found"] for r in rs)),
            "readmes_with_zero_hallucinations": sum(1 for r in rs if r["not_found"] == 0),
            "median_score": statistics.median(r["score"] for r in rs if r["score"] is not None),
            "median_claims_checked": statistics.median(r["checked"] for r in rs),
            "total_todos": sum(r["todos"] for r in rs),
        })
    return out


def to_markdown(summary, rows):
    head = ("| Condition | READMEs | Claims checked | Hallucinated claims | Claim accuracy | Command accuracy | Env var accuracy | Path accuracy "
            "| READMEs with 0 hallucinations | Median rubric score | TODOs left |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    fmt = lambda v: "n/a" if v is None else (f"{v}%" if isinstance(v, float) else str(v))
    lines = [head]
    for s in summary:
        lines.append(f"| {s['condition']} | {s['readmes']} | {s['claims_checked']} | {s['hallucinations']} | {fmt(s['claim_accuracy'])} | "
                     f"{fmt(s['command_accuracy'])} | {fmt(s['env_accuracy'])} | {fmt(s['path_accuracy'])} | "
                     f"{s['readmes_with_zero_hallucinations']}/{s['readmes']} | {s['median_score']} | {s['total_todos']} |")
    lines.append("\n### Every hallucinated claim\n")
    for r in sorted(rows, key=lambda r: (r["condition"], r["repo"])):
        for c in r["not_found_claims"]:
            lines.append(f"- `{r['condition']}` · {r['repo']} · line {c}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repos", required=True, type=Path)
    p.add_argument("--outputs", default=ROOT / "bench" / "outputs", type=Path)
    p.add_argument("--csv", default=ROOT / "bench" / "results" / "results.csv", type=Path)
    p.add_argument("--md", default=ROOT / "bench" / "results" / "summary.md", type=Path)
    a = p.parse_args(argv)
    rows = []
    for cond_dir in sorted(d for d in a.outputs.iterdir() if d.is_dir()):
        for readme in sorted(cond_dir.glob("*.md")):
            repo = a.repos / readme.stem
            if not repo.is_dir():
                print(f"skip {readme}: no checkout at {repo}", file=sys.stderr)
                continue
            row = {"condition": cond_dir.name, "repo": readme.stem.replace("__", "/"), **evaluate(readme, repo)}
            rows.append(row)
            print(f"{row['condition']:<22} {row['repo']:<40} claims {row['checked']:>3}  not found {row['not_found']:>2}  score {row['score']}")
    if not rows:
        print("no READMEs found", file=sys.stderr)
        return 2
    a.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [k for k in rows[0] if k != "not_found_claims"]
    with open(a.csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    summary = summarise(rows)
    a.md.write_text(to_markdown(summary, rows), encoding="utf-8")
    print("\n" + to_markdown(summary, []).split("\n### ")[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
