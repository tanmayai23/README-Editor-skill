#!/usr/bin/env python3
"""Score a README 0-100 and lint it. Stdlib only.

Usage:
    python score_readme.py README.md [--repo PATH] [--profile | --hf] [--json] [--min N]

Modes:
    (default)   project README rubric
    --profile   GitHub profile README rubric
    --hf        Hugging Face model/dataset/Space card rubric (validates YAML frontmatter)
Options:
    --repo PATH also check drift against the repository (scripts, package manager,
                env vars, license, runtime versions). Adds a 'drift' category.
    --json      machine-readable output
    --min N     exit 1 if score < N (use in CI)
    --color     force ANSI colors (auto on a terminal; NO_COLOR=1 disables)

Rubric details live in references/quality-rubric.md.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

FILLER = [
    "blazing fast", "blazingly fast", "lightning fast", "simply", "just run", "easy to use", "easy-to-use",
    "user-friendly", "robust", "seamless", "seamlessly", "cutting-edge", "cutting edge", "state-of-the-art solution",
    "leverage", "leverages", "revolutionary", "game-changer", "game changing", "next-generation", "world-class",
    "powerful and flexible", "best-in-class", "unleash", "supercharge", "effortless", "effortlessly",
    "in today's fast-paced", "look no further", "elevate your", "a plethora of", "delve", "comprehensive solution",
    "hassle-free", "obviously",
]
FILLER_WORDBOUND = {"simply", "robust", "leverage", "leverages", "delve", "obviously"}
GITHUB_ROUTE = re.compile(r"^(\.\./)+(actions|issues|pulls|wiki|releases|discussions|blob|tree|graphs|network|stargazers|fork|security|projects|compare|commits|labels|milestones)(/|$)")

FRAGILE_WIDGET_HOSTS = {
    "github-readme-stats.vercel.app": "public github-readme-stats instance is best-effort/rate-limited; self-host on Vercel or use the GitHub Action (see references/widgets.md)",
    "komarev.com/ghpvc": None,
}
DEAD_HOSTS = {
    "herokuapp.com": "Heroku free dynos were removed in 2022; this widget is almost certainly broken",
    "github-profile-trophy.vercel.app": "public trophy instance returns HTTP 402 (deployment disabled, Oct 2026); self-host or remove",
    "github-readme-activity-graph.vercel.app": "public activity-graph instance returns HTTP 402 (Oct 2026); self-host or use metrics/snake",
}

HF_LICENSES = {
    "apache-2.0", "mit", "openrail", "openrail++", "bigscience-openrail-m", "creativeml-openrail-m", "bigscience-bloom-rail-1.0",
    "bigcode-openrail-m", "afl-3.0", "artistic-2.0", "bsl-1.0", "bsd", "bsd-2-clause", "bsd-3-clause", "bsd-3-clause-clear",
    "c-uda", "cc", "cc0-1.0", "cc-by-2.0", "cc-by-2.5", "cc-by-3.0", "cc-by-4.0", "cc-by-sa-3.0", "cc-by-sa-4.0",
    "cc-by-nc-2.0", "cc-by-nc-3.0", "cc-by-nc-4.0", "cc-by-nd-4.0", "cc-by-nc-nd-3.0", "cc-by-nc-nd-4.0",
    "cc-by-nc-sa-2.0", "cc-by-nc-sa-3.0", "cc-by-nc-sa-4.0", "cdla-sharing-1.0", "cdla-permissive-1.0", "cdla-permissive-2.0",
    "wtfpl", "ecl-2.0", "epl-1.0", "epl-2.0", "etalab-2.0", "eupl-1.1", "eupl-1.2", "agpl-3.0", "gfdl", "gpl", "gpl-2.0",
    "gpl-3.0", "lgpl", "lgpl-2.1", "lgpl-3.0", "isc", "h-research", "intel-research", "lppl-1.3c", "ms-pl", "apple-ascl",
    "apple-amlr", "mpl-2.0", "odc-by", "odbl", "openmdw-1.0", "openrail++", "osl-3.0", "postgresql", "ofl-1.1", "ncsa", "unlicense", "zlib",
    "pddl", "lgpl-lr", "deepfloyd-if-license", "fair-noncommercial-research-license", "llama2", "llama3", "llama3.1",
    "llama3.2", "llama3.3", "llama4", "gemma", "unknown", "other",
}
HF_SPACE_COLORS = {"red", "yellow", "green", "blue", "indigo", "purple", "pink", "gray"}
HF_SPACE_SDKS = {"gradio", "docker", "static", "streamlit"}
HF_PIPELINE_TAGS = {
    "text-classification", "token-classification", "table-question-answering", "question-answering", "zero-shot-classification",
    "translation", "summarization", "feature-extraction", "text-generation", "fill-mask", "sentence-similarity",
    "text-to-speech", "text-to-audio", "automatic-speech-recognition", "audio-to-audio", "audio-classification",
    "voice-activity-detection", "depth-estimation", "image-classification", "object-detection", "image-segmentation",
    "text-to-image", "image-to-text", "image-to-image", "image-to-video", "unconditional-image-generation",
    "video-classification", "reinforcement-learning", "robotics", "tabular-classification", "tabular-regression",
    "tabular-to-text", "table-to-text", "multiple-choice", "text-ranking", "text-retrieval", "time-series-forecasting",
    "text-to-video", "image-text-to-text", "visual-question-answering", "document-question-answering",
    "zero-shot-image-classification", "graph-ml", "mask-generation", "zero-shot-object-detection", "text-to-3d",
    "image-to-3d", "image-feature-extraction", "video-text-to-text", "keypoint-detection", "visual-document-retrieval",
    "any-to-any", "video-to-video", "other", "audio-text-to-text", "image-text-to-image", "image-text-to-video",
}


class Report:
    def __init__(self):
        self.findings = []  # (level, category, message, line)
        self.cats = {}

    def add(self, level, cat, msg, line=None):
        self.findings.append({"level": level, "category": cat, "message": msg, "line": line})

    def score(self, cat, got, out_of):
        self.cats[cat] = {"score": round(max(0, min(got, out_of)), 1), "max": out_of}

    @property
    def total(self):
        got = sum(c["score"] for c in self.cats.values())
        mx = sum(c["max"] for c in self.cats.values()) or 1
        return round(100 * got / mx)


# ----------------------------------------------------------------------------- parsing
def strip_code(text: str) -> str:
    """Blank out fenced code blocks and inline code (keeps line numbers)."""
    out, fence = [], None
    for line in text.splitlines():
        m = re.match(r"^\s*(```+|~~~+)", line)
        if m:
            if fence is None:
                fence = m.group(1)[0] * 3
            elif line.strip().startswith(fence):
                fence = None
            out.append("")
            continue
        out.append("" if fence else re.sub(r"`[^`]*`", "``", line))
    return "\n".join(out)


def split_frontmatter(text: str):
    if text.startswith("---"):
        parts = text.split("\n---", 1)
        if len(parts) == 2:
            fm = parts[0][3:].strip("\n")
            body = parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
            return fm, body, fm.count("\n") + 2
    return None, text, 0


def parse_simple_yaml(fm: str) -> dict:
    """Tiny YAML subset parser: top-level keys, scalars, inline lists, '- item' lists, nested blocks kept raw."""
    data, key = {}, None
    for line in fm.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w\-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                data[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            elif val == "" or val in ("|", ">", "|-", ">-"):
                data[key] = []
            else:
                data[key] = val.strip("'\"")
            continue
        m = re.match(r"^\s+-\s+(.*)$", line)
        if m and key is not None and isinstance(data.get(key), list):
            data[key].append(m.group(1).strip().strip("'\""))
        elif key is not None and isinstance(data.get(key), list):
            data[key].append(line.strip())  # nested block, kept raw
    return data


def headings(text_nocode: str):
    hs = []
    for i, line in enumerate(text_nocode.splitlines(), 1):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if m:
            hs.append((len(m.group(1)), m.group(2).strip(), i))
        m2 = re.match(r"^\s*<h([1-6])[^>]*>(.*?)</h\1>", line, re.I)
        if m2:
            hs.append((int(m2.group(1)), re.sub(r"<[^>]+>", "", m2.group(2)).strip(), i))
    return hs


def find_section(hs, *patterns):
    for lvl, title, line in hs:
        t = re.sub(r"[^\w\s]", "", title.lower())
        if any(re.search(p, t) for p in patterns):
            return (lvl, title, line)
    return None


def images(text: str):
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", line):
            out.append({"alt": m.group(1).strip(), "src": m.group(2), "line": i, "kind": "md"})
        for m in re.finditer(r"<img\b([^>]*)>", line, re.I):
            attrs = m.group(1)
            src = re.search(r"src=[\"']([^\"']+)", attrs)
            alt = re.search(r"alt=[\"']([^\"']*)", attrs)
            out.append({"alt": alt.group(1).strip() if alt else None, "src": src.group(1) if src else "", "line": i, "kind": "html"})
    return out


def links(text: str):
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", line):
            out.append({"text": m.group(1), "href": m.group(2), "line": i})
        for m in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", line, re.I):
            out.append({"text": re.sub(r"<[^>]+>", "", m.group(2)), "href": m.group(1), "line": i})
    return out


def code_blocks(text: str):
    blocks, cur, lang, start = [], None, None, 0
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^\s*(```+|~~~+)\s*([\w+\-#.]*)", line)
        if m and cur is None:
            cur, lang, start = [], m.group(2).lower(), i
        elif m and cur is not None and not m.group(2):
            blocks.append({"lang": lang, "code": "\n".join(cur), "line": start})
            cur = None
        elif cur is not None:
            cur.append(line)
    return blocks


def slug(title: str) -> str:
    s = re.sub(r"<[^>]+>", "", title).strip().lower()
    s = re.sub(r"[^\w\- ]", "", s, flags=re.U)
    return s.replace(" ", "-")


# ----------------------------------------------------------------------------- shared checks
def quality_penalty(r: Report, cats) -> float:
    """Sum penalties; the same kind of finding counts at most 3 times (one bad pattern shouldn't zero the score)."""
    seen: dict = {}
    pen = 0.0
    for f in r.findings:
        if f["category"] not in cats:
            continue
        key = (f["level"], f["category"], f["message"].split(":")[0].split("'")[0][:40])
        seen[key] = seen.get(key, 0) + 1
        if seen[key] <= 3:
            pen += {"ERROR": 3, "WARN": 1.5, "INFO": 0.25}[f["level"]]
    return pen


def common_lints(r: Report, text, nocode, hs, imgs, lks, blocks, readme_path: Path, repo: Path | None, fm_offset=0):
    # headings
    h1s = [h for h in hs if h[0] == 1]
    if len(h1s) > 1:
        r.add("WARN", "structure", f"{len(h1s)} H1 headings; use exactly one (title) and H2 for sections", h1s[1][2])
    prev = 0
    for lvl, title, line in hs:
        if prev and lvl > prev + 1:
            r.add("WARN", "accessibility", f"heading level skips from H{prev} to H{lvl} ('{title[:40]}')", line)
        prev = lvl
        if not re.search(r"[A-Za-z0-9\u00C0-\uFFFF]", re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF]", "", title)):
            r.add("WARN", "accessibility", f"heading has no text besides emoji/symbols ('{title}')", line)
    # images alt
    for im in imgs:
        if im["alt"] is None or im["alt"] == "":
            r.add("ERROR", "accessibility", f"image without alt text: {im['src'][:80]}", im["line"])
        elif im["alt"].lower() in ("image", "img", "screenshot", "badge", "logo", "gif", "alt", "picture", "icon"):
            r.add("WARN", "accessibility", f"non-descriptive alt text '{im['alt']}' for {im['src'][:60]}", im["line"])
    # link text
    for lk in lks:
        if lk["text"].strip().lower() in ("here", "click here", "this", "link", "this link", "read more"):
            r.add("WARN", "accessibility", f"non-descriptive link text '{lk['text']}' → {lk['href'][:60]}", lk["line"])
    # anchors
    anchors = {slug(t) for _, t, _ in hs}
    anchors |= {a.lower() for a in re.findall(r"<[a-z0-9]+\b[^>]*\b(?:id|name)=[\"']([^\"']+)", text, re.I)}
    anchors |= {"readme", "top"}
    for lk in lks:
        if lk["href"].startswith("#") and len(lk["href"]) > 1:
            a = lk["href"][1:].lower()
            if a not in anchors and not any(a == x.strip("-") for x in anchors):
                r.add("WARN", "links", f"in-page anchor '{lk['href']}' matches no heading", lk["line"])
    # relative links / images exist
    base = readme_path.parent
    for item in [{"href": i["src"], "line": i["line"]} for i in imgs] + lks:
        h = item["href"]
        if not h or re.match(r"^(https?:|mailto:|#|data:|//|tel:)", h) or "{{" in h:
            continue
        if GITHUB_ROUTE.search(h):
            continue  # repo-relative GitHub routes (../../actions, ../../issues) resolve on github.com
        target = (base / h.split("#")[0].split("?")[0]).resolve()
        if not target.exists():
            r.add("ERROR", "links", f"relative link/image target not found: {h}", item["line"])
    # mermaid: common syntax breakers that render as "Syntax error" on GitHub
    for b in blocks:
        if b["lang"] != "mermaid":
            continue
        for k, ln in enumerate(b["code"].splitlines()):
            if re.match(r"\s*acc(Title|Descr)\s*:.*;", ln):
                r.add("ERROR", "quality", "mermaid accTitle/accDescr contains ';' (ends the statement and breaks the diagram); use commas", b["line"] + k + 1)
            m = re.search(r"(?:^|[\s;>|-])(end|graph|subgraph|flowchart|style|class|classDef|click|default|linkStyle|direction)\s*(?:[\[\(\{]|-->|---|-\.->|==>)", ln)
            if m and not re.match(r"\s*(subgraph|style|class|classDef|click|linkStyle|direction)\b", ln):
                r.add("ERROR", "quality", f"mermaid node id '{m.group(1)}' is a reserved word and breaks the diagram; rename the node", b["line"] + k + 1)
    # code blocks without language
    untagged = [b for b in blocks if not b["lang"]]
    if untagged:
        r.add("INFO", "quality", f"{len(untagged)} code block(s) without a language tag (no syntax highlighting)", untagged[0]["line"])
    # filler
    low_lines = nocode.splitlines()
    hits = []
    for i, line in enumerate(low_lines, 1):
        ll = line.lower()
        for f in FILLER:
            pat = r"\b" + re.escape(f) + r"\b" if f in FILLER_WORDBOUND or " " not in f else re.escape(f)
            if re.search(pat, ll):
                hits.append((f, i))
    for f, i in hits[:8]:
        r.add("WARN", "quality", f"filler/marketing phrase '{f}' — replace with a concrete fact", i)
    # placeholders
    for i, (line, plain) in enumerate(zip(text.splitlines(), nocode.splitlines()), 1):
        if re.search(r"\{\{[A-Z_]+\}\}|lorem ipsum|your[-_ ]?username|YOUR_[A-Z_]+|<your[-_ ][a-z]", line, re.I):
            r.add("ERROR", "quality", "unfilled template placeholder", i)
        elif "<!-- TODO" in plain:
            r.add("INFO", "quality", "TODO comment left for the author", i)
    # widget hosts
    for im in imgs:
        for host, why in DEAD_HOSTS.items():
            if host in im["src"]:
                r.add("ERROR", "widgets", f"{host}: {why}", im["line"])
        for host, why in FRAGILE_WIDGET_HOSTS.items():
            if why and host in im["src"]:
                r.add("WARN", "widgets", f"{host}: {why}", im["line"])
    # long lines of prose (walls of text)
    paras = re.split(r"\n\s*\n", nocode)
    walls = [p for p in paras if len(p) > 900 and not p.lstrip().startswith(("|", "<", "-", "*"))]
    if walls:
        r.add("WARN", "quality", f"{len(walls)} paragraph(s) over ~150 words; split or use lists")
    # bare URLs
    bare = [i for i, l in enumerate(low_lines, 1) if re.search(r"(?<![(<\"'=])\bhttps?://\S{40,}", l) and "](" not in l and not re.match(r"^\s*\[[^\]]+\]:\s", l)]
    if bare:
        r.add("INFO", "quality", f"{len(bare)} long bare URL(s); wrap as [descriptive text](url)", bare[0])
    # animated content
    anim = [im for im in imgs if re.search(r"\.gif\b|readme-typing-svg|snake|animated|giphy", im["src"], re.I)]
    if len(anim) > 2:
        r.add("WARN", "accessibility", f"{len(anim)} animated images; keep ≤2 and provide static alternatives (prefers-reduced-motion)", anim[0]["line"])
    return anchors


def drift_checks(r: Report, text: str, repo: Path):
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from analyze_repo import analyze  # type: ignore
        facts = analyze(repo)
    except Exception as e:  # pragma: no cover
        r.add("INFO", "drift", f"could not analyze repo for drift: {e}")
        return None
    low = text.lower()
    # commands are only checked inside code blocks and `inline code`, never in prose ("to make the …")
    code_text = "\n".join(b["code"] for b in code_blocks(text)) + "\n" + "\n".join(re.findall(r"`([^`\n]+)`", text))
    cmds = facts.get("commands", {})
    pm = facts.get("js_package_manager")
    if pm:
        used = {p for p in ("npm", "pnpm", "yarn", "bun") if re.search(rf"(^|\s|`){p}\s+(install|i|add|run|dev|build|test|start|ci)\b", code_text.lower(), re.M)}
        if used and pm not in used:
            r.add("ERROR", "drift", f"README uses {'/'.join(sorted(used))} but the repo lockfile indicates {pm}")
        scripts = (cmds.get("scripts") or {})
        for m in re.finditer(r"(?:npm run|pnpm(?: run)?|yarn(?: run)?|bun run)\s+([\w:\-.]+)", code_text):
            name = m.group(1)
            if name not in scripts and name not in ("install", "add", "i", "dlx", "create", "exec", "x", "global", "run", "remove", "init"):
                r.add("ERROR", "drift", f"README runs script '{name}' which does not exist in package.json")
    mk = cmds.get("make_targets")
    if mk:
        for m in re.finditer(r"(?:^|[\s;&|(])make\s+([\w\-.]+)", code_text, re.M):
            if m.group(1) not in mk and not m.group(1).startswith("-"):
                r.add("ERROR", "drift", f"README runs 'make {m.group(1)}' but Makefile has no such target")
    env = facts.get("env_vars") or {}
    from_example = [k for k, v in env.items() if str(v.get("source", "")).startswith((".env", "example"))]
    missing = [k for k in from_example if k not in text]
    if missing:
        r.add("WARN", "drift", f"env vars in .env example not documented: {', '.join(missing[:10])}")
    lic = (facts.get("license") or {}).get("spdx")
    if lic and lic != "UNKNOWN":
        short = lic.split("-")[0].lower()
        sec = re.search(r"licen[sc]e", low)
        if sec and short not in low:
            r.add("WARN", "drift", f"LICENSE file is {lic} but README doesn't name it")
    reqpy = facts.get("package", {}).get("requires_python")
    if reqpy:
        m = re.search(r"python\s*(?:>=|≥|version)?\s*(3\.\d+)", low)
        want = re.search(r"3\.\d+", reqpy)
        if m and want and m.group(1) != want.group(0):
            r.add("WARN", "drift", f"README mentions Python {m.group(1)} but pyproject requires-python is '{reqpy}'")
    eng = (facts.get("package", {}).get("engines") or {}).get("node")
    if eng:
        m = re.search(r"node(?:\.js)?\s*(?:>=|≥|v|version)?\s*(\d{2})", low)
        want = re.search(r"\d{2}", eng)
        if m and want and m.group(1) != want.group(0):
            r.add("WARN", "drift", f"README mentions Node {m.group(1)} but package.json engines.node is '{eng}'")
    if facts.get("docker", {}).get("compose_file") and "docker" not in low:
        r.add("INFO", "drift", "repo has docker compose but README doesn't explain running with Docker")
    if facts.get("ci") and "badge" not in low and "shields.io" not in low and "/badge.svg" not in low:
        r.add("INFO", "drift", "CI exists but no status badge")
    return facts



def design_lints(r: Report, text: str, imgs, readme_path: Path):
    """Visual-design checks: local SVG safety/size, dark variants, badge style consistency."""
    base = readme_path.parent
    seen = set()
    for im in imgs:
        src = im["src"].split("#")[0].split("?")[0]
        if not src or re.match(r"^(https?:|data:|//)", src) or not src.lower().endswith(".svg") or src in seen:
            continue
        seen.add(src)
        f = (base / src)
        if not f.is_file():
            continue
        size = f.stat().st_size
        body = f.read_text(encoding="utf-8", errors="ignore")[:2_000_000]
        if "<script" in body.lower():
            r.add("ERROR", "design", f"{src} contains <script>: it never runs inside an <img> and looks unsafe", im["line"])
        if re.search(r"@import|<link\b|url\(\s*['\"]?https?:|href=['\"]https?:[^'\"]+\.(?:png|jpe?g|gif|webp|svg|woff2?|ttf)", body, re.I):
            r.add("WARN", "design", f"{src} loads external resources (fonts/images); browsers ignore them in a README, so use system fonts or embed as data: URIs", im["line"])
        if size > 1_000_000:
            r.add("ERROR", "design", f"{src} is {size // 1024} KB; keep README SVGs under 100 KB", im["line"])
        elif size > 100_000:
            r.add("WARN", "design", f"{src} is {size // 1024} KB; aim for < 20 KB headers, < 100 KB max", im["line"])
    # GitHub empties a <picture> that opens after other markup on its line and closes on a later
    # line (e.g. `<a href="..."><picture>` then `<source>` below): dark mode and the link both break.
    # The same happens when a multi-line <picture> continues a paragraph, e.g. right under `<a id="top"></a>`.
    lines = strip_code(text).splitlines()
    for i, line in enumerate(lines, 1):
        m = re.search(r"<picture\b", line, re.I)
        if not m or re.search(r"</picture>", line[m.start():], re.I):
            continue
        prev = lines[i - 2] if i > 1 else ""
        if line[:m.start()].strip():
            r.add("ERROR", "design", "<picture> opens mid-line and closes on a later line; GitHub drops the "
                  "<source>, so the dark variant never shows and the link opens the image. Put <a>, "
                  "<picture> and </a> on their own lines, or the whole element on one line", i)
        elif prev.strip() and (not prev.lstrip().startswith("<") or re.fullmatch(r"\s*<a\b[^>]*>\s*</a>\s*", prev)):
            r.add("ERROR", "design", "<picture> continues the paragraph on the line above; GitHub drops the "
                  "<source>, so the dark variant never shows. Add a blank line before it", i)
    # dark/light: a local banner-like SVG shown without <picture>/theme fragment
    has_picture = "prefers-color-scheme" in text or "-mode-only" in text
    banners = [s_ for s_ in seen if re.search(r"(header|banner|hero|footer|logo)", s_, re.I)]
    if banners and not has_picture:
        r.add("INFO", "design", f"{banners[0]} has no dark/light variant switch; use <picture> + prefers-color-scheme (make_banner.py writes both)")
    # one badge style per page
    styles = set()
    for im in imgs:
        if "img.shields.io" in im["src"]:
            m = re.search(r"[?&]style=([\w-]+)", im["src"])
            styles.add(m.group(1) if m else "flat")
    if len(styles) > 1:
        r.add("WARN", "design", f"mixed badge styles ({', '.join(sorted(styles))}); use one style across the page")

# ----------------------------------------------------------------------------- project rubric
def score_project(text, path: Path, repo: Path | None) -> Report:
    r = Report()
    fm, body, off = split_frontmatter(text)
    nocode = strip_code(body)
    hs = headings(nocode)
    imgs = images(body)
    lks = links(body)
    blocks = code_blocks(body)
    lines = body.splitlines()
    n = len(lines)
    common_lints(r, body, nocode, hs, imgs, lks, blocks, path, repo)
    design_lints(r, body, imgs, path)

    # 1. Identity (15)
    s = 0
    if any(h[0] == 1 for h in hs) or re.search(r"<h1|<img[^>]+(logo|banner|header|hero|wordmark)", body[:3000], re.I):
        s += 4
    else:
        r.add("ERROR", "identity", "no title (H1)")
    first = []
    for l in nocode.splitlines()[:40]:
        t = l.strip()
        if not t or t.startswith(("#", "[!", "![", "[![", "---", "|", "<!--")):
            continue
        if t.startswith("<"):
            # centered HTML pitch, e.g. <p align="center"><b>…</b></p>: judge the visible text, ignore tag/img-only lines
            if re.match(r"<(img|picture|source|a\s|/|br|div|h1|h2|details|summary|table|td|tr)", t, re.I) and not re.match(r"<p\b", t, re.I):
                continue
            t = re.sub(r"<[^>]+>", " ", t).strip()
            if not t:
                continue
        first.append(t)
    pitch = next((l for l in first if len(l.split()) >= 5), None)
    if pitch:
        s += 6
        if len(pitch) > 300:
            r.add("WARN", "identity", "opening pitch is long; aim for one sentence (< 200 chars)")
            s -= 2
    else:
        r.add("ERROR", "identity", "no one-line description near the top explaining what the project is")
    badges = [i for i in imgs if re.search(r"shields\.io|badge|badgen|/workflows/.+\.svg|codecov\.io|coveralls", i["src"])]
    if badges:
        s += 3
        if len(badges) > 10:
            r.add("WARN", "visuals", f"{len(badges)} badges; keep 3–6 meaningful ones in the header")
            s -= 1
    else:
        r.add("INFO", "identity", "no status badges (build, version, license)")
    if find_section(hs, r"feature", r"highlight", r"why", r"what it does", r"overview", r"about"):
        s += 2
    else:
        r.add("WARN", "identity", "no Features/Overview section")
    r.score("identity", s, 15)

    # 2. Getting started (25)
    s = 0
    inst = find_section(hs, r"install", r"setup", r"getting started", r"quick ?start", r"set up")
    use = find_section(hs, r"usage", r"example", r"how to use", r"quick ?start", r"getting started", r"tutorial", r"api", r"commands")
    shell_blocks = [b for b in blocks if b["lang"] in ("bash", "sh", "shell", "console", "zsh", "powershell", "ps1", "cmd", "")]
    if inst:
        s += 7
        if inst[2] > max(60, 0.45 * n):
            r.add("WARN", "getting-started", f"installation/quickstart starts at line {inst[2]}; move it into the first screen (~line 40)")
            s -= 2
    else:
        r.add("ERROR", "getting-started", "no Installation / Getting Started / Quickstart section")
    if shell_blocks:
        s += 6
    else:
        r.add("ERROR", "getting-started", "no copy-pasteable shell commands in code blocks")
    if use:
        s += 6
    else:
        r.add("ERROR", "getting-started", "no Usage / Examples section")
    if len(blocks) >= 2:
        s += 3
    if find_section(hs, r"prereq", r"requirement", r"dependencies", r"before you begin") or re.search(r"\b(node(?:\.js)?|python|go|rust|java|ruby|php|\.net|dotnet|deno|bun)\s*(>=|≥|v?\d)", nocode, re.I):
        s += 3
    else:
        r.add("INFO", "getting-started", "no prerequisites (runtime versions, system deps)")
    r.score("getting-started", s, 25)

    # 3. Structure (15)
    s = 15
    h2 = [h for h in hs if h[0] == 2]
    if len(h2) < 3:
        r.add("WARN", "structure", "fewer than 3 sections (H2); README may be too thin")
        s -= 5
    has_toc = (find_section(hs, r"table of contents", r"contents", r"toc")
               or re.search(r"<summary>.*contents", body, re.I)
               or sum(1 for lk in lks if lk["href"].startswith("#") and len(lk["href"]) > 1) >= 4)
    if len(h2) > 6 and not has_toc:
        r.add("WARN", "structure", f"{len(h2)} sections but no table of contents")
        s -= 3
    empty = []
    blines = nocode.splitlines()
    for i, (lvl, t, ln) in enumerate(hs):
        nxt = hs[i + 1][2] if i + 1 < len(hs) else len(blines) + 1
        chunk = "\n".join(blines[ln:nxt - 1]).strip()
        raw_chunk = "\n".join(lines[ln:nxt - 1]).strip()
        if not chunk and not raw_chunk and (i + 1 >= len(hs) or hs[i + 1][0] <= lvl):
            empty.append((t, ln))
    for t, ln in empty:
        r.add("WARN", "structure", f"empty section '{t}'", ln)
        s -= 2
    if n > 700:
        r.add("WARN", "structure", f"README is {n} lines; move deep reference material to docs/ and link it")
        s -= 3
    elif n < 25:
        r.add("WARN", "structure", f"README is only {n} lines")
        s -= 4
    r.score("structure", s, 15)

    # 4. Visuals & architecture (10)
    s = 0
    has_mermaid = any(b["lang"] == "mermaid" for b in blocks)
    shots = [i for i in imgs if i not in badges and not re.search(r"shields\.io|badge", i["src"])]
    if has_mermaid or find_section(hs, r"architecture", r"how it works", r"design", r"diagram"):
        s += 5
    else:
        r.add("INFO", "visuals", "no architecture / how-it-works diagram (Mermaid renders natively on GitHub)")
    if shots:
        s += 4
    else:
        r.add("INFO", "visuals", "no screenshot/demo/logo image")
    if re.search(r"prefers-color-scheme|#gh-(dark|light)-mode-only|#hf-(dark|light)-mode-only", body):
        s += 1
    r.score("visuals", s, 10)

    # 5. Community & meta (15)
    s = 0
    if find_section(hs, r"licen[sc]e") or re.search(r"licen[sc]ed under|license-\w+-|/license", body, re.I):
        s += 5
    else:
        r.add("ERROR", "community", "no License section")
    if find_section(hs, r"contribut") or re.search(r"CONTRIBUTING\.md", body):
        s += 4
    else:
        r.add("WARN", "community", "no Contributing section / link to CONTRIBUTING.md")
    if find_section(hs, r"support", r"contact", r"help", r"community", r"faq", r"author", r"maintainer", r"acknowledg", r"credits") or re.search(r"\b(open|file|report)\s+an?\s+issue|\bissues\b|discussions", body, re.I):
        s += 3
    else:
        r.add("INFO", "community", "no support/contact/how to get help")
    if find_section(hs, r"test", r"development", r"contribut", r"local", r"build"):
        s += 3
    else:
        r.add("INFO", "community", "no Development/Testing instructions for contributors")
    r.score("community", s, 15)

    # 6. Quality & accessibility (20)
    # a near-empty README has nothing to lint; don't hand it free quality points
    r.score("quality", (20 - quality_penalty(r, ("accessibility", "links", "quality", "widgets", "design"))) * min(1.0, n / 40), 20)

    if repo is not None:
        before = len(r.findings)
        drift_checks(r, body, repo)
        dr = [f for f in r.findings[before:] if f["category"] == "drift"]
        penalty = sum({"ERROR": 4, "WARN": 2, "INFO": 0.5}[f["level"]] for f in dr)
        r.score("drift", 10 - penalty, 10)
    return r


# ----------------------------------------------------------------------------- profile rubric
def score_profile(text, path: Path) -> Report:
    r = Report()
    nocode = strip_code(text)
    hs = headings(nocode)
    imgs = images(text)
    lks = links(text)
    blocks = code_blocks(text)
    common_lints(r, text, nocode, hs, imgs, lks, blocks, path, None)
    design_lints(r, text, imgs, path)
    low = nocode.lower()

    s = 0  # intro (20)
    head = "\n".join(nocode.splitlines()[:25]).lower()
    if re.search(r"\b(hi|hey|hello|i'?m|i am|namaste|hola)\b", head) or any(h[0] <= 2 for h in hs[:2]):
        s += 8
    else:
        r.add("WARN", "intro", "no greeting / name heading at the top")
    if re.search(r"(developer|engineer|student|scientist|designer|researcher|founder|maintainer|enthusiast|architect|analyst|devops|programmer|freelanc)", low):
        s += 7
    else:
        r.add("WARN", "intro", "no role/identity line (what you do)")
    if re.search(r"(currently|working on|learning|focus|building|looking for|open to|ask me)", low):
        s += 5
    else:
        r.add("INFO", "intro", "no 'currently working on / learning / open to' line")
    r.score("intro", s, 20)

    s = 0  # skills (15)
    icons = [i for i in imgs if re.search(r"skillicons\.dev|devicon|simpleicons|shields\.io/badge/.*logo=|vectorlogo|techstack", i["src"], re.I)]
    if icons or find_section(hs, r"skill", r"tech", r"stack", r"tools", r"languages"):
        s += 10
    else:
        r.add("WARN", "skills", "no skills / tech stack section")
    if len(icons) > 30:
        r.add("WARN", "skills", f"{len(icons)} tech icons; curate to the ≤15 you actually use")
    else:
        s += 5
    r.score("skills", s, 15)

    s = 0  # projects/work (15)
    if find_section(hs, r"project", r"work", r"featured", r"portfolio", r"pinned", r"open source", r"contribution", r"blog", r"writing", r"publication"):
        s += 15
    elif re.search(r"github\.com/[^/\s)]+/[^/\s)]+", text):
        s += 8
        r.add("INFO", "projects", "projects mentioned but no Featured Projects section")
    else:
        r.add("WARN", "projects", "no projects / work showcased")
    r.score("projects", s, 15)

    s = 0  # contact (15)
    socials = re.findall(r"(linkedin\.com|twitter\.com|x\.com|mailto:|dev\.to|medium\.com|hashnode|youtube\.com|instagram\.com|bsky\.app|mastodon|discord|kaggle\.com|leetcode\.com|stackoverflow\.com|huggingface\.co|substack|portfolio|\.dev\b|\.me\b|\.io\b)", text, re.I)
    if socials:
        s += 15 if len(set(map(str.lower, socials))) >= 2 else 10
    else:
        r.add("WARN", "contact", "no contact / social links")
    r.score("contact", s, 15)

    s = 15  # widgets (15)
    widgets = [i for i in imgs if re.search(r"readme-stats|streak|trophy|activity-graph|wakatime|metrics|snake|typing-svg|visitor|komarev|spotify|leetcard|stats", i["src"], re.I)]
    if len(widgets) > 6:
        r.add("WARN", "widgets", f"{len(widgets)} dynamic widgets; ≤4 keeps the page fast and readable")
        s -= 5
    if widgets and not re.search(r"prefers-color-scheme|theme=|#gh-(dark|light)-mode-only|transparent|bg_color|hide_border", text):
        r.add("WARN", "widgets", "widgets have no theme/transparent setting; they will clash in dark or light mode")
        s -= 4
    s -= 3 * sum(1 for f in r.findings if f["category"] == "widgets" and f["level"] == "ERROR")
    r.score("widgets", s, 15)

    s = 20  # quality & a11y (20)
    s -= quality_penalty(r, ("accessibility", "links", "quality", "design"))
    r.score("quality", s, 20)
    return r


# ----------------------------------------------------------------------------- HF rubric
def score_hf(text, path: Path) -> Report:
    r = Report()
    fm, body, off = split_frontmatter(text)
    nocode = strip_code(body)
    hs = headings(nocode)
    imgs = images(body)
    lks = links(body)
    blocks = code_blocks(body)
    common_lints(r, body, nocode, hs, imgs, lks, blocks, path, None)
    design_lints(r, body, imgs, path)
    s = 0  # frontmatter (40)
    kind = "model"
    if fm is None:
        r.add("ERROR", "frontmatter", "no YAML frontmatter (--- block at top); the Hub uses it for license, tags, widgets, search")
    else:
        d = parse_simple_yaml(fm)
        if "sdk" in d or "app_file" in d or "colorFrom" in d:
            kind = "space"
        elif "task_categories" in d or "size_categories" in d or "configs" in d or "pretty_name" in d:
            kind = "dataset"
        s += 10
        lic = d.get("license")
        if not lic:
            r.add("ERROR", "frontmatter", "missing 'license'")
        elif str(lic).lower() not in HF_LICENSES:
            r.add("WARN", "frontmatter", f"license '{lic}' is not a Hub license id (use 'other' + license_name + license_link)")
            s += 4
        else:
            s += 8
            if str(lic).lower() == "other" and not (d.get("license_name") and d.get("license_link")):
                r.add("ERROR", "frontmatter", "license: other requires license_name and license_link")
        if kind == "model":
            if d.get("pipeline_tag"):
                s += 6
                if d["pipeline_tag"] not in HF_PIPELINE_TAGS:
                    r.add("WARN", "frontmatter", f"pipeline_tag '{d['pipeline_tag']}' not a known Hub task")
            else:
                r.add("WARN", "frontmatter", "missing 'pipeline_tag' (enables the inference widget and task search)")
            if d.get("library_name"):
                s += 6
            else:
                r.add("WARN", "frontmatter", "missing 'library_name' (must be explicit for repos created after Aug 2024)")
            if d.get("base_model"):
                s += 4
                if not d.get("base_model_relation"):
                    r.add("INFO", "frontmatter", "base_model set; consider base_model_relation (adapter|merge|quantized|finetune)")
            else:
                r.add("INFO", "frontmatter", "no base_model (fine for from-scratch models; set it for fine-tunes/adapters/quantizations)")
                s += 2
            s += 6 if (d.get("language") or d.get("tags")) else 0
        elif kind == "dataset":
            for k, pts in (("task_categories", 6), ("language", 4), ("size_categories", 4), ("pretty_name", 4)):
                if d.get(k):
                    s += pts
                else:
                    r.add("WARN" if pts > 4 else "INFO", "frontmatter", f"missing '{k}'")
            s += 4
        else:
            for k in ("title", "sdk"):
                if not d.get(k):
                    r.add("ERROR", "frontmatter", f"Space config missing '{k}'")
                else:
                    s += 5
            if d.get("sdk") and d["sdk"] not in HF_SPACE_SDKS:
                r.add("ERROR", "frontmatter", f"sdk '{d['sdk']}' invalid; use gradio | docker | static | streamlit")
            if d.get("sdk") in ("gradio", "streamlit") and not d.get("app_file"):
                r.add("WARN", "frontmatter", "app_file not set (defaults vary); set it explicitly")
            elif d.get("app_file") or d.get("sdk") in ("docker", "static"):
                s += 4
            for c in ("colorFrom", "colorTo"):
                if d.get(c) and d[c] not in HF_SPACE_COLORS:
                    r.add("ERROR", "frontmatter", f"{c} '{d[c]}' invalid; allowed: {', '.join(sorted(HF_SPACE_COLORS))}")
            s += 4 if d.get("emoji") else 0
            s += 4 if d.get("short_description") else 0
            if not d.get("short_description"):
                r.add("INFO", "frontmatter", "no short_description (shown on the Space card)")
    r.score("frontmatter", s, 40)

    s = 0  # sections (40)
    if kind == "model":
        req = [("description|model details|overview|summary", 6, "Model description"),
               ("intended|uses|use cases|direct use", 6, "Intended uses"),
               ("out.of.scope|misuse|limitations", 4, "Out-of-scope use"),
               ("bias|risk|limitation", 6, "Bias, risks and limitations"),
               ("how to (get started|use)|usage|quick ?start|inference", 6, "How to get started (code)"),
               ("training", 4, "Training data & procedure"),
               ("evaluation|results|benchmark|metrics", 5, "Evaluation"),
               ("citation|bibtex", 3, "Citation")]
    elif kind == "dataset":
        req = [("description|summary|overview", 8, "Dataset description"),
               ("structure|fields|schema|instances|splits", 8, "Dataset structure"),
               ("creation|curation|source|collection", 6, "Dataset creation"),
               ("bias|limitation|considerations|risks", 6, "Bias / limitations"),
               ("usage|how to use|load", 6, "Usage (load_dataset snippet)"),
               ("licen[sc]|citation", 6, "License / citation")]
    else:
        req = [("about|description|overview|what", 15, "What the Space does"),
               ("usage|how to|instructions|example", 15, "How to use it"),
               ("model|credits|acknowledg|built with|license", 10, "Models / credits")]
    for pat, pts, label in req:
        if find_section(hs, pat):
            s += pts
        else:
            r.add("WARN", "sections", f"missing section: {label}")
    if kind != "space" and not any(b["lang"] in ("python", "py", "bash", "sh") for b in blocks):
        r.add("WARN", "sections", "no runnable code snippet")
        s -= 4
    if re.search(r"\[more information needed\]", body, re.I):
        n = len(re.findall(r"\[more information needed\]", body, re.I))
        r.add("INFO", "sections", f"{n} '[More Information Needed]' placeholder(s) — fill what you can")
    r.score("sections", s, 40)

    s = 20
    s -= quality_penalty(r, ("accessibility", "links", "quality", "design"))
    r.score("quality", s, 20)
    r.kind = kind
    return r


# ----------------------------------------------------------------------------- output
def grade(score):
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 55 else "F"


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in argv[1:]]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    path = Path(args[0])
    if not path.is_file():
        print(f"error: {path} not found", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n")
    repo = None
    if "--repo" in args:
        repo = Path(args[args.index("--repo") + 1])
    mode = "profile" if "--profile" in args else "hf" if "--hf" in args else "project"
    if mode == "project":
        rep = score_project(text, path, repo)
    elif mode == "profile":
        rep = score_profile(text, path)
    else:
        rep = score_hf(text, path)
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    rep.findings.sort(key=lambda f: (order[f["level"]], f["line"] or 0))
    total = rep.total
    if "--json" in args:
        print(json.dumps({"file": str(path), "mode": mode, "score": total, "grade": grade(total),
                          "categories": rep.cats, "findings": rep.findings,
                          **({"hf_kind": rep.kind} if hasattr(rep, "kind") else {})}, indent=2, ensure_ascii=False))
    else:
        # color: --color forces it, NO_COLOR disables it, otherwise only on a real terminal
        use_color = "--color" in args or (sys.stdout.isatty() and not os.environ.get("NO_COLOR"))
        C = (lambda code, s: f"\033[{code}m{s}\033[0m") if use_color else (lambda code, s: s)
        tone = lambda ratio: "32" if ratio >= 0.85 else "33" if ratio >= 0.6 else "31"  # green / yellow / red
        label = f"{mode}" + (f" ({rep.kind})" if hasattr(rep, "kind") else "")
        print(C("1;" + tone(total / 100), f"README score: {total}/100  grade {grade(total)}") + C("2", f"  [{label}]  {path}"))
        print(C("2", "─" * 64))
        for c, v in rep.cats.items():
            ratio = v["score"] / v["max"]
            filled = round(20 * ratio)
            bar = C(tone(ratio), "━" * filled) + C("2", "─" * (20 - filled))
            print(f"  {c:<16} {bar} {v['score']:>5}/{v['max']}")
        print(C("2", "─" * 64))
        if not rep.findings:
            print("  no findings")
        level_color = {"ERROR": "1;31", "WARN": "33", "INFO": "2"}
        for f in rep.findings:
            loc = f" (line {f['line']})" if f["line"] else ""
            lvl = f"{f['level']:<5}"
            print(f"  {C(level_color[f['level']], lvl)} [{f['category']}] {f['message']}{C('2', loc)}")
        errs = sum(1 for f in rep.findings if f["level"] == "ERROR")
        warns = sum(1 for f in rep.findings if f["level"] == "WARN")
        print(C("2", "─" * 64))
        print(f"  {errs} error(s), {warns} warning(s)")
    if "--min" in args:
        if total < int(args[args.index("--min") + 1]):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
