#!/usr/bin/env python3
"""Check that every external link, image, badge and widget URL in a README responds.

Finds inline links and images, reference-style definitions ([id]: url), and HTML
<a>/<img>/<source> tags. URLs inside fenced code blocks and inline code are skipped.

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


FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)(?!`)((?:(?!\n[ \t]*\n).)+?)(?<!`)\1(?!`)", re.S)
REF_DEF = re.compile(r"^ {0,3}\[([^\]]+)\]:[ \t]*(?:<([^>\s]+)>|(\S+))", re.M)
IMG_REF = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
IMG_SHORTCUT = re.compile(r"!\[([^\]]+)\](?![\[(:])")
HTTP = re.compile(r"https?://", re.I)


def strip_code(text: str) -> str:
    """Blank out fenced code blocks and inline code spans so their URLs are not checked."""
    out, fence = [], None
    for line in text.split("\n"):
        m = FENCE.match(line)
        if fence is None:
            # A backtick fence's info string can't contain a backtick (that's inline code).
            if m and not (m.group(1)[0] == "`" and "`" in line[m.end():]):
                fence = m.group(1)
                out.append("")
            else:
                out.append(line)
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line[m.end():].strip():
                fence = None
            out.append("")
    return INLINE_CODE.sub(lambda c: re.sub(r"[^\n]", " ", c.group(0)), "\n".join(out))


def _destination(text: str, i: int):
    """Read the link destination that starts just after the '(' at index i.

    Handles <bracketed> destinations and balanced parentheses, so
    https://en.wikipedia.org/wiki/Rust_(programming_language) comes back whole.
    """
    n = len(text)
    while i < n and text[i] in " \t":
        i += 1
    if i < n and text[i] == "<":
        j = text.find(">", i + 1)
        if j == -1 or "\n" in text[i + 1:j]:
            return None
        return text[i + 1:j]
    depth, j = 0, i
    while j < n:
        c = text[j]
        if c == "\\" and j + 1 < n:
            j += 2
            continue
        if c.isspace():
            break
        if c == "(":
            depth += 1
        elif c == ")":
            if depth == 0:
                break
            depth -= 1
        j += 1
    return text[i:j] if j > i else None


def _is_image(text: str, close: int) -> bool:
    """True when the ']' at index close ends image alt text ('![...]') rather than link text."""
    depth, k = 0, close - 1
    while k >= 0:
        c = text[k]
        if c == "]":
            depth += 1
        elif c == "[":
            if depth == 0:
                return k > 0 and text[k - 1] == "!"
            depth -= 1
        elif c == "\n" and k > 0 and text[k - 1] == "\n":
            return False  # reached a blank line without finding the opening bracket
        k -= 1
    return False


def _label(s: str) -> str:
    return " ".join(s.split()).lower()


def extract(text: str, images_only: bool):
    text = strip_code(text)
    urls = []  # (position, kind, url), sorted by position at the end
    for m in re.finditer(r"\]\(", text):
        u = _destination(text, m.end())
        if u and HTTP.match(u):
            kind = "image" if _is_image(text, m.start()) else "link"
            if kind == "image" or not images_only:
                urls.append((m.start(), kind, u))
    for m in re.finditer(r"<(?:img|source)\b[^>]*?(?:src|srcset)=[\"'](https?://[^\"'\s]+)", text, re.I):
        urls.append((m.start(), "image", m.group(1)))
    if not images_only:
        for m in re.finditer(r"<a\b[^>]*href=[\"'](https?://[^\"']+)", text, re.I):
            urls.append((m.start(), "link", m.group(1)))
    # Reference definitions: [id]: url  or  [id]: <url>. A definition used by ![alt][id] is an image.
    image_labels = {_label(ref or alt) for alt, ref in IMG_REF.findall(text)}
    image_labels |= {_label(alt) for alt in IMG_SHORTCUT.findall(text)}
    for m in REF_DEF.finditer(text):
        u = m.group(2) or m.group(3)
        if not HTTP.match(u):
            continue
        kind = "image" if _label(m.group(1)) in image_labels else "link"
        if kind == "image" or not images_only:
            urls.append((m.start(), kind, u))
    seen, out = set(), []
    for _, kind, u in sorted(urls, key=lambda t: t[0]):
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
