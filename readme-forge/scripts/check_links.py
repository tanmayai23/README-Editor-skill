#!/usr/bin/env python3
"""Check that every external link, image, badge and widget URL in a README responds.

Stdlib only. Needs network access — run only when the user allows it.
Usage:
    python check_links.py README.md [--timeout 10] [--json] [--images-only]

Reports: OK (2xx/3xx), BROKEN (4xx/5xx/DNS), SLOW (> 5s — common for cold widget
instances), RATE-LIMITED (429 or a widget error SVG), and SVG widgets that return
an error card instead of a chart.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (readme-forge link checker; +https://github.com)"
SKIP = re.compile(r"^(mailto:|tel:|#|data:)|localhost|127\.0\.0\.1|example\.com|\{\{")
ERROR_SVG = re.compile(rb"(something went wrong|rate limit|could not fetch|not found|maximum retries exceeded|user not found)", re.I)


def strip_code(text: str) -> str:
    """Blank out fenced code blocks (keeps line numbers)."""
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
        out.append("" if fence else line)
    return "\n".join(out)


def _extract_markdown_targets(text: str):
    """Find ![...](dest) and [...](dest) handling balanced parens in dest."""
    items = []
    for m in re.finditer(r"(!)?\[(?:[^\]\\]|\\.)*\]\(", text):
        is_img = bool(m.group(1))
        start_idx = m.end()
        # Optional leading <...>
        if start_idx < len(text) and text[start_idx] == "<":
            close_angle = text.find(">", start_idx + 1)
            if close_angle != -1:
                items.append(("image" if is_img else "link", text[start_idx + 1:close_angle].strip()))
                continue
        depth = 1
        i = start_idx
        while i < len(text):
            c = text[i]
            if c == "\\":
                i += 2
                continue
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    raw = text[start_idx:i].strip()
                    url = raw.split()[0] if raw else ""
                    items.append(("image" if is_img else "link", url))
                    break
            elif c in ("\r", "\n"):
                break
            i += 1
    return items


def extract(text: str, images_only: bool):
    nocode = strip_code(text)
    urls = []

    # Markdown inline links/images (with balanced parentheses support)
    for kind, u in _extract_markdown_targets(nocode):
        if u.startswith(("http://", "https://")):
            if not images_only or kind == "image":
                urls.append((kind, u))

    # Reference link definitions: [id]: https://...
    ref_defs = {}
    for m in re.finditer(r"^\s*\[([^\]]+)\]:\s*<?(https?://\S+?)>?(?:\s+[\"'(].*)?$", nocode, re.M):
        ref_defs[m.group(1).lower()] = m.group(2)

    img_refs = set(m.group(1).lower() for m in re.finditer(r"!\[(?:[^\]\\]|\\.)*\]\[([^\]]+)\]", nocode))
    for ref_id, u in ref_defs.items():
        is_img = ref_id in img_refs or bool(re.search(r"\.(svg|png|jpe?g|gif|webp)(?:$|\?)|\b(badge|shields\.io)\b", u, re.I))
        if not images_only or is_img:
            urls.append(("image" if is_img else "link", u))

    # HTML tags
    for m in re.finditer(r"<(?:img|source)\b[^>]*?(?:src|srcset)=[\"'](https?://[^\"'\s]+)", nocode, re.I):
        urls.append(("image", m.group(1)))
    if not images_only:
        for m in re.finditer(r"<a\b[^>]*href=[\"'](https?://[^\"']+)", nocode, re.I):
            urls.append(("link", m.group(1)))

    seen, out = set(), []
    for kind, u in urls:
        u = u.replace("&amp;", "&")
        if u not in seen and not SKIP.search(u):
            seen.add(u)
            out.append((kind, u))
    return out


def check(kind, url, timeout):
    ctx = ssl.create_default_context()
    t0 = time.time()
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                status = resp.status
                ctype = resp.headers.get("Content-Type", "")
                body = resp.read(20000) if method == "GET" and "svg" in ctype else b""
                dt = time.time() - t0
                if body and ERROR_SVG.search(body) and kind == "image":
                    return {"url": url, "kind": kind, "status": status, "result": "WIDGET-ERROR", "seconds": round(dt, 2)}
                if method == "HEAD" and kind == "image" and "svg" in ctype:
                    continue  # re-fetch body to detect error cards
                return {"url": url, "kind": kind, "status": status, "result": "SLOW" if dt > 8 else "OK", "seconds": round(dt, 2)}
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 400, 404, 501):
                continue
            res = "RATE-LIMITED" if e.code == 429 else "BROKEN"
            return {"url": url, "kind": kind, "status": e.code, "result": res, "seconds": round(time.time() - t0, 2)}
        except Exception as e:  # DNS, timeout, SSL
            if method == "HEAD":
                continue
            return {"url": url, "kind": kind, "status": None, "result": "BROKEN", "error": str(e)[:120], "seconds": round(time.time() - t0, 2)}
    return {"url": url, "kind": kind, "status": None, "result": "BROKEN", "seconds": round(time.time() - t0, 2)}


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    text = Path(argv[1]).read_text(encoding="utf-8", errors="ignore")
    timeout = float(argv[argv.index("--timeout") + 1]) if "--timeout" in argv else 10.0
    urls = extract(text, "--images-only" in argv)
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda ku: check(ku[0], ku[1], timeout), urls))
    bad = [r for r in results if r["result"] != "OK"]
    if "--json" in argv:
        print(json.dumps({"checked": len(results), "problems": bad, "all": results}, indent=2))
    else:
        print(f"Checked {len(results)} URL(s): {len(results) - len(bad)} OK, {len(bad)} need attention")
        for r in sorted(bad, key=lambda r: r["result"]):
            print(f"  {r['result']:<13} {r.get('status') or '-':<4} {r['kind']:<5} {r['url']}" + (f"  ({r['error']})" if r.get("error") else ""))
    return 1 if any(r["result"] in ("BROKEN", "WIDGET-ERROR") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
