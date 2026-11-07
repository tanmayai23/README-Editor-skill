"""Files saved with a BOM or as UTF-16 (common on Windows) must read like plain UTF-8 (issue #24).

Fixtures are written byte-for-byte into temp dirs so no editor or git setting can strip the BOM.
"""
import codecs
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "readme-forge" / "scripts"
SCORE = SCRIPTS / "score_readme.py"
sys.path.insert(0, str(SCRIPTS))

import analyze_repo  # noqa: E402

_spec = importlib.util.spec_from_file_location("rf_score_readme_enc", str(SCORE))
score_readme = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(score_readme)

BOM = codecs.BOM_UTF8

PACKAGE_JSON = json.dumps({
    "name": "bom-app", "version": "1.0.0",
    "scripts": {"dev": "vite"},
    "dependencies": {"react": "^18.0.0"},
}, indent=2)

PYPROJECT = """[project]
name = "bom-tool"
version = "0.3.0"
description = "A tool saved by PowerShell 5"
requires-python = ">=3.8"
dependencies = ["click>=8"]
"""

README = """# Title

A small command line tool that converts CSV files into JSON documents.

## Installation

```bash
pip install bom-tool
```

## Usage

```bash
bom-tool convert data.csv
```

## Features

- Reads CSV with any delimiter
- Writes pretty JSON

## Contributing

Open an issue first. See CONTRIBUTING.md.

## License

MIT
"""


class TempRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def write(self, name, data: bytes):
        p = self.tmp / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p


class DecoderTest(unittest.TestCase):
    CASES = [
        ("utf-8 BOM", BOM + "héllo".encode("utf-8"), "héllo"),
        ("utf-16 LE BOM", "héllo".encode("utf-16"), "héllo"),
        ("utf-16 BE BOM", codecs.BOM_UTF16_BE + "héllo".encode("utf-16-be"), "héllo"),
        ("utf-32 LE BOM", codecs.BOM_UTF32_LE + "héllo".encode("utf-32-le"), "héllo"),
        ("utf-32 BE BOM", codecs.BOM_UTF32_BE + "héllo".encode("utf-32-be"), "héllo"),
        ("plain utf-8", "héllo".encode("utf-8"), "héllo"),
        ("latin-1", "héllo".encode("latin-1"), "héllo"),
        ("empty", b"", ""),
    ]

    def test_both_scripts_decode_alike(self):
        for label, data, want in self.CASES:
            with self.subTest(label):
                self.assertEqual(analyze_repo.decode_bytes(data), want)
                self.assertEqual(score_readme.decode_bytes(data), want)

    def test_cut_multibyte_char_at_read_limit_stays_utf8(self):
        # A read limit that splits "é" must not turn the whole file into latin-1 mojibake.
        tmp = Path(tempfile.mkdtemp())
        try:
            p = tmp / "a.txt"
            p.write_bytes("ab é".encode("utf-8"))  # "é" is bytes 3-4
            self.assertEqual(analyze_repo.read_text(p, 4), "ab ")
            self.assertEqual(score_readme.read_text(p, 4), "ab ")
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)


class AnalyzeBomTest(TempRepo):
    def test_package_json_with_bom(self):
        self.write("package.json", BOM + PACKAGE_JSON.encode("utf-8"))
        f = analyze_repo.analyze(self.tmp)
        self.assertEqual(f["package"].get("name"), "bom-app")
        self.assertIn("React", f["frameworks"])
        self.assertIn("dev", f["commands"]["scripts"])

    def test_pyproject_with_bom(self):
        self.write("pyproject.toml", BOM + PYPROJECT.encode("utf-8"))
        f = analyze_repo.analyze(self.tmp)
        self.assertEqual(f["package"].get("name"), "bom-tool")
        self.assertEqual(f["package"].get("version"), "0.3.0")
        self.assertEqual(f["package"].get("requires_python"), ">=3.8")
        self.assertIn("Click (CLI)", f["frameworks"])

    def test_pyproject_with_bom_without_tomllib(self):
        # Python < 3.11 has no tomllib; the fallback parser must also see past the BOM.
        self.write("pyproject.toml", BOM + PYPROJECT.encode("utf-8"))
        with mock.patch.object(analyze_repo, "tomllib", None):
            f = analyze_repo.analyze(self.tmp)
        self.assertEqual(f["package"].get("name"), "bom-tool")
        self.assertEqual(f["package"].get("version"), "0.3.0")

    def test_requirements_txt_in_utf16(self):
        # `pip freeze > requirements.txt` in Windows PowerShell 5.1 writes UTF-16 LE with a BOM and CRLF.
        self.write("requirements.txt", "Django==4.2.7\r\nrequests==2.31.0\r\n".encode("utf-16"))
        f = analyze_repo.analyze(self.tmp)
        self.assertIn("Django", f["frameworks"])
        self.assertEqual(f["dependency_count"], 2)

    def test_setup_cfg_with_bom(self):
        self.write("setup.cfg", BOM + b"[metadata]\nname = cfg-tool\n")
        f = analyze_repo.analyze(self.tmp)
        self.assertEqual(f["package"].get("name"), "cfg-tool")


class ScoreBomTest(TempRepo):
    def score(self, path):
        proc = subprocess.run([sys.executable, str(SCORE), str(path), "--json"],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_readme_with_bom_scores_like_without(self):
        (self.tmp / "CONTRIBUTING.md").write_text("x", encoding="utf-8")
        plain = self.score(self.write("plain/README.md", README.encode("utf-8")))
        bom = self.score(self.write("bom/README.md", BOM + README.encode("utf-8")))
        self.assertNotIn("no title (H1)", [x["message"] for x in bom["findings"]])
        self.assertEqual(bom["score"], plain["score"])
        self.assertGreater(bom["score"], 50)

    def test_utf16_readme_scores_like_utf8(self):
        plain = self.score(self.write("plain/README.md", README.encode("utf-8")))
        wide = self.score(self.write("wide/README.md", README.encode("utf-16")))
        self.assertEqual(wide["score"], plain["score"])


if __name__ == "__main__":
    unittest.main()
