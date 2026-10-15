"""Unit tests for score_readme.py (resolves issue #28)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "readme-forge" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import score_readme  # noqa: E402


class TestRelativeLinksAndCodeBlocks(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.tmpdir.name)
        # Create a mock repo structure
        (self.repo_dir / ".git").mkdir()
        docs_dir = self.repo_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "my file.md").write_text("# My File\n", encoding="utf-8")
        (docs_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_encoded_and_root_relative_links_and_fenced_links(self):
        """Regression test for issue #28:
        - docs/my%20file.md (encoded relative link)
        - /docs/guide.md (root-relative link)
        - ./docs/not-real.md (inside fenced code block)
        None of these should report 'relative link/image target not found'.
        """
        readme_path = self.repo_dir / "README.md"
        sample = """# Test Project

A test project description for validation.

## Installation
```bash
pip install test-project
```

## Usage
Here are some links:
- [Encoded Link](docs/my%20file.md)
- [Root Relative Link](/docs/guide.md)

Here is a fenced code block with fake links:
```markdown
[Fake Link](./docs/not-real.md)
![Fake Image](./images/fake-image.png)
```

## Features
- Fast and reliable

## License
MIT
"""
        readme_path.write_text(sample, encoding="utf-8")

        rep = score_readme.score_project(sample, readme_path, self.repo_dir)
        link_errors = [
            f["message"] for f in rep.findings
            if f["category"] == "links" and "relative link/image target not found" in f["message"]
        ]
        self.assertEqual(link_errors, [], f"Expected no relative link errors, got: {link_errors}")

    def test_truly_missing_relative_link_still_reported(self):
        """Verify that a genuinely missing relative link is still detected and reported."""
        readme_path = self.repo_dir / "README.md"
        sample = """# Test Project

A test project description for validation.

## Installation
```bash
pip install test-project
```

## Usage
[Missing Link](docs/does_not_exist.md)

## License
MIT
"""
        readme_path.write_text(sample, encoding="utf-8")

        rep = score_readme.score_project(sample, readme_path, self.repo_dir)
        link_errors = [
            f["message"] for f in rep.findings
            if f["category"] == "links" and "relative link/image target not found" in f["message"]
        ]
        self.assertEqual(len(link_errors), 1)
        self.assertIn("docs/does_not_exist.md", link_errors[0])


if __name__ == "__main__":
    unittest.main()
