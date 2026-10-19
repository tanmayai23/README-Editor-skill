#!/usr/bin/env python3
"""Select + fetch the 'good' and 'neglected' README sets for scorer validation (the procedure in README.md).

Writes READMEs to WORK/readmes/{good,neglected}/OWNER__REPO.md and WORK/data/selection.json
(queries, skip log, rows with SHAs; repos.csv was written from those rows).
Usage: python bench/scorer-validation/select_repos.py WORK
Note: search results and default branches change over time, so a rerun will not reproduce the same
list; repos.csv pins the list that was actually scored.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path


def gh(args, raw=False, check=True):
    for attempt in range(4):
        p = subprocess.run(["gh", "api", *args], capture_output=True)
        if p.returncode == 0:
            out = p.stdout.decode("utf-8", errors="replace")
            return out if raw else json.loads(out)
        err = p.stderr.decode("utf-8", errors="replace")
        if "rate limit" in err.lower() or "secondary" in err.lower():
            time.sleep(30 * (attempt + 1))
            continue
        if check:
            raise RuntimeError(f"gh api {args}: {err.strip()}")
        return None
    raise RuntimeError(f"gh api {args}: rate limited")


def repo_meta(full):
    return gh([f"repos/{full}"], check=False)


def readme_info(full):
    """Return (name, raw_text) of the repo's README per GitHub, or (None, None)."""
    meta = gh([f"repos/{full}/readme"], check=False)
    if not meta:
        return None, None
    raw = gh([f"repos/{full}/readme", "-H", "Accept: application/vnd.github.raw"], raw=True, check=False)
    return meta.get("name"), raw


def head_sha(full):
    return gh([f"repos/{full}/commits/HEAD", "-q", ".sha"], raw=True).strip()


WORK = Path(sys.argv[1])
N = 25
rows, log = [], []
MD_NAME = re.compile(r"^readme(\.md|\.markdown)$", re.I)


def take(group, full, meta):
    name, text = readme_info(full)
    if not text or not name or not MD_NAME.match(name):
        log.append(f"{group}: skip {full}: README missing or not Markdown ({name})")
        return False
    sha = head_sha(full)
    (WORK / "readmes" / group / f"{full.replace('/', '__')}.md").write_text(text, encoding="utf-8")
    rows.append({"group": group, "repo": full, "sha": sha, "url": f"https://github.com/{full}/blob/{sha}/{name}",
                 "readme_file": name, "stars": meta.get("stargazers_count"), "language": meta.get("language")})
    return True


# ---------------- good: first 25 GitHub project links in awesome-readme "## Examples"
AWESOME_SHA = "67494300e0a6e3df6c6b50913b93207db90798b4"
for sub in ("data", "readmes/good", "readmes/neglected"):
    (WORK / sub).mkdir(parents=True, exist_ok=True)
src = gh([f"repos/matiassingers/awesome-readme/contents/readme.md?ref={AWESOME_SHA}", "-H", "Accept: application/vnd.github.raw"], raw=True)
sec = src.split("\n## Examples", 1)[1].split("\n## ", 1)[0]
seen, good = set(), 0
for m in re.finditer(r"\]\((https?://github\.com/[^)\s]+)\)", sec):
    if good >= N:
        break
    url = m.group(1)
    path = re.sub(r"https?://github\.com/", "", url).split("#")[0].split("?")[0].strip("/")
    parts = path.split("/")
    if len(parts) != 2:
        log.append(f"good: skip non-repo link {url}")
        continue
    full_guess = "/".join(parts)
    if full_guess.lower() in seen:
        continue
    seen.add(full_guess.lower())
    meta = repo_meta(full_guess)
    if not meta:
        log.append(f"good: skip {url}: repo not found")
        continue
    full = meta["full_name"]  # canonical (redirects/renames resolved)
    if meta.get("archived"):
        log.append(f"good: skip {full}: archived")
        continue
    if meta.get("fork"):
        log.append(f"good: note {full} is a fork (kept; rule only excludes archived)")
    if take("good", full, meta):
        good += 1
log.append(f"good: selected {good}")

# ---------------- neglected: per-language search, round-robin
LANGS = ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "Ruby", "PHP", "C#"]
QTPL = "language:{lang} stars:0..1 created:2019-01-01..2023-12-31 pushed:<2024-01-01 size:>50 fork:false archived:false"
queues, queries = {}, {}
for lang in LANGS:
    q = QTPL.format(lang='"C#"' if lang == "C#" else lang)
    queries[lang] = q
    res = gh(["-X", "GET", "search/repositories", "-f", f"q={q}", "-f", "sort=updated", "-f", "order=desc",
              "-f", "per_page=50"])
    queues[lang] = res["items"]
    time.sleep(3)
picked, counts = 0, {l: 0 for l in LANGS}
idx = {l: 0 for l in LANGS}
while picked < N:
    progressed = False
    for lang in LANGS:
        if picked >= N:
            break
        while idx[lang] < len(queues[lang]):
            it = queues[lang][idx[lang]]
            idx[lang] += 1
            if take("neglected", it["full_name"], it):
                picked += 1
                counts[lang] += 1
                progressed = True
                break
            log.append(f"neglected: skip {it['full_name']} ({lang})")
    if not progressed:
        break
log.append(f"neglected: selected {picked} {counts}")

(WORK / "data" / "selection.json").write_text(json.dumps({"queries": queries, "date_utc": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()),
                                                          "log": log, "rows": rows}, indent=2), encoding="utf-8")
print("\n".join(log))
print(len(rows))
