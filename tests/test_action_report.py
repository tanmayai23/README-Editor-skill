"""Tests for action/report.py (the GitHub Action). No network: the HTTP layer is faked."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "action"

_spec = importlib.util.spec_from_file_location("rf_action_report", str(ROOT / "action" / "report.py"))
report = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(report)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def result(path="README.md", score="score_before.json", verify="verify_before.json"):
    return {"path": path, "score": fixture(score) if score else None,
            "verify": fixture(verify) if verify else None, "error": None, "verify_error": None}


class FakeGitHub:
    """Records calls and answers like the issues comments API."""

    def __init__(self, comments=None, status=None):
        self.comments = comments or []
        self.status = status or {}  # method -> forced status code
        self.calls = []

    def __call__(self, method, url, token, data=None):
        self.calls.append((method, url, data))
        if method in self.status:
            return self.status[method], {"message": "Resource not accessible by integration"}
        if method == "GET":
            page = int(url.split("page=")[-1])
            return 200, self.comments[(page - 1) * 100: page * 100]
        if method == "PATCH":
            return 200, {"id": int(url.rsplit("/", 1)[-1])}
        if method == "POST":
            return 201, {"id": 999}
        return 500, None


class RenderTests(unittest.TestCase):
    def test_marker_header_and_score(self):
        md = report.render([result()])
        self.assertTrue(md.startswith(report.MARKER))
        self.assertIn("45/100 · grade F", md)
        self.assertIn("`█████████░░░░░░░░░░░` **45**/100", md)

    def test_accuracy_line(self):
        md = report.render([result()])
        self.assertIn("**Accuracy:** 1/2 commands, env vars and paths in the README match the code (50%).", md)

    def test_category_table(self):
        md = report.render([result()])
        self.assertIn("| Category | Score | |", md)
        self.assertIn("| getting-started | 13/25 |", md)
        self.assertIn("| quality | 3.6/20 |", md)

    def test_findings_details_skip_info(self):
        md = report.render([result()])
        self.assertIn("<details><summary>4 errors, 4 warnings</summary>", md)
        self.assertIn("- **ERROR** `accessibility` image without alt text: screenshot.png (line 10)", md)
        self.assertNotIn("consider a logo", md)
        self.assertNotIn("no status badges", md)

    def test_findings_capped(self):
        res = result()
        res["score"]["findings"] = [{"level": "WARN", "category": "x", "message": f"m{i}", "line": i}
                                    for i in range(30)]
        md = report.render([res])
        self.assertIn("m19", md)
        self.assertNotIn("m20 ", md)
        self.assertIn("...and 10 more", md)

    def test_untrusted_text_escaped(self):
        md = report.render([result()])
        self.assertIn("ping &#64;octo-org/team \\| &lt;b&gt;html&lt;/b&gt;", md)
        self.assertNotIn("@octo-org", md)

    def test_not_found_claims_table(self):
        md = report.render([result()])
        self.assertIn("<details><summary>1 claim not found in the code</summary>", md)
        self.assertIn("| 8 | script | `npm run serve` | package.json scripts: dev, build, start, test |", md)
        self.assertNotIn("cd orbit-api", md)

    def test_verifier_missing_degrades(self):
        md = report.render([result(verify=None)])
        self.assertIn("Claim check unavailable", md)
        self.assertNotIn("**Accuracy:**", md)

    def test_unscorable_file(self):
        res = {"path": "nope.md", "score": None, "verify": None, "error": "file not found", "verify_error": None}
        md = report.render([res])
        self.assertIn("Could not score this README:** file not found", md)

    def test_multiple_sections(self):
        md = report.render([result("a.md"), result("b.md", score="score_good.json", verify=None)])
        self.assertIn("### `a.md` · 45/100", md)
        self.assertIn("### `b.md` · 92/100 · grade A", md)
        self.assertEqual(md.count(report.MARKER), 1)

    def test_code_span_with_backticks(self):
        self.assertEqual(report.code("a`b"), "``a`b``")


class ThresholdTests(unittest.TestCase):
    def test_no_thresholds_pass(self):
        self.assertEqual(report.check_thresholds([result()]), [])

    def test_min_score_fails(self):
        fails = report.check_thresholds([result()], min_score=80)
        self.assertEqual(len(fails), 1)
        self.assertIn("below min-score 80", fails[0])

    def test_min_score_passes(self):
        self.assertEqual(report.check_thresholds([result(score="score_good.json")], min_score=80), [])

    def test_min_accuracy(self):
        self.assertEqual(len(report.check_thresholds([result()], min_accuracy=90)), 1)
        self.assertEqual(report.check_thresholds([result()], min_accuracy=50), [])
        # no verifier -> accuracy unknown -> not enforced
        self.assertEqual(report.check_thresholds([result(verify=None)], min_accuracy=90), [])

    def test_accuracy_fraction_input(self):
        self.assertEqual(report.parse_threshold("0.9", percent=True), 90.0)
        self.assertEqual(report.parse_threshold("85", percent=True), 85.0)

    def test_unscorable_always_fails(self):
        res = {"path": "x.md", "score": None, "verify": None, "error": "file not found", "verify_error": None}
        self.assertEqual(len(report.check_thresholds([res])), 1)

    def test_summary_uses_weakest(self):
        out = report.summarize([result(score="score_good.json"), result()])
        self.assertEqual(out, {"score": "45", "grade": "F", "accuracy": "50"})

    def test_failed_threshold_shown_in_markdown(self):
        md = report.render([result()], min_score=80)
        self.assertIn("**Check failed:** score 45 is below the minimum of 80.", md)


class UpsertTests(unittest.TestCase):
    API, REPO = "https://api.github.com", "o/r"

    def test_creates_when_absent(self):
        gh = FakeGitHub(comments=[{"id": 1, "body": "hello", "user": {"type": "User"}}])
        self.assertEqual(report.upsert_comment(self.API, self.REPO, 7, "t", "body", gh), ("created", 999))
        self.assertEqual([c[0] for c in gh.calls], ["GET", "POST"])
        self.assertTrue(gh.calls[1][1].endswith("/repos/o/r/issues/7/comments"))

    def test_updates_bot_comment(self):
        gh = FakeGitHub(comments=[
            {"id": 1, "body": report.MARKER + " quoted by a human", "user": {"type": "User"}},
            {"id": 2, "body": report.MARKER + " old", "user": {"type": "Bot"}},
        ])
        self.assertEqual(report.upsert_comment(self.API, self.REPO, 7, "t", "new", gh), ("updated", 2))
        self.assertEqual(gh.calls[-1], ("PATCH", self.API + "/repos/o/r/issues/comments/2", {"body": "new"}))

    def test_paginates(self):
        comments = [{"id": i, "body": "x", "user": {"type": "User"}} for i in range(150)]
        comments.append({"id": 500, "body": report.MARKER, "user": {"type": "Bot"}})
        gh = FakeGitHub(comments=comments)
        self.assertEqual(report.upsert_comment(self.API, self.REPO, 7, "t", "b", gh), ("updated", 500))
        self.assertEqual([c[0] for c in gh.calls], ["GET", "GET", "PATCH"])

    def test_patch_forbidden_falls_back_to_post(self):
        gh = FakeGitHub(comments=[{"id": 3, "body": report.MARKER, "user": {"type": "User"}}],
                        status={"PATCH": 403})
        self.assertEqual(report.upsert_comment(self.API, self.REPO, 7, "t", "b", gh), ("created", 999))


class CommentEnvTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.event = os.path.join(self.tmp, "event.json")
        with open(self.event, "w", encoding="utf-8") as fh:
            json.dump({"number": 42, "pull_request": {"number": 42}}, fh)
        self.env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": self.event,
                    "GITHUB_REPOSITORY": "o/r", "RF_GITHUB_TOKEN": "t"}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_posts_on_pull_request(self):
        gh = FakeGitHub()
        status = report.maybe_comment("body", self.env, gh)
        self.assertEqual(status, "created comment 999")
        self.assertIn("/issues/42/comments", gh.calls[-1][1])

    def test_skips_on_push(self):
        gh = FakeGitHub()
        env = dict(self.env, GITHUB_EVENT_NAME="push")
        self.assertTrue(report.maybe_comment("b", env, gh).startswith("skipped"))
        self.assertEqual(gh.calls, [])

    def test_skips_without_token(self):
        env = dict(self.env)
        del env["RF_GITHUB_TOKEN"]
        self.assertEqual(report.maybe_comment("b", env, FakeGitHub()), "skipped: no github-token")

    def test_forked_pr_403_warns_and_does_not_raise(self):
        gh = FakeGitHub(status={"GET": 403})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            status = report.maybe_comment("b", self.env, gh)
        self.assertTrue(status.startswith("failed"))
        self.assertIn("::warning::", buf.getvalue())
        self.assertIn("forks get a read-only token", buf.getvalue())

    def test_network_error_does_not_raise(self):
        def boom(*a, **k):
            raise report.CommentError("network error talking to GitHub: timed out")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            status = report.maybe_comment("b", self.env, boom)
        self.assertTrue(status.startswith("failed"))
        self.assertIn("::warning::", buf.getvalue())


class MainTests(unittest.TestCase):
    """End to end against the real scorer, with a GitHub-like environment and no token."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "proj")
        os.makedirs(self.repo)
        with open(os.path.join(self.repo, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("# demo\n\nA tiny project.\n\n## Install\n\n```bash\npip install demo\n```\n")
        self.out = os.path.join(self.tmp, "out.txt")
        self.summary = os.path.join(self.tmp, "summary.md")
        self.report_file = os.path.join(self.tmp, "r", "report.md")
        self.env = {"GITHUB_ACTIONS": "true", "GITHUB_OUTPUT": self.out,
                    "GITHUB_STEP_SUMMARY": self.summary, "GITHUB_EVENT_NAME": "pull_request"}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, *extra):
        readme = os.path.join(self.repo, "README.md")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = report.main([readme, "--repo", self.repo, "--report-file", self.report_file] + list(extra),
                               env=self.env)
        return code, buf.getvalue()

    def test_writes_outputs_summary_and_report(self):
        code, stdout = self.run_main()
        self.assertEqual(code, 0)
        outputs = dict(line.split("=", 1) for line in Path(self.out).read_text(encoding="utf-8").splitlines())
        self.assertTrue(outputs["score"].isdigit())
        self.assertIn(outputs["grade"], "ABCDF")
        self.assertEqual(outputs["report"], str(Path(self.report_file).resolve()))
        self.assertTrue(Path(self.summary).read_text(encoding="utf-8").startswith(report.MARKER))
        self.assertTrue(Path(self.report_file).read_text(encoding="utf-8").startswith(report.MARKER))
        self.assertIn("::stop-commands::", stdout)

    def test_min_score_exit_code(self):
        code, stdout = self.run_main("--min-score", "101")
        self.assertEqual(code, 1)
        self.assertIn("::error::", stdout)

    def test_uses_verifier_when_present(self):
        scripts = os.path.join(self.tmp, "scripts")
        os.makedirs(scripts)
        shutil.copy(str(ROOT / "readme-forge" / "scripts" / "score_readme.py"), scripts)
        with open(os.path.join(scripts, "verify_readme.py"), "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.stdout.write(open(%r, encoding='utf-8').read())\n"
                     % str(FIXTURES / "verify_before.json"))
        res = report.evaluate(os.path.join(self.repo, "README.md"), self.repo, scripts)
        self.assertEqual(res["verify"]["summary"]["not_found"], 1)
        self.assertIn("**Accuracy:** 1/2", report.render([res]))

    def test_missing_readme_fails(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = report.main([os.path.join(self.tmp, "missing.md"), "--no-comment"], env=self.env)
        self.assertEqual(code, 1)
        self.assertIn("file not found", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
