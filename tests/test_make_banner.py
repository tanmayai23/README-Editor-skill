"""Tests for readme-forge-design/scripts/make_banner.py (animated SVG banners). No network."""
import contextlib
import importlib.util
import io
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "readme-forge-design"

_spec = importlib.util.spec_from_file_location("rf_make_banner", str(DESIGN / "scripts" / "make_banner.py"))
make_banner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_banner)

SVG_NS = "{http://www.w3.org/2000/svg}"
CJK_TITLE = "日本語のタイトルがとても長い場合のレイアウト確認用テスト"  # 28 wide characters
LONG_SUB = ("A command line tool that reads your repository, checks every claim in the README "
            "against the code and fails the build when they drift apart")  # 140 characters
SIZES = ((1280, 320), (800, 240), (640, 200))


def run(*argv):
    """Run make_banner.main quietly; returns its exit code."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return make_banner.main([str(a) for a in argv])


def text_spans(svg):
    """(content, left, right) for every text element, using the script's own width estimate."""
    root = ET.fromstring(svg)
    for el in root.iter(SVG_NS + "text"):
        content = "".join(el.itertext())
        if len(content.strip()) <= 2:  # decorations such as the vortex counter ticks and arrows
            continue
        fs = float(el.get("font-size"))
        fam = el.get("font-family", "")
        per = 0.6 if "monospace" in fam else 0.56 if "sans-serif" in fam else 0.70
        w = make_banner.text_em(content, per) * fs + float(el.get("letter-spacing", 0)) * len(content)
        m = re.match(r"translate\(([-\d.]+) [-\d.]+\) scale\(([-\d.]+) 1\)", el.get("transform", ""))
        if m:
            x, w = float(m.group(1)), w * float(m.group(2))
        else:
            x = float(el.get("x"))
        anchor = el.get("text-anchor", "start")
        left = x - w / 2 if anchor == "middle" else x - w if anchor == "end" else x
        yield content, left, left + w


class AccentTests(unittest.TestCase):
    def test_short_hex_accent_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run("--style", "orbit", "--accent", "#FFF", "--title", "x", "--out", tmp), 0)
            self.assertIn("#FFFFFF", (Path(tmp) / "header-dark.svg").read_text(encoding="utf-8"))

    def test_named_colour_is_a_clean_usage_error(self):
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            make_banner.main(["--kind", "button", "--accent", "red", "--title", "x", "--out", tmp])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("--accent must be a hex colour", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_other_bad_accents_are_rejected(self):
        for bad in ("FF8A3D", "#FF8A3", "#GGG", "#FF8A3D00", "", "rgb(1,2,3)"):
            with self.subTest(accent=bad), self.assertRaises(SystemExit) as cm:
                run("--accent", bad, "--title", "x", "--out", "unused")
            self.assertEqual(cm.exception.code, 2)

    def test_parse_hex_expands_and_normalises(self):
        self.assertEqual(make_banner.parse_hex("#fff"), "#FFFFFF")
        self.assertEqual(make_banner.parse_hex("#0ea5e9"), "#0EA5E9")
        self.assertIsNone(make_banner.parse_hex("red"))

    def test_colour_helpers_accept_both_forms(self):
        self.assertEqual(make_banner.shade("#000", 0.5), make_banner.shade("#000000", 0.5))
        self.assertEqual(make_banner._lum("#FFF"), make_banner._lum("#FFFFFF"))
        self.assertEqual(make_banner.mix("#000", "#FFF", 0), "#000000")


class TextFitTests(unittest.TestCase):
    def test_wide_characters_and_emoji_count_as_one_em(self):
        self.assertEqual(make_banner.text_em("abcd", 0.5), 2.0)
        self.assertEqual(make_banner.text_em("日本語", 0.5), 3.0)
        self.assertEqual(make_banner.text_em("ＡＢ", 0.5), 2.0)  # fullwidth
        self.assertEqual(make_banner.text_em("🚀", 0.5), 1.0)
        self.assertEqual(make_banner.text_em("👍🏽", 0.5), 1.0)  # skin-tone modifier adds nothing
        self.assertEqual(make_banner.text_em("é", 0.5), 0.5)  # combining accent adds nothing

    def test_cjk_title_size_fits_the_canvas(self):
        ts = make_banner.title_size("日本語" * 8, 1280, 320, 72)
        self.assertLessEqual(24 * ts, 1280 * 0.8)

    def test_long_subtitle_shrinks_then_wraps_then_ends_in_an_ellipsis(self):
        size, lines = make_banner.fit_text(LONG_SUB, 1100, 24, 14, 0.56, max_lines=2)
        self.assertEqual((size, lines), (14, [LONG_SUB]))  # shrinks onto one line
        size, lines = make_banner.fit_text(LONG_SUB, 600, 24, 14, 0.56, max_lines=2)
        self.assertEqual(size, 14)
        self.assertEqual(" ".join(lines), LONG_SUB)  # wraps at a space, nothing lost
        size, lines = make_banner.fit_text(LONG_SUB, 400, 24, 14, 0.56, max_lines=2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[-1].endswith("…"))
        for width in (1100, 600, 400):
            size, lines = make_banner.fit_text(LONG_SUB, width, 24, 14, 0.56, max_lines=2)
            for line in lines:
                self.assertLessEqual(make_banner.text_em(line, 0.56) * size, width)

    def test_cjk_text_wraps_between_characters(self):
        lines = make_banner.wrap("日本語" * 10, 12, 0.56, max_lines=3)
        self.assertEqual("".join(lines), "日本語" * 10)
        self.assertEqual([len(ln) for ln in lines], [12, 12, 6])

    def test_short_text_is_untouched(self):
        self.assertEqual(make_banner.fit_text("short", 600, 24, 14, 0.56), (24, ["short"]))

    def test_cjk_and_long_subtitles_stay_inside_every_banner(self):
        styles = sorted(make_banner.STYLES)
        cases = [("header", s, w, h) for s in styles for w, h in SIZES]
        cases += [("footer", s, w, None) for s in styles for w, _ in SIZES]
        with tempfile.TemporaryDirectory() as tmp:
            for kind, style, w, h in cases:
                for title, sub in ((CJK_TITLE, LONG_SUB), ("readme-forge", CJK_TITLE * 3)):
                    argv = ["--kind", kind, "--style", style, "--width", w, "--title", title, "--subtitle", sub,
                            "--tag", "新しい · New release", "--theme", "dark", "--out", tmp, "--name", "b"]
                    if h:
                        argv += ["--height", h]
                    self.assertEqual(run(*argv), 0)
                    svg = (Path(tmp) / "b-dark.svg").read_text(encoding="utf-8")
                    for content, left, right in text_spans(svg):
                        with self.subTest(kind=kind, style=style, width=w, text=content[:20]):
                            self.assertGreaterEqual(left, -1)
                            self.assertLessEqual(right, w + 1)

    def test_buttons_grow_to_fit_wide_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("--kind", "button", "--title", "今すぐ始める", "--out", tmp, "--theme", "dark")
            svg = (Path(tmp) / "button-dark.svg").read_text(encoding="utf-8")
            w = float(ET.fromstring(svg).get("width"))
            for _, left, right in text_spans(svg):
                self.assertGreaterEqual(left, 0)
                self.assertLessEqual(right, w)


SMIL = re.compile(r"<(animate|animateMotion|animateTransform|animateColor|set)\b")
REDUCE = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def every_output(tmp):
    """(label, svg) for every kind and style, both themes, with a tag (spotlight's pill) and a logo."""
    logo = ROOT / ".github" / "assets" / "logo-320.png"
    jobs = [("header", s, ["--tag", "New"]) for s in make_banner.STYLES]
    jobs += [("header", s, ["--logo", logo]) for s in make_banner.STYLES]
    jobs += [("footer", s, []) for s in make_banner.STYLES]
    jobs += [("divider", s, []) for s in make_banner.STYLES]
    jobs += [("button", "aurora", ["--variant", v]) for v in ("primary", "secondary")]
    for i, (kind, style, extra) in enumerate(jobs):
        name = f"b{i}"
        run("--kind", kind, "--style", style, "--title", "readme-forge", "--subtitle", "Banners", *extra,
            "--out", tmp, "--name", name)
        for theme in ("dark", "light"):
            yield f"{kind}/{style}/{theme}{extra[:1]}", (Path(tmp) / f"{name}-{theme}.svg").read_text(encoding="utf-8")


class MotionTests(unittest.TestCase):
    def test_no_smil_in_any_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = list(every_output(tmp))
        self.assertGreater(len(outputs), 150)
        for label, svg in outputs:
            with self.subTest(label):
                self.assertIsNone(SMIL.search(svg))
                ET.fromstring(svg)  # well-formed

    def test_every_animation_is_stopped_by_reduced_motion(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label, svg in every_output(tmp):
                if "animation:" in svg:
                    with self.subTest(label):
                        self.assertIn(REDUCE, svg)

    def test_static_banners_have_no_animation(self):
        with tempfile.TemporaryDirectory() as tmp:
            for style in make_banner.STYLES:
                run("--style", style, "--title", "x", "--tag", "New", "--static", "--theme", "dark", "--out", tmp)
                svg = (Path(tmp) / "header-dark.svg").read_text(encoding="utf-8")
                with self.subTest(style):
                    self.assertNotIn("@keyframes", svg)
                    self.assertIsNone(SMIL.search(svg))

    def test_terminal_title_is_never_erased_without_animation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("--style", "terminal", "--title", "my-cli", "--theme", "dark", "--out", tmp)
            svg = (Path(tmp) / "header-dark.svg").read_text(encoding="utf-8")
            self.assertNotIn("clip-path", svg)
            # the cover that "erases" the title rests at zero width; only the CSS animation widens it
            cover = re.search(r'<rect class="erase"[^>]*>', svg).group(0)
            self.assertIn('transform="scale(0 1)"', cover)
            self.assertIn(REDUCE, svg)
            run("--style", "terminal", "--title", "my-cli", "--theme", "dark", "--static", "--out", tmp)
            self.assertNotIn('class="erase"', (Path(tmp) / "header-dark.svg").read_text(encoding="utf-8"))

    def test_committed_gallery_is_current_and_smil_free(self):
        committed = DESIGN / "assets" / "banners"
        with tempfile.TemporaryDirectory() as tmp:
            run("--gallery", tmp)
            fresh = sorted(p.name for p in Path(tmp).iterdir())
            for name in fresh:
                with self.subTest(name):
                    self.assertTrue((committed / name).exists())
                    text = (committed / name).read_text(encoding="utf-8")
                    self.assertEqual(text, (Path(tmp) / name).read_text(encoding="utf-8"),
                                     "regenerate with: python readme-forge-design/scripts/make_banner.py --gallery readme-forge-design/assets/banners")
                    self.assertIsNone(SMIL.search(text))


if __name__ == "__main__":
    unittest.main()
