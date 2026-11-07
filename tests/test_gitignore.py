"""analyze_repo must skip .gitignore'd files (issue #26).

Repro: a Flask app plus a 2000-line generated TypeScript client that .gitignore excludes.
The generated code used to make the repo "TypeScript (99.9%)" and leak its env vars.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "readme-forge" / "scripts"))

import analyze_repo  # noqa: E402

APP = '''import os
from flask import Flask

app = Flask(__name__)
KEY = os.environ["REAL_KEY"]


@app.get("/health")
def health():
    return "ok"
'''


def generated_client(lines=2000):
    out = ["// generated: do not edit"]
    for i in range(3):
        out.append(f"export const s{i} = process.env.GEN_SECRET_{i};")
    out.append('router.get("/generated-route", handler);')
    out += [f"export const v{i} = {i};" for i in range(lines - len(out))]
    return "\n".join(out) + "\n"


class GitignoreRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.write("app.py", APP)
        self.write("requirements.txt", "flask\n")
        self.write(".gitignore", "# build output\ngenerated/\n")
        self.write("generated/client.ts", generated_client())
        self.write("generated/tests/test_client.py", "def test_x():\n    assert True\n")

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def write(self, name, text):
        p = self.tmp / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def assert_generated_ignored(self, f):
        self.assertEqual(f["primary_language"], "Python")
        self.assertNotIn("TypeScript", [l["name"] for l in f["languages"]])
        self.assertEqual(set(f["env_vars"]), {"REAL_KEY"})
        self.assertEqual({r["path"] for r in f["http_routes"]}, {"/health"})
        self.assertNotIn("generated", f["tests"])


class WithoutGitTest(GitignoreRepo):
    """No git on PATH (or not a work tree): the root .gitignore is parsed."""

    def analyze(self):
        with mock.patch.object(analyze_repo, "git_files", return_value=None):
            return analyze_repo.analyze(self.tmp)

    def test_ignored_dir_contributes_nothing(self):
        self.assert_generated_ignored(self.analyze())

    def test_without_gitignore_the_generated_code_counts(self):
        # Control: proves the fixture really does skew the facts when nothing ignores it.
        (self.tmp / ".gitignore").unlink()
        f = self.analyze()
        self.assertEqual(f["primary_language"], "TypeScript")
        self.assertIn("GEN_SECRET_0", f["env_vars"])

    def test_glob_anchored_and_negated_patterns(self):
        self.write(".gitignore", "*.gen.py\n!keep.gen.py\n/top_only.py\n**/cache/\nout/**\n")
        self.write("a.gen.py", "import os\nos.environ['GLOB_HIT']\n")
        self.write("keep.gen.py", "import os\nos.environ['NEGATED_KEEP']\n")
        self.write("top_only.py", "import os\nos.environ['ANCHORED_HIT']\n")
        self.write("pkg/top_only.py", "import os\nos.environ['ANCHORED_MISS']\n")
        self.write("pkg/cache/x.py", "import os\nos.environ['DEEP_DIR_HIT']\n")
        self.write("out/y.py", "import os\nos.environ['DOUBLESTAR_HIT']\n")
        env = set(self.analyze()["env_vars"])
        self.assertIn("NEGATED_KEEP", env)
        self.assertIn("ANCHORED_MISS", env)
        for gone in ("GLOB_HIT", "ANCHORED_HIT", "DEEP_DIR_HIT", "DOUBLESTAR_HIT"):
            self.assertNotIn(gone, env)

    def test_ignore_dirs_still_skipped(self):
        self.write("node_modules/lib/index.js", "process.env.FROM_NODE_MODULES\n")
        self.assertNotIn("FROM_NODE_MODULES", self.analyze()["env_vars"])

    def test_file_cap_still_applies(self):
        with mock.patch.object(analyze_repo, "MAX_FILES", 2), \
                mock.patch.object(analyze_repo, "git_files", return_value=None):
            self.assertEqual(len(list(analyze_repo.walk(self.tmp))), 2)


@unittest.skipIf(shutil.which("git") is None, "git is not installed")
class WithGitTest(GitignoreRepo):
    """In a git work tree, git decides: nested .gitignore files and untracked files included."""

    def setUp(self):
        super().setUp()
        res = subprocess.run(["git", "init", "-q", str(self.tmp)], capture_output=True)
        if res.returncode != 0:
            self.skipTest("git init failed: " + res.stderr.decode(errors="replace"))

    def test_uses_git_listing(self):
        self.assertIsNotNone(analyze_repo.git_files(self.tmp))

    def test_ignored_dir_contributes_nothing(self):
        self.assert_generated_ignored(analyze_repo.analyze(self.tmp))

    def test_nested_gitignore_is_respected(self):
        # Only git knows about .gitignore files below the root.
        self.write("src/.gitignore", "secret_gen.py\n")
        self.write("src/secret_gen.py", "import os\nos.environ['NESTED_IGNORED']\n")
        self.write("src/real.py", "import os\nos.environ['NESTED_KEPT']\n")
        env = set(analyze_repo.analyze(self.tmp)["env_vars"])
        self.assertIn("NESTED_KEPT", env)
        self.assertNotIn("NESTED_IGNORED", env)

    def test_ignore_dirs_still_skipped(self):
        self.write("node_modules/lib/index.js", "process.env.FROM_NODE_MODULES\n")
        self.write("examples/demo.py", "import os\nos.environ['FROM_EXAMPLES']\n")
        env = analyze_repo.analyze(self.tmp)["env_vars"]
        self.assertNotIn("FROM_NODE_MODULES", env)
        self.assertNotIn("FROM_EXAMPLES", env)

    def test_file_cap_still_applies(self):
        with mock.patch.object(analyze_repo, "MAX_FILES", 2):
            self.assertEqual(len(list(analyze_repo.walk(self.tmp))), 2)


class NotAWorkTreeTest(unittest.TestCase):
    def test_git_files_is_none_outside_a_repo(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            if subprocess.run(["git", "-C", str(tmp), "rev-parse"], capture_output=True).returncode == 0:
                self.skipTest("temp dir is inside a git work tree")
            self.assertIsNone(analyze_repo.git_files(tmp))
        except FileNotFoundError:
            self.assertIsNone(analyze_repo.git_files(tmp))  # no git at all
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
