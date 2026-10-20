#!/usr/bin/env python3
"""Reproducible selection of the 20-repo README-generation benchmark (writes bench/repos.json).

Procedure (fixed before looking at any candidate):
  For each slot below, run GitHub repository searches (sort=stars desc, 100/page, up to 3 pages), one
  per license in SEARCH_LICENSES order (mit, then apache-2.0, then bsd-3-clause), and walk the results in order. Take the first N repos that pass ALL filters:
    1. not owned by tanmayai23, not a fork, not archived, license spdx in PERMISSIVE
    2. root README exists and is weak: <= 15 non-blank lines and no word install/usage/getting started/quickstart
    3. the tree at HEAD is complete (not truncated), has < 2000 files, repo size < 30 MB
    4. the slot's package manifest exists (root, except C# where any *.csproj/*.sln counts)
    5. real code: >= 5 source files with the slot's extensions
  No candidate is skipped for any other reason, so the README generator's likely performance plays no part.
  Revision note: a first run (same filters, one query per slot without a license qualifier) filled only 16 of
  20 slots, because most top results had no or a non-permissive license. The per-license queries replaced it
  before any repo was cloned or any README was generated.

Usage: python bench/select_benchmark_repos.py [--out bench/repos.json]   (needs an authenticated gh)
"""
import base64
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PERMISSIVE = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense", "Zlib"}
BASE = "stars:20..500 size:100..30000 created:2018-01-01..2024-12-31 pushed:>2022-06-01 fork:false archived:false"
PY = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"]
CC = ["CMakeLists.txt", "Makefile", "meson.build", "configure.ac"]
# (ecosystem label, language qualifier, count, root manifests, source extensions, extra requirement)
SLOTS = [
    ("python", "Python", 3, PY, [".py"], None),
    ("node-pnpm-or-yarn", "TypeScript", 1, ["package.json"], [".ts", ".tsx", ".js"], "pnpm-or-yarn-lock"),
    ("node", "JavaScript", 1, ["package.json"], [".js", ".mjs", ".cjs", ".jsx"], None),
    ("node", "TypeScript", 1, ["package.json"], [".ts", ".tsx"], None),
    ("go", "Go", 2, ["go.mod"], [".go"], None),
    ("rust", "Rust", 2, ["Cargo.toml"], [".rs"], None),
    ("jvm-java", "Java", 1, ["pom.xml", "build.gradle", "build.gradle.kts"], [".java"], None),
    ("jvm-kotlin", "Kotlin", 1, ["build.gradle", "build.gradle.kts", "pom.xml"], [".kt", ".kts"], None),
    ("ruby", "Ruby", 1, ["Gemfile", "*.gemspec"], [".rb"], None),
    ("php", "PHP", 1, ["composer.json"], [".php"], None),
    ("dotnet", '"C#"', 1, ["**.csproj", "**.sln"], [".cs"], None),
    ("dart", "Dart", 1, ["pubspec.yaml"], [".dart"], None),
    ("elixir", "Elixir", 1, ["mix.exs"], [".ex", ".exs"], None),
    ("swift", "Swift", 1, ["Package.swift"], [".swift"], None),
    ("cpp", '"C++"', 1, CC, [".cpp", ".cc", ".cxx", ".hpp", ".h"], None),
    ("c", "C", 1, CC, [".c", ".h"], None),
]
SEARCH_LICENSES = ["mit", "apache-2.0", "bsd-3-clause"]
WEAK_WORDS = re.compile(r"\b(install\w*|usage|getting started|quick ?start)\b", re.I)


def gh(args, raw=False):
    for attempt in range(5):
        p = subprocess.run(["gh", "api", *args], capture_output=True)
        if p.returncode == 0:
            out = p.stdout.decode("utf-8", errors="replace")
            return out if raw else json.loads(out)
        err = p.stderr.decode("utf-8", errors="replace").lower()
        if "rate limit" in err or "secondary" in err:
            time.sleep(20 * (attempt + 1))
            continue
        return None
    return None


def manifest_ok(paths, root_names, wanted):
    for w in wanted:
        if w.startswith("**"):
            if any(p.endswith(w[2:]) for p in paths):
                return w[2:]
        elif w.startswith("*"):
            if any(n.endswith(w[1:]) for n in root_names):
                return w
        elif w in root_names:
            return w
    return None


def main(argv):
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else HERE / "repos.json"
    chosen, log, taken = [], [], set()
    for label, lang, count, manifests, exts, extra in SLOTS:
        got = 0
        for page, q in [(pg, f"language:{lang} license:{lc} {BASE}") for lc in SEARCH_LICENSES for pg in (1, 2, 3)]:
            if got >= count:
                break
            res = gh(["-X", "GET", "search/repositories", "-f", f"q={q}", "-f", "sort=stars", "-f", "order=desc",
                      "-f", "per_page=100", "-f", f"page={page}"])
            time.sleep(2.5)
            for it in (res or {}).get("items", []):
                if got >= count:
                    break
                full = it["full_name"]
                why = None
                lic = (it.get("license") or {}).get("spdx_id")
                if full.lower() in taken:
                    continue
                if it["owner"]["login"].lower() == "tanmayai23" or it.get("fork") or it.get("archived"):
                    why = "owner/fork/archived"
                elif lic not in PERMISSIVE:
                    why = f"license {lic}"
                if why:
                    log.append(f"{label}: skip {full}: {why}")
                    continue
                meta = gh([f"repos/{full}/readme"])
                if not meta or "/" in meta.get("path", "/"):
                    log.append(f"{label}: skip {full}: no root README")
                    continue
                text = base64.b64decode(meta.get("content") or "").decode("utf-8", errors="replace")
                nonblank = [l for l in text.splitlines() if l.strip()]
                if len(nonblank) > 15 or WEAK_WORDS.search(text):
                    log.append(f"{label}: skip {full}: README not weak ({len(nonblank)} non-blank lines)")
                    continue
                sha = (gh([f"repos/{full}/commits/HEAD", "-q", ".sha"], raw=True) or "").strip()
                tree = gh([f"repos/{full}/git/trees/{sha}?recursive=1"]) if sha else None
                if not tree or tree.get("truncated"):
                    log.append(f"{label}: skip {full}: tree unavailable/truncated")
                    continue
                blobs = [e["path"] for e in tree["tree"] if e["type"] == "blob"]
                root_names = {p for p in blobs if "/" not in p}
                if len(blobs) >= 2000 or it["size"] >= 30000:
                    log.append(f"{label}: skip {full}: too big ({len(blobs)} files, {it['size']} KB)")
                    continue
                man = manifest_ok(blobs, root_names, manifests)
                if not man:
                    log.append(f"{label}: skip {full}: no manifest {manifests}")
                    continue
                if extra == "pnpm-or-yarn-lock" and not ({"pnpm-lock.yaml", "yarn.lock"} & root_names):
                    log.append(f"{label}: skip {full}: no pnpm-lock.yaml/yarn.lock")
                    continue
                src = [p for p in blobs if any(p.lower().endswith(e) for e in exts)]
                if len(src) < 5:
                    log.append(f"{label}: skip {full}: only {len(src)} source files")
                    continue
                feats = [f for f in ("Makefile", "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yaml",
                                     ".env.example", ".env.sample", "justfile", "pnpm-lock.yaml", "yarn.lock",
                                     "package-lock.json") if f in root_names]
                chosen.append({
                    "repo": full, "sha": sha, "license": lic, "language": it.get("language"), "ecosystem": label,
                    "manifest": man, "readme_file": meta["path"], "readme_lines": len(text.splitlines()),
                    "readme_nonblank_lines": len(nonblank), "files": len(blobs), "size_kb": it["size"],
                    "stars_at_selection": it["stargazers_count"], "root_features": feats,
                    "why": f"{len(nonblank)}-line README with no install/usage, {len(src)} {lang.strip(chr(34))} source files, {man}",
                    "query": q,
                })
                taken.add(full.lower())
                got += 1
                log.append(f"{label}: TAKE {full}")
                print(f"{label}: TAKE {full}", flush=True)
        if got < count:
            log.append(f"{label}: WARNING only {got}/{count} found")
            print(f"{label}: WARNING only {got}/{count} found", flush=True)
    doc = {
        "selected_utc": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()),
        "procedure": __doc__.split("Usage:")[0].strip(),
        "search_sort": "stars desc, per_page=100, pages 1-3 per license query",
        "search_licenses": SEARCH_LICENSES,
        "repos": chosen,
    }
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    (out.with_suffix(".selection-log.txt")).write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"selected {len(chosen)} repos -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
