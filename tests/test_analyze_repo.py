"""Unit tests for analyze_repo.py (resolves issue #34)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "readme-forge" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import analyze_repo  # noqa: E402


class TestAnalyzeRepoIssue34(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.tmpdir.name)
        (self.repo_dir / ".git").mkdir()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_env_vars_scanned_in_non_test_files_with_test_in_name(self):
        """Regression test for issue #34:
        Files like latest.py and contest.py should NOT be skipped when extracting env vars,
        while actual test files like test_foo.py should be skipped.
        """
        latest_file = self.repo_dir / "latest.py"
        latest_file.write_text("import os\ntoken = os.environ['API_TOKEN']\n", encoding="utf-8")

        contest_file = self.repo_dir / "contest.py"
        contest_file.write_text("import os\ndb = os.getenv('CONTEST_DB_URL')\n", encoding="utf-8")

        test_file = self.repo_dir / "test_runner.py"
        test_file.write_text("import os\nval = os.environ['IGNORED_TEST_VAR']\n", encoding="utf-8")

        facts = analyze_repo.analyze(self.repo_dir)
        env_vars = facts.get("env_vars", {})

        self.assertIn("API_TOKEN", env_vars)
        self.assertIn("CONTEST_DB_URL", env_vars)
        self.assertNotIn("IGNORED_TEST_VAR", env_vars)

    def test_file_size_handles_missing_file_and_dangling_symlink(self):
        """file_size() should return 0 without throwing an exception for nonexistent files or broken symlinks."""
        missing = self.repo_dir / "does_not_exist.bin"
        self.assertEqual(analyze_repo.file_size(missing), 0)

        # Attempt to create a dangling symlink if OS supports it
        symlink_path = self.repo_dir / "broken_link.safetensors"
        try:
            symlink_path.symlink_to(missing)
            self.assertEqual(analyze_repo.file_size(symlink_path), 0)
            # analyze() should also run without raising FileNotFoundError
            facts = analyze_repo.analyze(self.repo_dir)
            self.assertIsInstance(facts, dict)
        except (OSError, NotImplementedError):
            # Windows without Developer Mode or unprivileged user cannot create symlinks
            pass


if __name__ == "__main__":
    unittest.main()
