"""Tests for readme-forge-design/scripts/make_page.py (the page kit). No network."""
import contextlib
import importlib.util
import io
import re
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "readme-forge-design"

_spec = importlib.util.spec_from_file_location("rf_make_page", str(DESIGN / "scripts" / "make_page.py"))
make_page = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_page)


def build_example(name, tmp):
    """Copy an example spec into tmp and build it there; returns (README text, assets dir)."""
    spec = Path(tmp) / "page.json"
    shutil.copy(DESIGN / "examples" / name / "page.json", spec)
    with contextlib.redirect_stdout(io.StringIO()):
        make_page.build(spec, None, Path(tmp) / "preview.html")
    readme = (Path(tmp) / "README.md").read_text(encoding="utf-8")
    assets = next(p for p in Path(tmp).rglob("*-light.svg")).parent
    return readme, assets


class PageKitTests(unittest.TestCase):
    def test_profile_example_writes_every_card_in_both_themes(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme, assets = build_example("keynote-profile", tmp)
            light = sorted(p.name[:-10] for p in assets.glob("*-light.svg"))
            dark = sorted(p.name[:-9] for p in assets.glob("*-dark.svg"))
            self.assertEqual(light, dark)
            self.assertIn("hero", light)
            self.assertIn("footer", light)
            for svg in assets.glob("*.svg"):
                root = ET.fromstring(svg.read_text(encoding="utf-8"))  # well-formed XML
                self.assertTrue(root.get("aria-label"), svg.name)
            # every local image in the README has its dark variant next to it
            for src in re.findall(r'src="(\./[^"]+-light\.svg)"', readme):
                self.assertIn(src.replace("-light.svg", "-dark.svg"), readme)
                self.assertTrue((Path(tmp) / src).exists(), src)

    def test_linked_pictures_stay_on_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme, _ = build_example("keynote-profile", tmp)
            for line in readme.splitlines():
                if "<picture>" in line:
                    self.assertIn("</picture>", line)

    def test_paired_cards_share_a_height(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, assets = build_example("keynote-profile", tmp)
            def h(name):
                return re.search(r'height="(\d+)"', (assets / name).read_text(encoding="utf-8")).group(1)
            self.assertEqual(h("project-echo-light.svg"), h("project-ledgerly-light.svg"))
            self.assertEqual(h("achievement-01-light.svg"), h("achievement-02-light.svg"))

    def test_project_example_keeps_markdown_outside_the_card_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme, _ = build_example("keynote-project", tmp)
            self.assertIn("```bash\nclaude plugin install readme-forge", readme)
            before = readme.split("```bash")[0]
            self.assertEqual(before.count('<div align="center">'), before.count("</div>"))

    def test_placeholders_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "page.json"
            shutil.copy(DESIGN / "templates" / "page" / "profile.json", spec)
            with self.assertRaises(SystemExit) as cm:
                make_page.build(spec, None, None)
            self.assertIn("placeholder", str(cm.exception.code))

    def test_icons_resolve_by_slug_alias_and_title(self):
        self.assertEqual(make_page.resolve_icon("python")[0], "brand")
        self.assertEqual(make_page.resolve_icon("aws")[1]["title"], "Amazon Web Services")
        self.assertEqual(make_page.resolve_icon("Next.js")[1]["title"], "Next.js")
        self.assertEqual(make_page.resolve_icon("email")[0], "line")
        self.assertEqual(make_page.resolve_icon("no-such-tool"), (None, None))
        t = make_page.T("keynote", "light")
        self.assertIn(">No<", make_page.icon("no-such-tool", 0, 0, 30, t, t.surface))

    def test_shipped_examples_hold_no_personal_contact_data(self):
        # Examples and starter specs ship to every user: only fictional/example.com contacts,
        # GitHub's octocat demo account, this repo, and the widget hosts are allowed.
        allowed = ("example.com", "github.com/octocat", "github.com/tanmayai23/README-Editor-skill",
                   "github-readme-stats.vercel.app", "streak-stats.demolab.com", "raw.githubusercontent.com/octocat")
        files = [p for d in ("examples", "templates/page") for p in (DESIGN / d).rglob("*")
                 if p.suffix in (".json", ".md", ".svg")]
        self.assertTrue(files)
        for p in files:
            text = p.read_text(encoding="utf-8")
            for email in re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
                self.assertTrue(email.endswith("@example.com"), f"{p.name}: {email}")
            for url in re.findall(r"https?://[^\s\"'<>)]+", text):
                if url.startswith(("http://www.w3.org/", "https://github.com/{{", "https://{{")) or "{{" in url:
                    continue
                self.assertTrue(any(a in url for a in allowed), f"{p.name}: {url}")

    def test_dark_tokens_keep_text_readable(self):
        for theme in make_page.THEMES:
            for mode in ("light", "dark"):
                t = make_page.T(theme, mode)
                for c in (t.fg, t.body, t.muted):
                    self.assertGreaterEqual(make_page.contrast(c, t.card), 4.5, f"{theme} {mode} {c}")


if __name__ == "__main__":
    unittest.main()
