#!/usr/bin/env python3
"""Check that every external link, image, badge and widget URL in a README responds.

Finds inline links and images, reference-style definitions ([id]: url), and HTML
<a>/<img>/<source> tags. URLs inside fenced code blocks and inline code are skipped.

Stdlib only. Needs network access — run only when the user allows it.
Usage:
    python check_links.py README.md [--timeout 10] [--json] [--images-only]

Redirects (301/302/303/307/308) are followed on every Python version.

Statuses:
    OK            2xx after redirects
    SLOW          answered, but took more than 8 s (common for cold widget instances)
    RATE-LIMITED  429
    UNVERIFIED    the host blocks automated checks, so the link could not be tested:
                  401/403/429/999 from bot-blocking hosts (npmjs.com, linkedin.com,
                  x.com, medium.com, ...) and GitHub pages shown only to signed-in
                  users (/stargazers, /watchers, ...). Open these in a browser.
    WIDGET-ERROR  an SVG widget that returned an error card instead of a chart
    BROKEN        other 4xx/5xx, DNS, timeout or TLS errors

Exits 1 only for BROKEN or WIDGET-ERROR; SLOW, RATE-LIMITED and UNVERIFIED are
listed but don't fail CI.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
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


# Hosts that answer automated clients with 401/403/429/999 even when the page exists
# (Cloudflare bot checks, LinkedIn's 999). Subdomains match too.
BOT_BLOCKING_HOSTS = (
    "npmjs.com", "linkedin.com", "lnkd.in", "twitter.com", "x.com", "medium.com",
    "facebook.com", "instagram.com", "reddit.com", "quora.com", "stackoverflow.com",
    "stackexchange.com", "producthunt.com", "researchgate.net", "udemy.com", "fiverr.com",
    "upwork.com", "glassdoor.com", "indeed.com", "tiktok.com", "threads.net", "discord.com",
)
BOT_BLOCK_CODES = (401, 403, 429, 999)
# GitHub serves these repository pages only to signed-in users; anonymous requests get 404.
GITHUB_LOGIN_ONLY = re.compile(
    r"^/[^/]+/[^/]+/(stargazers|watchers|graphs/traffic|settings|network/members|community/license/new)(/|$)")
GITHUB_HOSTS = ("github.com", "www.github.com")


def unverifiable(url: str, code) -> str:
    """Say why an HTTP error from this URL proves nothing about the link, or return "" if it does."""
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if code in BOT_BLOCK_CODES and any(host == h or host.endswith("." + h) for h in BOT_BLOCKING_HOSTS):
        return "this site blocks automated checks; open it in a browser to confirm"
    if host in GITHUB_HOSTS and code in (401, 403, 404, 429) and GITHUB_LOGIN_ONLY.match(parts.path):
        return "GitHub shows this page only to signed-in users; open it in a browser to confirm"
    return ""


class RedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow 307/308 redirects for HEAD and GET and keep the method.

    urllib only follows 308 from Python 3.11, so on 3.8-3.10 a permanent redirect
    to a working page was reported as BROKEN 308. Older versions also turned a
    redirected HEAD into a GET.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        method = req.get_method()
        if code in (301, 302, 303, 307, 308) and method in ("GET", "HEAD"):
            newheaders = {k: v for k, v in req.headers.items() if k.lower() not in ("content-length", "content-type")}
            return urllib.request.Request(newurl.replace(" ", "%20"), headers=newheaders, method=method,
                                          origin_req_host=req.origin_req_host, unverifiable=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_302


def build_opener(ctx=None):
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx or ssl.create_default_context()),
                                       RedirectHandler())


def check(kind, url, timeout, opener=None):
    opener = opener or build_opener()
    t0 = time.time()
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with opener.open(req, timeout=timeout) as resp:
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
            if method == "HEAD" and e.code in (400, 401, 403, 404, 405, 501, 999):
                continue
            note = unverifiable(url, e.code)
            if note:
                return {"url": url, "kind": kind, "status": e.code, "result": "UNVERIFIED", "note": note,
                        "seconds": round(time.time() - t0, 2)}
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
    opener = build_opener()
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda ku: check(ku[0], ku[1], timeout, opener), urls))
    bad = [r for r in results if r["result"] != "OK"]
    if "--json" in argv:
        print(json.dumps({"checked": len(results), "problems": bad, "all": results}, indent=2))
    else:
        print(f"Checked {len(results)} URL(s): {len(results) - len(bad)} OK, {len(bad)} need attention")
        for r in sorted(bad, key=lambda r: r["result"]):
            print(f"  {r['result']:<13} {r.get('status') or '-':<4} {r['kind']:<5} {r['url']}" + (f"  ({r.get('error') or r.get('note')})" if r.get("error") or r.get("note") else ""))
    return 1 if any(r["result"] in ("BROKEN", "WIDGET-ERROR") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
