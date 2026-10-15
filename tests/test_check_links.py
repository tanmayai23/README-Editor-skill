"""Unit tests for check_links.py (resolves issue #29)."""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "readme-forge" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_links  # noqa: E402


class TestCheckLinksIssue29(unittest.TestCase):
    def test_balanced_parentheses_in_urls(self):
        """Regression test for issue #29: URLs containing parentheses must not be cut off."""
        sample = """# Documentation
See [Rust](https://en.wikipedia.org/wiki/Rust_(programming_language)) for details.
Nested: [Link](https://wikidata.org/math(func(x)))
"""
        urls = check_links.extract(sample, images_only=False)
        extracted_urls = [u for _, u in urls]

        self.assertIn("https://en.wikipedia.org/wiki/Rust_(programming_language)", extracted_urls)
        self.assertNotIn("https://en.wikipedia.org/wiki/Rust_(programming_language", extracted_urls)
        self.assertIn("https://wikidata.org/math(func(x))", extracted_urls)

    def test_reference_style_definitions(self):
        """Regression test for issue #29: Reference-style links and badges must be collected."""
        sample = """# Status
[![CI][ci-badge]][ci-link]

[ci-badge]: https://github.com/nope/nope/actions/workflows/ci.yml/badge.svg
[ci-link]: https://github.com/nope/nope/actions
[doc-ref]: <https://docs.rs/guide> "Documentation"
"""
        urls = check_links.extract(sample, images_only=False)
        url_dict = {u: k for k, u in urls}

        self.assertIn("https://github.com/nope/nope/actions/workflows/ci.yml/badge.svg", url_dict)
        self.assertEqual(url_dict["https://github.com/nope/nope/actions/workflows/ci.yml/badge.svg"], "image")

        self.assertIn("https://github.com/nope/nope/actions", url_dict)
        self.assertEqual(url_dict["https://github.com/nope/nope/actions"], "link")

        self.assertIn("https://docs.rs/guide", url_dict)

    def test_images_only_filters_links_and_keeps_badge_references(self):
        """When images_only=True, only images and badge reference definitions should be extracted."""
        sample = """# Project
[![CI][ci-badge]][ci-link]
[Website](https://my-actual-site.org)

[ci-badge]: https://img.shields.io/badge/status-active-green.svg
[ci-link]: https://my-actual-site.org/ci
"""
        urls = check_links.extract(sample, images_only=True)
        kinds = {u: k for k, u in urls}

        self.assertIn("https://img.shields.io/badge/status-active-green.svg", kinds)
        self.assertEqual(kinds["https://img.shields.io/badge/status-active-green.svg"], "image")
        self.assertNotIn("https://my-actual-site.org/ci", kinds)
        self.assertNotIn("https://my-actual-site.org", kinds)

    def test_fenced_code_blocks_are_skipped(self):
        """Links inside fenced code blocks should be skipped."""
        sample = """# Example
Real link: [Real](https://real-domain-xyz.com)

```markdown
[Fake in fence](https://fake-fenced-code-domain.com)
[fake-badge]: https://fake-fenced-code-domain.com/badge.svg
```
"""
        urls = check_links.extract(sample, images_only=False)
        extracted_urls = [u for _, u in urls]

        self.assertIn("https://real-domain-xyz.com", extracted_urls)
        self.assertNotIn("https://fake-fenced-code-domain.com", extracted_urls)
        self.assertNotIn("https://fake-fenced-code-domain.com/badge.svg", extracted_urls)


if __name__ == "__main__":
    unittest.main()
