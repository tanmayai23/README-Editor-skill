"""Unit tests for score_readme.py (resolves issue #27)."""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "readme-forge" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import score_readme  # noqa: E402


class TestSlugAndAnchors(unittest.TestCase):
    def test_slug_formatting(self):
        self.assertEqual(score_readme.slug("Usage"), "usage")
        self.assertEqual(score_readme.slug("The `run` command"), "the-run-command")
        self.assertEqual(score_readme.slug("[Config reference](docs/guide.md)"), "config-reference")
        self.assertEqual(score_readme.slug("### Quick Start Guide"), "quick-start-guide")
        self.assertEqual(score_readme.slug("HTML <tag>in heading</tag>"), "html-in-heading")

    def test_anchors_regression_duplicate_code_and_links(self):
        """Regression test for issue #27: duplicate headings, inline code and markdown links in headings."""
        sample = """# Sample Project

A sample project overview.

## Table of Contents
- [Usage first](#usage)
- [Usage second](#usage-1)
- [The run command](#the-run-command)
- [Config reference](#config-reference)

## Usage
First usage section.

## Usage
Second usage section.

## The `run` command
Command details.

## [Config reference](docs/guide.md)
Reference details.
"""
        rep = score_readme.score_project(sample, Path("README.md"), None)
        anchor_warnings = [
            f["message"] for f in rep.findings
            if f["category"] == "links" and "matches no heading" in f["message"]
        ]
        self.assertEqual(anchor_warnings, [], f"Expected no anchor warnings, but got: {anchor_warnings}")


if __name__ == "__main__":
    unittest.main()
