"""Unit tests for check_links.py (resolves issue #30)."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "readme-forge" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_links  # noqa: E402


class TestCheckLinksIssue30(unittest.TestCase):
    def test_smart_redirect_handler_307_308(self):
        """SmartRedirectHandler should implement http_error_307 and http_error_308."""
        handler = check_links.SmartRedirectHandler()
        self.assertTrue(hasattr(handler, "http_error_307"))
        self.assertTrue(hasattr(handler, "http_error_308"))

    @patch("urllib.request.OpenerDirector.open")
    def test_npm_and_linkedin_403_reported_as_unverified(self, mock_open):
        """Regression test for issue #30: 403 from bot-blocking hosts should be UNVERIFIED, not BROKEN."""
        mock_open.side_effect = urllib.error.HTTPError(
            url="https://www.npmjs.com/package/react",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None,
        )
        res = check_links.check("link", "https://www.npmjs.com/package/react", timeout=5.0)
        self.assertEqual(res["result"], "UNVERIFIED")
        self.assertEqual(res["status"], 403)

    @patch("urllib.request.OpenerDirector.open")
    def test_github_stargazers_404_reported_as_unverified(self, mock_open):
        """Regression test for issue #30: 404 from GitHub login-only pages should be UNVERIFIED, not BROKEN."""
        mock_open.side_effect = urllib.error.HTTPError(
            url="https://github.com/foo/bar/stargazers",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        res = check_links.check("link", "https://github.com/foo/bar/stargazers", timeout=5.0)
        self.assertEqual(res["result"], "UNVERIFIED")
        self.assertEqual(res["status"], 404)

    @patch("urllib.request.OpenerDirector.open")
    def test_genuinely_broken_link_still_reported_as_broken(self, mock_open):
        """Non-bot-blocking 404 should still be reported as BROKEN."""
        mock_open.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/nonexistent",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        res = check_links.check("link", "https://api.github.com/nonexistent", timeout=5.0)
        self.assertEqual(res["result"], "BROKEN")
        self.assertEqual(res["status"], 404)


if __name__ == "__main__":
    unittest.main()
