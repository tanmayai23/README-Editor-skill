"""Tests for readme-forge/scripts/learn.py (the preference learner)."""
import contextlib
import importlib.util
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "readme-forge" / "scripts" / "learn.py"

_spec = importlib.util.spec_from_file_location("rf_learn", str(SCRIPT))
ln = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ln)

GENERATED = """# App

<img alt="banner" src=".github/assets/header-dark.svg">

## 🚀 Features

Does things.

## Quickstart

```bash
## not a heading
npm install
```

## FAQ

Questions.

## Roadmap

Plans.
"""

EDITED = """# App

<img alt="banner" src=".github/assets/header-dark.svg">

## Features

Does things.

## Quickstart

```bash
npm install
```

## Examples

See examples.
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        self.old_home = os.environ.get("READMEFORGE_HOME")
        os.environ["READMEFORGE_HOME"] = str(tmp / "home")
        os.environ.pop("READMEFORGE_LEARN", None)
        self.addCleanup(self.restore)
        self.proj = tmp / "proj"
        (self.proj / ".github" / "assets").mkdir(parents=True)
        self.readme = self.proj / "README.md"
        self.readme.write_text(GENERATED, encoding="utf-8")
        self.banner = self.proj / ".github" / "assets" / "header-dark.svg"
        self.banner.write_text("<svg>beam</svg>", encoding="utf-8")

    def restore(self):
        if self.old_home is None:
            os.environ.pop("READMEFORGE_HOME", None)
        else:
            os.environ["READMEFORGE_HOME"] = self.old_home

    def run_main(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ln.main([str(a) for a in args])
        return code, buf.getvalue()

    def snapshot(self, *extra):
        return self.run_main("snapshot", self.readme, "--context", "mode=project,kind=cli",
                             "--choice", "banner.style=beam@file:.github/assets/header-dark.svg",
                             "--choice", "length=standard", *extra)

    def suggest(self, *args):
        code, out = self.run_main("suggest", "--json", "--seed", "1", *args)
        self.assertEqual(code, 0)
        return json.loads(out)


class ReadmeParsing(Base):
    def test_sections_skip_code_fences_and_emoji(self):
        self.assertEqual(sorted(ln.sections(GENERATED)), ["faq", "features", "quickstart", "roadmap"])

    def test_emoji_headings(self):
        self.assertTrue(ln.emoji_headings(GENERATED))
        self.assertFalse(ln.emoji_headings(EDITED))

    def test_slug_strips_markup(self):
        self.assertEqual(ln.slug("[Getting **started**](#x) `now`"), "getting-started-now")

    def test_parse_choice(self):
        self.assertEqual(ln.parse_choice("banner.style=beam@file:a.svg"),
                         {"decision": "banner.style", "option": "beam", "marker": "file:a.svg"})
        self.assertIsNone(ln.parse_choice("length=concise")["marker"])


class Bandit(Base):
    def test_no_evidence_keeps_the_default(self):
        d = self.suggest("--decision", "banner.style:beam,aurora,prism")["decisions"][0]
        self.assertEqual(d["pick"], "beam")
        self.assertFalse(d["confident"])
        self.assertEqual({r["mean"] for r in d["ranking"]}, {0.5})

    def test_rewards_move_the_ranking(self):
        data = ln.load()
        for _ in range(4):
            ln.update(data, "banner.style", "aurora", 1, {"kind": "cli"}, "test")
            ln.update(data, "banner.style", "beam", 0, {"kind": "cli"}, "test")
        r = ln.rank(data, "banner.style", ["beam", "aurora"], {"kind": "cli"}, random.Random(0))
        self.assertEqual(r["ranking"][0]["option"], "aurora")
        self.assertTrue(r["confident"])
        picks = [ln.rank(data, "banner.style", ["beam", "aurora"], {"kind": "cli"}, random.Random(i))["pick"]
                 for i in range(50)]
        self.assertGreater(picks.count("aurora"), 40)

    def test_context_specific_evidence_wins(self):
        data = ln.load()
        for _ in range(3):
            ln.update(data, "banner.style", "terminal", 1, {"kind": "cli"}, "test")
            ln.update(data, "banner.style", "terminal", 0, {"kind": "webapp"}, "test")
        cli = ln.posterior(data, "banner.style", "terminal", {"kind": "cli"})
        web = ln.posterior(data, "banner.style", "terminal", {"kind": "webapp"})
        self.assertGreater(cli[0] / sum(cli), 0.6)
        self.assertLess(web[0] / sum(web), 0.4)

    def test_decay_lets_tastes_change(self):
        data = ln.load()
        for _ in range(5):
            ln.update(data, "length", "detailed", 1, {}, "test")
        for _ in range(5):
            ln.update(data, "length", "detailed", 0, {}, "test")
        a, b = ln.posterior(data, "length", "detailed", {})
        self.assertLess(a / (a + b), 0.5)


class LearningFromEdits(Base):
    def test_unchanged_readme_waits(self):
        self.snapshot()
        code, out = self.run_main("observe", self.readme)
        self.assertIn("no edits", out)
        self.assertTrue(ln.snapshot_path(self.readme).exists())

    def test_edits_become_rewards(self):
        self.snapshot()
        self.readme.write_text(EDITED, encoding="utf-8")
        self.banner.write_text("<svg>aurora</svg>", encoding="utf-8")
        code, out = self.run_main("observe", self.readme, "--json")
        self.assertEqual(code, 0)
        got = {(r["decision"], r["option"]): r["reward"] for r in json.loads(out)}
        self.assertEqual(got[("banner.style", "beam")], 0.0)
        self.assertEqual(got[("section:faq", "keep")], 0.0)
        self.assertEqual(got[("section:roadmap", "keep")], 0.0)
        self.assertEqual(got[("section:features", "keep")], 1.0)
        self.assertEqual(got[("section:examples", "keep")], 1.0)
        self.assertEqual(got[("length", "standard")], 0.0)
        self.assertEqual(got[("length", "concise")], 1.0)
        self.assertEqual(got[("headings.emoji", "no")], 1.0)
        self.assertFalse(ln.snapshot_path(self.readme).exists())

    def test_kept_asset_is_a_positive_reward(self):
        self.snapshot()
        code, out = self.run_main("observe", self.readme, "--accepted", "--json")
        got = {(r["decision"], r["option"]): r["reward"] for r in json.loads(out)}
        self.assertEqual(got[("banner.style", "beam")], 1.0)
        self.assertEqual(got[("length", "standard")], 1.0)

    def test_stale_snapshot_counts_as_accepted(self):
        self.snapshot()
        p = ln.snapshot_path(self.readme)
        snap = json.loads(p.read_text(encoding="utf-8"))
        snap["created"] = time.time() - (ln.STALE_DAYS + 1) * 86400
        p.write_text(json.dumps(snap), encoding="utf-8")
        code, out = self.run_main("observe", self.readme)
        self.assertIn("learned", out)

    def test_section_deleted_twice_is_omitted(self):
        for _ in range(2):
            self.readme.write_text(GENERATED, encoding="utf-8")
            self.snapshot()
            self.readme.write_text(EDITED, encoding="utf-8")
            self.run_main("observe", self.readme)
        rows = {s["section"]: s for s in self.suggest("--context", "mode=project,kind=cli",
                                                       "--sections", "FAQ,Features")["sections"]}
        self.assertEqual(rows["faq"]["advice"], "omit")
        self.assertEqual(rows["features"]["advice"], "include")

    def test_learning_follows_the_user_to_a_new_project_of_the_same_kind(self):
        self.snapshot()
        self.readme.write_text(EDITED, encoding="utf-8")
        self.banner.write_text("<svg>aurora</svg>", encoding="utf-8")
        self.run_main("observe", self.readme)
        d = self.suggest("--context", "mode=project,kind=cli", "--decision", "banner.style:beam,aurora")["decisions"][0]
        self.assertEqual(d["ranking"][0]["option"], "aurora")


class Controls(Base):
    def test_preferences_round_trip(self):
        self.run_main("prefer", "never use emoji in headings")
        self.run_main("prefer", "never use emoji in headings")
        self.assertEqual(self.suggest()["preferences"], ["never use emoji in headings"])
        self.run_main("prefer", "--remove", "1")
        self.assertEqual(self.suggest()["preferences"], [])

    def test_off_switch(self):
        self.run_main("off")
        code, out = self.snapshot()
        self.assertIn("learning is off", out)
        self.assertFalse(ln.snapshot_path(self.readme).exists())
        self.assertFalse(self.suggest()["learning"])
        self.run_main("on")
        self.assertTrue(self.suggest()["learning"])

    def test_env_off_switch(self):
        os.environ["READMEFORGE_LEARN"] = "0"
        self.addCleanup(os.environ.pop, "READMEFORGE_LEARN", None)
        code, out = self.run_main("reward", "length=concise", "--value", "1")
        self.assertIn("learning is off", out)
        self.assertEqual(ln.load()["decisions"], {})

    def test_reset_forgets_everything(self):
        self.run_main("reward", "length=concise", "--value", "1")
        self.run_main("prefer", "short READMEs")
        self.snapshot()
        self.run_main("reset")
        data = ln.load()
        self.assertEqual((data["decisions"], data["preferences"]), ({}, []))
        self.assertFalse(ln.snapshot_path(self.readme).exists())

    def test_store_holds_no_readme_text(self):
        self.snapshot()
        self.readme.write_text(EDITED, encoding="utf-8")
        self.run_main("observe", self.readme)
        stored = ln.store_path().read_text(encoding="utf-8")
        self.assertNotIn("Does things", stored)
        self.assertNotIn("npm install", stored)

    def test_cli_runs(self):
        env = dict(os.environ)
        proc = subprocess.run([sys.executable, str(SCRIPT), "show"], capture_output=True, text=True,
                              encoding="utf-8", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nothing learned yet", proc.stdout)


if __name__ == "__main__":
    unittest.main()
