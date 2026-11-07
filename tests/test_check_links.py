"""Tests for readme-forge/scripts/check_links.py (the link checker). No real network calls."""
import contextlib
import http.server
import importlib.util
import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "readme-forge" / "scripts" / "check_links.py"

_spec = importlib.util.spec_from_file_location("rf_check_links", str(SCRIPT))
cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cl)


def urls(text, images_only=False):
    return cl.extract(text, images_only)


class ReferenceLinks(unittest.TestCase):
    ISSUE = (
        "[![CI][ci-badge]][ci-link]\n"
        "[ci-badge]: https://github.com/nope/nope/actions/workflows/ci.yml/badge.svg\n"
        "[ci-link]: https://github.com/nope/nope/actions\n"
        "[Rust](https://en.wikipedia.org/wiki/Rust_(programming_language))\n"
    )

    def test_issue_example_is_checked_correctly(self):
        self.assertEqual(urls(self.ISSUE), [
            ("image", "https://github.com/nope/nope/actions/workflows/ci.yml/badge.svg"),
            ("link", "https://github.com/nope/nope/actions"),
            ("link", "https://en.wikipedia.org/wiki/Rust_(programming_language)"),
        ])

    def test_images_only_keeps_reference_badge(self):
        self.assertEqual(urls(self.ISSUE, images_only=True), [
            ("image", "https://github.com/nope/nope/actions/workflows/ci.yml/badge.svg"),
        ])

    def test_angle_bracket_definition(self):
        self.assertEqual(urls("[docs]: <https://docs.example.org/guide> \"Guide\"\n"),
                         [("link", "https://docs.example.org/guide")])

    def test_definition_indented_and_with_title(self):
        self.assertEqual(urls("   [Home]: https://home.example.org 'Home page'\n"),
                         [("link", "https://home.example.org")])

    def test_collapsed_and_shortcut_image_references(self):
        text = "![Logo][]\n![Banner]\n\n[logo]: https://cdn.example.org/logo.png\n[banner]: https://cdn.example.org/b.svg\n"
        self.assertEqual(urls(text), [
            ("image", "https://cdn.example.org/logo.png"),
            ("image", "https://cdn.example.org/b.svg"),
        ])

    def test_relative_and_anchor_definitions_skipped(self):
        self.assertEqual(urls("[a]: ./docs/a.md\n[b]: #usage\n[c]: mailto:x@y.z\n"), [])


class InlineLinks(unittest.TestCase):
    def test_balanced_parentheses(self):
        self.assertEqual(urls("See [it](https://en.wikipedia.org/wiki/Foo_(bar)_(baz)) now."),
                         [("link", "https://en.wikipedia.org/wiki/Foo_(bar)_(baz)")])

    def test_unbalanced_closing_paren_ends_destination(self):
        self.assertEqual(urls("(see [x](https://x.example.org/a))"),
                         [("link", "https://x.example.org/a")])

    def test_title_is_not_part_of_url(self):
        self.assertEqual(urls('[x](https://x.example.org/a "A (title)")'),
                         [("link", "https://x.example.org/a")])

    def test_angle_bracket_destination(self):
        self.assertEqual(urls("[x](<https://x.example.org/a b>)"),
                         [("link", "https://x.example.org/a b")])

    def test_badge_inside_link_gives_image_and_link(self):
        text = "[![PyPI](https://img.shields.io/pypi/v/x.svg)](https://pypi.org/project/x/)"
        self.assertEqual(urls(text), [
            ("image", "https://img.shields.io/pypi/v/x.svg"),
            ("link", "https://pypi.org/project/x/"),
        ])
        self.assertEqual(urls(text, images_only=True), [("image", "https://img.shields.io/pypi/v/x.svg")])

    def test_html_tags_still_found(self):
        text = '<a href="https://a.example.org/"><img src="https://img.example.org/i.png" alt="i"></a>'
        self.assertEqual(urls(text), [("link", "https://a.example.org/"), ("image", "https://img.example.org/i.png")])

    def test_duplicates_and_skipped_hosts(self):
        text = "[a](https://a.example.org/) [b](https://a.example.org/) [c](http://localhost:3000) [d](#top)"
        self.assertEqual(urls(text), [("link", "https://a.example.org/")])


class CodeIsSkipped(unittest.TestCase):
    def test_fenced_backticks(self):
        text = "```markdown\n[x](https://in-fence.example.org/)\n[r]: https://ref-in-fence.example.org/\n```\n[y](https://after.example.org/)\n"
        self.assertEqual(urls(text), [("link", "https://after.example.org/")])

    def test_fenced_tildes_and_longer_fence(self):
        text = "~~~~\n~~~\n[x](https://in-fence.example.org/)\n~~~~\n[y](https://after.example.org/)\n"
        self.assertEqual(urls(text), [("link", "https://after.example.org/")])

    def test_indented_fence(self):
        text = "1. Step\n   ```bash\n   curl https://x.example.org [x](https://in-fence.example.org/)\n   ```\n"
        self.assertEqual(urls(text), [])

    def test_inline_code(self):
        text = "Write `[x](https://code.example.org/)` or ``a ` [y](https://code2.example.org/)`` then [z](https://real.example.org/)."
        self.assertEqual(urls(text), [("link", "https://real.example.org/")])

    def test_unclosed_backtick_does_not_hide_later_paragraphs(self):
        text = "A stray ` backtick.\n\nAnother ` one, then [z](https://real.example.org/)."
        self.assertEqual(urls(text), [("link", "https://real.example.org/")])


class _Handler(http.server.BaseHTTPRequestHandler):
    """Local test server: /old -> 308 -> /ok, /temp -> 307 -> /ok, /ok 200, anything else 404."""
    seen = []

    def _reply(self, with_body):
        _Handler.seen.append((self.command, self.path))
        if self.path in ("/old", "/temp"):
            self.send_response(308 if self.path == "/old" else 307)
            self.send_header("Location", "/ok")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = b"ok" if self.path == "/ok" else b"missing"
        self.send_response(200 if self.path == "/ok" else 404)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if with_body:
            self.wfile.write(body)

    def do_HEAD(self):
        self._reply(False)

    def do_GET(self):
        self._reply(True)

    def log_message(self, *args):
        pass


class LocalServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        _Handler.seen = []
        # No proxies, so a proxy set in the environment can't intercept 127.0.0.1.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), cl.RedirectHandler())

    def check(self, path):
        return cl.check("link", self.base + path, 5, self.opener)

    def test_308_is_followed_and_keeps_head(self):
        r = self.check("/old")
        self.assertEqual((r["result"], r["status"]), ("OK", 200))
        self.assertEqual(_Handler.seen, [("HEAD", "/old"), ("HEAD", "/ok")])

    def test_307_is_followed(self):
        r = self.check("/temp")
        self.assertEqual((r["result"], r["status"]), ("OK", 200))

    def test_200(self):
        self.assertEqual(self.check("/ok")["result"], "OK")

    def test_404_is_broken(self):
        r = self.check("/nope")
        self.assertEqual((r["result"], r["status"]), ("BROKEN", 404))


class RedirectHandlerLogic(unittest.TestCase):
    """The handler itself, so 308 support is tested even on Python 3.11+ where urllib has it built in."""

    def redirect(self, code, method):
        req = urllib.request.Request("https://a.example.org/old", method=method, headers={"User-Agent": cl.UA})
        return cl.RedirectHandler().redirect_request(req, None, code, "", {}, "https://a.example.org/new")

    def test_308_and_307_keep_method(self):
        for code in (307, 308):
            for method in ("HEAD", "GET"):
                new = self.redirect(code, method)
                self.assertEqual((new.full_url, new.get_method()), ("https://a.example.org/new", method))
                self.assertEqual(new.get_header("User-agent"), cl.UA)

    def test_308_dispatch_exists(self):
        self.assertTrue(callable(getattr(cl.RedirectHandler(), "http_error_308", None)))


class HostClassification(unittest.TestCase):
    def test_bot_blocking_hosts(self):
        for url, code in [("https://www.npmjs.com/package/react", 403),
                          ("https://npmjs.com/package/react", 401),
                          ("https://www.linkedin.com/in/someone", 999),
                          ("https://x.com/someone", 403),
                          ("https://medium.com/@someone", 429)]:
            self.assertTrue(cl.unverifiable(url, code), (url, code))

    def test_real_errors_stay_broken(self):
        for url, code in [("https://www.npmjs.com/package/react", 404),
                          ("https://www.linkedin.com/in/someone", 500),
                          ("https://notnpmjs.com/x", 403),
                          ("https://npmjs.com.evil.example.org/x", 403),
                          ("https://github.com/owner/repo", 404),
                          ("https://github.com/owner/repo/issues", 404),
                          ("https://github.com/owner/stargazers", 404)]:
            self.assertFalse(cl.unverifiable(url, code), (url, code))

    def test_github_login_only_pages(self):
        for path in ("stargazers", "watchers", "settings", "graphs/traffic", "network/members"):
            self.assertTrue(cl.unverifiable("https://github.com/owner/repo/" + path, 404), path)
        self.assertTrue(cl.unverifiable("https://github.com/owner/repo/stargazers?tab=x", 404))


class _FakeOpener:
    """Stands in for the urllib opener: raises the HTTP error mapped to each URL."""

    def __init__(self, codes):
        self.codes = codes

    def open(self, req, timeout=None):
        code = self.codes[req.full_url]
        raise urllib.error.HTTPError(req.full_url, code, "error", {}, io.BytesIO(b""))


class ExitCode(unittest.TestCase):
    def run_main(self, codes, *flags):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("\n".join("[l%d](%s)" % (i, u) for i, u in enumerate(codes)), encoding="utf-8")
            out = io.StringIO()
            with mock.patch.object(cl, "build_opener", return_value=_FakeOpener(codes)), \
                    contextlib.redirect_stdout(out):
                rc = cl.main(["check_links.py", str(readme)] + list(flags))
        return rc, out.getvalue()

    def test_issue_links_do_not_fail(self):
        rc, out = self.run_main({
            "https://www.npmjs.com/package/react": 403,
            "https://github.com/owner/repo/stargazers": 404,
        })
        self.assertEqual(rc, 0)
        self.assertIn("UNVERIFIED", out)
        self.assertNotIn("BROKEN", out)
        self.assertIn("Checked 2 URL(s): 0 OK, 2 need attention", out)

    def test_json_reports_unverified(self):
        rc, out = self.run_main({"https://www.linkedin.com/in/someone": 999}, "--json")
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual([p["result"] for p in data["problems"]], ["UNVERIFIED"])

    def test_broken_still_fails(self):
        rc, out = self.run_main({"https://www.npmjs.com/package/react": 403,
                                 "https://dead.example.org/page": 404})
        self.assertEqual(rc, 1)
        self.assertIn("BROKEN", out)


if __name__ == "__main__":
    unittest.main()
