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
BOT_BLOCKING_HOSTS = re.compile(
    r"://(?:[^/]+\.)?(npmjs\.(?:com|org)|linkedin\.com|twitter\.com|x\.com)(?:/|$)",
    re.I,
)
GITHUB_LOGIN_PAGES = re.compile(
    r"^https?://github\.com/[^/]+/[^/]+/(stargazers|network/dependents|pulse|graphs/traffic)(?:/|$|\?)",
    re.I,
)


class SmartRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Ensure HTTP 307 and 308 redirects are followed across Python versions."""

    def http_error_307(self, req, fp, code, msg, headers):
        return self.do_redirect(req, fp, code, msg, headers)

    def http_error_308(self, req, fp, code, msg, headers):
        return self.do_redirect(req, fp, code, msg, headers)


def extract(text: str, images_only: bool):
    urls = []
    for m in re.finditer(r"!\[[^\]]*\]\((https?://[^)\s]+)", text):
        urls.append(("image", m.group(1)))
    for m in re.finditer(r"<(?:img|source)\b[^>]*?(?:src|srcset)=[\"'](https?://[^\"'\s]+)", text, re.I):
        urls.append(("image", m.group(1)))
    if not images_only:
        for m in re.finditer(r"(?<!!)\[[^\]]+\]\((https?://[^)\s]+)", text):
            urls.append(("link", m.group(1)))
        for m in re.finditer(r"<a\b[^>]*href=[\"'](https?://[^\"']+)", text, re.I):
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
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx), SmartRedirectHandler())
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
            if method == "HEAD" and e.code in (403, 405, 400, 404, 501):
                continue
            if e.code == 429:
                res = "RATE-LIMITED"
            elif (e.code in (401, 403, 999) and BOT_BLOCKING_HOSTS.search(url)) or (
                e.code in (401, 403, 404) and GITHUB_LOGIN_PAGES.search(url)
            ):
                res = "UNVERIFIED"
            else:
                res = "BROKEN"
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
