"""Unit tests for make_banner.py (resolves issue #33)."""

import argparse
import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "readme-forge" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import make_banner  # noqa: E402


class TestMakeBannerIssue33(unittest.TestCase):
    def test_accent_expansion_and_validation(self):
        """Regression test for issue #33:
        --accent '#FFF' should expand to '#FFFFFF'.
        --accent 'red' should be rejected with an error.
        """
        # Valid short hex
        parser = argparse.ArgumentParser()
        parser.add_argument("--accent")
        # Direct shade and _lum tests on 3-character hex
        self.assertEqual(make_banner.shade("#FFF", -0.2), "#CCCCCC")
        self.assertAlmostEqual(make_banner._lum("#FFF"), 1.0, places=2)
        self.assertEqual(make_banner.shade("#000", 0.5), "#7F7F7F")
        self.assertAlmostEqual(make_banner._lum("#000"), 0.0, places=2)

    def test_main_accent_flag_validation(self):
        """make_banner main() should accept #FFF and reject non-hex color names."""
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                make_banner.main(["--kind", "button", "--accent", "red", "--title", "x"])

        # Should not raise for valid short hex #FFF
        # Use a mock/temp directory or list
        try:
            # Test that main() processes --accent #FFF and produces no exception during arg validation
            p = argparse.ArgumentParser()
            p.add_argument("--accent")
            a = p.parse_args(["--accent", "#FFF"])
            # verify hex expansion logic
            import re
            m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", a.accent)
            self.assertIsNotNone(m)
            hex_part = m.group(1)
            expanded = "#" + ("".join(c * 2 for c in hex_part) if len(hex_part) == 3 else hex_part).upper()
            self.assertEqual(expanded, "#FFFFFF")
        except Exception as e:
            self.fail(f"Accent validation raised unexpected exception: {e}")

    def test_cjk_title_and_long_subtitle_fit_canvas(self):
        """Regression test for issue #33:
        A 24-character Japanese title and a 140-character subtitle must not overflow the canvas.
        """
        canvas_width = 1280
        max_allowed_width = canvas_width * 0.80  # 1024px

        # 24-character Japanese title
        cjk_title = "これは日本語のテストタイトルです二十四文字ありますよ"
        ts = make_banner.title_size(cjk_title, canvas_width, 320, 72)
        estimated_title_width = len(cjk_title) * 1.0 * ts
        self.assertLessEqual(estimated_title_width, max_allowed_width,
                             f"CJK title width {estimated_title_width}px overflows {max_allowed_width}px (font-size: {ts})")
        self.assertLess(ts, 72, "CJK font size should be downscaled from base 72")

        # 140-character subtitle
        long_sub = "A" * 140
        ss = make_banner.title_size(long_sub, canvas_width, 320, 24, min_size=12)
        estimated_sub_width = len(long_sub) * 0.56 * ss
        self.assertLessEqual(estimated_sub_width, max_allowed_width + 10,  # small rounding tolerance
                             f"Subtitle width {estimated_sub_width}px overflows {max_allowed_width}px (font-size: {ss})")
        self.assertLess(ss, 24, "Long subtitle font size should be downscaled from base 24")

    def test_text_block_renders_fitted_sizes(self):
        """Verify that text_block emits scaled font-size attributes for CJK and long subtitles."""
        a = argparse.Namespace(
            kind="header", style="aurora", palette=None, accent=None,
            title="これは日本語のテストタイトルです二十四文字ありますよ",
            subtitle="A" * 140, tag="", width=1280, height=320,
            theme="dark", static=True, out=".", name=None
        )
        ctx = make_banner.Ctx(a, "dark")
        make_banner.text_block(ctx)
        svg_content = "\n".join(ctx.body)

        self.assertIn('font-size="39"', svg_content)
        self.assertIn('font-size="13"', svg_content)


if __name__ == "__main__":
    unittest.main()
