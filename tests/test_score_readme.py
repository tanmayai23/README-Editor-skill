"""Regression tests for readme-forge/scripts/score_readme.py link and anchor checks."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "readme-forge" / "scripts" / "score_readme.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "score"

_spec = importlib.util.spec_from_file_location("rf_score_readme", str(SCRIPT))
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)


def score_json(path, *args):
    proc = subprocess.run([sys.executable, str(SCRIPT), str(path), "--json"] + list(args),
                          capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)
    return json.loads(proc.stdout)


def messages(rep, category=None):
    return [f["message"] for f in rep["findings"] if category is None or f["category"] == category]


class AnchorSlugTest(unittest.TestCase):
    """Issue #27: slug headings the way GitHub does."""

    def test_slug_strips_inline_code_and_links(self):
        self.assertEqual(sr.slug("The `run` command"), "the-run-command")
        self.assertEqual(sr.slug("[Config reference](docs/guide.md)"), "config-reference")
        self.assertEqual(sr.slug("![logo](logo.png) Project"), "project")
        self.assertEqual(sr.slug("Hello, World!"), "hello-world")

    def test_duplicate_headings_get_numbered(self):
        text = "## Usage\n## Usage\n## Usage\n"
        hs = sr.headings(sr.strip_code(text))
        self.assertEqual(sr.heading_anchors(text, hs), ["usage", "usage-1", "usage-2"])

    def test_numbering_skips_a_slug_a_real_heading_already_has(self):
        # github-slugger: "Usage", "Usage 1", "Usage" -> usage, usage-1, usage-2
        text = "## Usage\n## Usage 1\n## Usage\n"
        hs = sr.headings(sr.strip_code(text))
        self.assertEqual(sr.heading_anchors(text, hs), ["usage", "usage-1", "usage-2"])

    def test_fixture_has_no_false_anchor_warnings(self):
        rep = score_json(FIXTURES / "anchors" / "README.md")
        anchor_warnings = [m for m in messages(rep, "links") if "in-page anchor" in m]
        for good in ("#usage'", "#usage-1'", "#the-run-command'", "#config-reference'"):
            self.assertFalse([m for m in anchor_warnings if good in m], anchor_warnings)
        # A genuinely broken anchor is still reported.
        self.assertEqual(anchor_warnings, ["in-page anchor '#no-such-heading' matches no heading"])


if __name__ == "__main__":
    unittest.main()
