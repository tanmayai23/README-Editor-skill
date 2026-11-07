"""Tests for readme-forge/scripts/check_links.py (the link checker). No real network calls."""
import importlib.util
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
