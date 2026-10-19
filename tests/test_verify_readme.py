"""Tests for readme-forge/scripts/verify_readme.py (the claim checker)."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "readme-forge" / "scripts" / "verify_readme.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "verify"
NODE = FIXTURES / "node-app"
PY = FIXTURES / "py-cli"

_spec = importlib.util.spec_from_file_location("rf_verify_readme", str(SCRIPT))
vr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vr)

_cache = {}


def report(repo, name):
    key = (repo, name)
    if key not in _cache:
        _cache[key] = vr.verify(repo / name, repo)
    return _cache[key]


def claim(rep, kind, text):
    for c in rep["claims"]:
        if c["kind"] == kind and c["text"] == text:
            return c
    raise AssertionError(f"no {kind} claim {text!r}; claims: {[(c['kind'], c['text']) for c in rep['claims']]}")


def run_cli(*args):
    proc = subprocess.run([sys.executable, str(SCRIPT)] + [str(a) for a in args],
                          capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


class NodeAppGood(unittest.TestCase):
    def setUp(self):
        self.rep = report(NODE, "README.good.md")

    def test_summary_is_perfect(self):
        s = self.rep["summary"]
        self.assertEqual(s["not_found"], 0, [c for c in self.rep["claims"] if c["status"] == "not_found"])
        self.assertEqual(s["accuracy"], 100.0)
        self.assertEqual(s["checked"], s["verified"] + s["not_found"])
        self.assertGreaterEqual(s["verified"], 10)

    def test_seeded_true_claims(self):
        for kind, text in [("command", "pnpm install"), ("package_manager", "pnpm"), ("script", "pnpm dev"),
                           ("script", "pnpm test"), ("script", "pnpm run dev"), ("command", "cp .env.example .env"),
                           ("command", "docker compose up -d api db"), ("env_var", "DATABASE_URL"),
                           ("env_var", "STRIPE_KEY"), ("env_var", "PORT"), ("path", "src/index.js"),
                           ("command", "cd node-app")]:
            self.assertEqual(claim(self.rep, kind, text)["status"], "verified", (kind, text))

    def test_generic_commands_excluded(self):
        for text in ("git status", "cd ..", "node --version", "curl http://localhost:3000/health"):
            self.assertEqual(claim(self.rep, "command", text)["status"], "generic", text)
        s = self.rep["summary"]
        self.assertGreaterEqual(s["generic"], 4)
        self.assertEqual(s["checked"], s["verified"])  # generic claims never enter accuracy

    def test_console_output_tree_and_comments_ignored(self):
        texts = {c["text"] for c in self.rep["claims"]}
        self.assertNotIn("listening on http://localhost:3000", texts)
        self.assertFalse(any("index.js    #" in t or t.startswith(("src/", "└")) and t != "src/index.js" for t in texts))
        self.assertFalse(any("TODO" in t for t in texts))

    def test_line_numbers_point_at_the_readme(self):
        lines = (NODE / "README.good.md").read_text(encoding="utf-8").splitlines()
        c = claim(self.rep, "script", "pnpm dev")
        self.assertEqual(lines[c["line"] - 1].strip(), "pnpm dev")
        c = claim(self.rep, "env_var", "STRIPE_KEY")
        self.assertIn("STRIPE_KEY", lines[c["line"] - 1])


class NodeAppBad(unittest.TestCase):
    def setUp(self):
        self.rep = report(NODE, "README.bad.md")

    def test_every_seeded_error_is_caught(self):
        for kind, text in [("package_manager", "npm"), ("script", "pnpm run deploy"), ("env_var", "REDIS_URL"),
                           ("path", "docs/setup.md"), ("command", "docker compose up worker")]:
            self.assertEqual(claim(self.rep, kind, text)["status"], "not_found", (kind, text))

    def test_evidence_explains_the_miss(self):
        self.assertIn("pnpm", claim(self.rep, "package_manager", "npm")["evidence"])
        self.assertIn("api, db", claim(self.rep, "command", "docker compose up worker")["evidence"])
        self.assertIn("dev, test", claim(self.rep, "script", "pnpm run deploy")["evidence"])

    def test_package_json_still_counts_for_npm_install(self):
        self.assertEqual(claim(self.rep, "command", "npm install")["status"], "verified")

    def test_accuracy(self):
        s = self.rep["summary"]
        self.assertEqual(s["not_found"], 5)
        self.assertEqual(s["accuracy"], round(100 * s["verified"] / s["checked"], 1))
        self.assertLess(s["accuracy"], 50)


class PyCliGood(unittest.TestCase):
    def setUp(self):
        self.rep = report(PY, "README.good.md")

    def test_summary_is_perfect(self):
        s = self.rep["summary"]
        self.assertEqual(s["not_found"], 0, [c for c in self.rep["claims"] if c["status"] == "not_found"])
        self.assertEqual(s["accuracy"], 100.0)

    def test_seeded_true_claims(self):
        for kind, text in [("command", "pip install -e ."), ("command", "pip install -r requirements-dev.txt"),
                           ("command", "tool --verbose --out result.json"), ("flag", "--verbose"), ("flag", "--out"),
                           ("command", "python -m pkg --help"), ("script", "make test"), ("script", "make lint"),
                           ("path", "pkg/cli.py")]:
            self.assertEqual(claim(self.rep, kind, text)["status"], "verified", (kind, text))

    def test_generic_commands_excluded(self):
        for text in ("python -m venv .venv", "source .venv/bin/activate", "python --version"):
            self.assertEqual(claim(self.rep, "command", text)["status"], "generic", text)


class PyCliBad(unittest.TestCase):
    def setUp(self):
        self.rep = report(PY, "README.bad.md")

    def test_every_seeded_error_is_caught(self):
        self.assertEqual(claim(self.rep, "flag", "--dry-run")["status"], "not_found")
        self.assertEqual(claim(self.rep, "script", "make release")["status"], "not_found")
        self.assertEqual(claim(self.rep, "command", "python scripts/train.py")["status"], "not_found")

    def test_declared_bin_itself_is_real(self):
        self.assertEqual(claim(self.rep, "command", "tool --dry-run")["status"], "verified")

    def test_summary(self):
        s = self.rep["summary"]
        self.assertEqual((s["verified"], s["not_found"], s["checked"]), (1, 3, 4))
        self.assertEqual(s["accuracy"], 25.0)


class Parsing(unittest.TestCase):
    def test_split_statements(self):
        self.assertEqual(vr.split_statements("cd app && npm i; npm test || echo fail"),
                         ["cd app", "npm i", "npm test", "echo fail"])
        self.assertEqual(vr.split_statements("pnpm dev | tee log.txt"), ["pnpm dev"])
        self.assertEqual(vr.split_statements("echo 'a && b' # comment"), ["echo 'a && b'"])
        self.assertEqual(vr.split_statements("node x.js > out.log 2>&1 &"), ["node x.js > out.log 2>&1"])

    def test_prompts_and_continuations(self):
        block = [(1, "$ make build \\"), (2, "    VERBOSE=1"), (3, "building..."), (4, "$ make test")]
        self.assertEqual([t for _, t in vr.logical_lines(block, "console")], ["make build VERBOSE=1", "make test"])
        npm_output = [(1, "$ npm start"), (2, "> app@1.0.0 start"), (3, "> node index.js")]
        self.assertEqual([t for _, t in vr.logical_lines(npm_output, "")], ["npm start"])

    def test_normalize_remote(self):
        a = vr.normalize_remote("git@github.com:Owner/Repo.git")
        self.assertEqual(a, vr.normalize_remote("https://github.com/owner/repo"))
        self.assertEqual(a, vr.normalize_remote("https://github.com/owner/repo.git/"))

    def test_env_table_detection(self):
        self.assertTrue(vr.table_is_env("| Variable | Required |"))
        self.assertTrue(vr.table_is_env("| Name | Default | Description |"))
        self.assertFalse(vr.table_is_env("| Task | Command |"))


class Cli(unittest.TestCase):
    def test_json_contract(self):
        code, out, err = run_cli(NODE / "README.bad.md", "--repo", NODE, "--json")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(set(data), {"readme", "repo", "summary", "by_kind", "claims"})
        self.assertEqual(set(data["summary"]), {"verified", "not_found", "unverifiable", "generic", "checked", "accuracy"})
        for kind, counts in data["by_kind"].items():
            self.assertIn(kind, vr.KINDS)
            self.assertEqual(set(counts), {"verified", "not_found", "unverifiable"})
        for c in data["claims"]:
            self.assertEqual(set(c), {"kind", "text", "line", "status", "evidence"})
            self.assertIn(c["status"], vr.STATUSES)
            self.assertIsInstance(c["line"], int)

    def test_human_output(self):
        code, out, _ = run_cli(PY / "README.bad.md", "--repo", PY)
        self.assertEqual(code, 0)
        self.assertIn("✗", out)
        self.assertIn("--dry-run", out)
        self.assertIn("claims: 4 checked · 1 verified · 3 not found", out)
        self.assertIn("accuracy 25.0%", out)

    def test_min_accuracy_gate(self):
        self.assertEqual(run_cli(PY / "README.bad.md", "--repo", PY, "--min-accuracy", "90")[0], 1)
        self.assertEqual(run_cli(PY / "README.bad.md", "--repo", PY, "--min-accuracy", "25")[0], 0)
        self.assertEqual(run_cli(PY / "README.good.md", "--repo", PY, "--min-accuracy", "100")[0], 0)

    def test_bad_input_exits_2(self):
        self.assertEqual(run_cli(FIXTURES / "missing.md", "--repo", PY)[0], 2)
        self.assertEqual(run_cli(PY / "README.good.md", "--repo", FIXTURES / "nope")[0], 2)
        self.assertEqual(run_cli(PY / "README.good.md", "--repo", PY, "--min-accuracy", "lots")[0], 2)
        self.assertEqual(run_cli(PY / "README.good.md", "--bogus")[0], 2)


if __name__ == "__main__":
    unittest.main()
