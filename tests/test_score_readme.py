"""Regression tests for readme-forge/scripts/score_readme.py link and anchor checks."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
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


LINKS_README = """# Links

Regression fixture for issue #28: none of these links should be reported missing, except one.

- [Spaced file](docs/my%20file.md)
- [Root-relative guide](/docs/guide.md)
- ![Spaced logo](img/my%20logo.png)
- [Section of the spaced file](docs/my%20file.md#part)
- [Missing on purpose](docs/missing.md)

An example from the docs, never checked:

```markdown
See [the reference](./docs/not-real.md) and ![diagram](./img/not-real.png).
```

Inline code is prose too: `[x](./also-not-real.md)`.
"""


class RelativeLinkTest(unittest.TestCase):
    """Issue #28: encoded, root-relative and code-block links."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def write(self, name, text="x\n"):
        p = self.tmp / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def missing(self, readme):
        return [m for m in messages(score_json(readme), "links") if "target not found" in m]

    def test_encoded_root_relative_and_code_links(self):
        (self.tmp / ".git").mkdir()                    # repo root
        self.write("docs/guide.md")                     # /docs/guide.md lives here
        self.write("pkg/docs/my file.md")               # README is one level down
        self.write("pkg/img/my logo.png")
        readme = self.write("pkg/README.md", LINKS_README)
        self.assertEqual(self.missing(readme), ["relative link/image target not found: docs/missing.md"])

    def test_git_file_marks_a_worktree_root(self):
        (self.tmp / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")
        self.write("docs/guide.md")
        readme = self.write("pkg/README.md", "# T\n\n[Guide](/docs/guide.md)\n")
        self.assertEqual(self.missing(readme), [])

    def test_root_relative_without_git_uses_readme_dir(self):
        if any((d / ".git").exists() for d in self.tmp.resolve().parents):
            self.skipTest("temp dir sits inside a git repository")
        self.write("docs/guide.md")
        readme = self.write("README.md", "# T\n\n[Guide](/docs/guide.md)\n[Gone](/docs/gone.md)\n")
        self.assertEqual(self.missing(readme), ["relative link/image target not found: /docs/gone.md"])

    def test_links_ignores_code(self):
        found = [lk["href"] for lk in sr.links(LINKS_README)]
        self.assertNotIn("./docs/not-real.md", found)
        self.assertNotIn("./also-not-real.md", found)
        self.assertIn("/docs/guide.md", found)


if __name__ == "__main__":
    unittest.main()
