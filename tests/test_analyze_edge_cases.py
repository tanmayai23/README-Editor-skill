"""analyze_repo edge cases from issue #34: dangling weights symlinks and test-like file names."""
import os
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


class TempRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def write(self, name, text="x\n"):
        p = self.tmp / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p


class DanglingWeightsSymlinkTest(TempRepo):
    def setUp(self):
        super().setUp()
        (self.tmp / "sl").mkdir()
        self.write("sl/real.safetensors", "weights")
        try:
            os.symlink(str(self.tmp / "blobs" / "missing-blob"), str(self.tmp / "sl" / "model.safetensors"))
        except (OSError, NotImplementedError, AttributeError) as e:
            self.skipTest(f"cannot create symlinks here: {e}")

    def check(self, f):
        self.assertEqual(f["huggingface"]["weights"], ["sl/real.safetensors"])

    def test_without_git(self):
        with mock.patch.object(analyze_repo, "git_files", return_value=None):
            self.check(analyze_repo.analyze(self.tmp))

    @unittest.skipIf(shutil.which("git") is None, "git is not installed")
    def test_with_git(self):
        if subprocess.run(["git", "init", "-q", str(self.tmp)], capture_output=True).returncode != 0:
            self.skipTest("git init failed")
        self.check(analyze_repo.analyze(self.tmp))

    def test_file_size_of_dangling_link_is_zero(self):
        self.assertEqual(analyze_repo.file_size(self.tmp / "sl" / "model.safetensors"), 0)


class TestLikeNamesTest(TempRepo):
    def test_env_vars_read_from_files_whose_name_contains_test(self):
        self.write("latest.py", "import os\nTOKEN = os.environ['API_TOKEN']\n")
        self.write("contest.py", "import os\nos.getenv('CONTEST_KEY')\n")
        self.write("attestation.ts", "export const k = process.env.ATTEST_KEY;\n")
        env = analyze_repo.analyze(self.tmp)["env_vars"]
        for var, src in (("API_TOKEN", "latest.py"), ("CONTEST_KEY", "contest.py"), ("ATTEST_KEY", "attestation.ts")):
            self.assertEqual(env.get(var), {"source": src})

    def test_real_test_files_are_still_skipped(self):
        self.write("test_app.py", "import os\nos.environ['FROM_PY_TEST']\n")
        self.write("server_test.go", 'package main\nimport "os"\nvar _ = os.Getenv("FROM_GO_TEST")\n')
        self.write("app.test.ts", "process.env.FROM_JS_TEST;\n")
        self.write("app.spec.js", "process.env.FROM_JS_SPEC;\n")
        env = analyze_repo.analyze(self.tmp)["env_vars"]
        for var in ("FROM_PY_TEST", "FROM_GO_TEST", "FROM_JS_TEST", "FROM_JS_SPEC"):
            self.assertNotIn(var, env)


if __name__ == "__main__":
    unittest.main()
