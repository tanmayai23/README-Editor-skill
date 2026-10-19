#!/usr/bin/env python3
"""Summarise results.csv: per-group stats, AUC (Mann-Whitney), per-category separation, failure cases.

Usage: python bench/scorer-validation/analyze.py [results.csv]   (stdlib only, re-runnable)
"""
import csv
import statistics as st
import sys
from pathlib import Path

CATS = [("identity", 15), ("getting-started", 25), ("structure", 15), ("visuals", 10), ("community", 15), ("quality", 20)]


def auc(pos, neg):
    """P(random pos > random neg), ties count 1/2  ==  Mann-Whitney U / (n1*n2)."""
    u = sum(1.0 if p > q else 0.5 if p == q else 0.0 for p in pos for q in neg)
    return u / (len(pos) * len(neg))


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent / "results.csv"
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    bad = [r for r in rows if r["status"] != "ok"]
    rows = [r for r in rows if r["status"] == "ok"]
    g = {k: [r for r in rows if r["group"] == k] for k in ("good", "neglected")}
    print(f"rows scored: good={len(g['good'])} neglected={len(g['neglected'])}; not scored: {len(bad)}")
    for r in bad:
        print(f"  NOT SCORED {r['group']} {r['repo']}: {r['status']}")

    print("\n## Total score by group")
    print("| group | n | mean | median | stdev | min | max |")
    print("|---|---|---|---|---|---|---|")
    for k, rs in g.items():
        s = [float(r["score"]) for r in rs]
        print(f"| {k} | {len(s)} | {st.mean(s):.1f} | {st.median(s):.1f} | {st.stdev(s):.1f} | {min(s):.0f} | {max(s):.0f} |")
    good = [float(r["score"]) for r in g["good"]]
    neg = [float(r["score"]) for r in g["neglected"]]
    print(f"\nAUC (total score, good vs neglected) = {auc(good, neg):.3f}")
    for thr in (55, 70):
        tp = sum(s >= thr for s in good)
        fp = sum(s >= thr for s in neg)
        print(f"threshold >= {thr}: good {tp}/{len(good)} pass, neglected {fp}/{len(neg)} pass")

    # README length alone as a baseline 'scorer'
    gl = [float(r["lines"]) for r in g["good"]]
    nl = [float(r["lines"]) for r in g["neglected"]]
    print(f"baseline AUC using README line count alone = {auc(gl, nl):.3f}")

    print("\n## Per category (share of category max, so categories are comparable)")
    print("| category | max | good mean | neglected mean | diff (pts) | AUC |")
    print("|---|---|---|---|---|---|")
    for c, mx in CATS:
        a = [float(r[c]) for r in g["good"]]
        b = [float(r[c]) for r in g["neglected"]]
        print(f"| {c} | {mx} | {st.mean(a):.1f} ({st.mean(a) / mx:.0%}) | {st.mean(b):.1f} ({st.mean(b) / mx:.0%}) "
              f"| {st.mean(a) - st.mean(b):+.1f} | {auc(a, b):.3f} |")

    key = lambda r: (float(r["score"]), r["repo"])
    print("\n## 5 lowest-scored good READMEs")
    for r in sorted(g["good"], key=key)[:5]:
        print(f"  {r['score']:>3} {r['grade']} {r['repo']} (lines {r['lines']}) " + " ".join(f"{c}={r[c]}" for c, _ in CATS))
    print("\n## 5 highest-scored neglected READMEs")
    for r in sorted(g["neglected"], key=key, reverse=True)[:5]:
        print(f"  {r['score']:>3} {r['grade']} {r['repo']} (lines {r['lines']}) " + " ".join(f"{c}={r[c]}" for c, _ in CATS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
