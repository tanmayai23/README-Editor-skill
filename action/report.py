#!/usr/bin/env python3
"""readme-forge GitHub Action: score a README, check its claims, report on the PR.

Runs score_readme.py (and verify_readme.py when it exists) on one or more
READMEs, builds one Markdown report, writes it to the job summary and to
GITHUB_OUTPUT, upserts a single PR comment, and enforces score/accuracy
thresholds. Standard library only, Python 3.8+.

Local use (prints the Markdown, never talks to GitHub):
    python action/report.py README.md --repo . --no-comment
    python action/report.py docs/a.md docs/b.md --min-score 80

Exit codes: 0 ok, 1 a threshold failed or a README could not be scored.
Commenting problems (forked PRs, missing permissions, network) only warn.
"""
import argparse
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

MARKER = "<!-- readme-forge-report -->"
HERE = Path(__file__).resolve().parent
DEFAULT_SCRIPTS = HERE.parent / "readme-forge" / "scripts"
PROJECT_URL = "https://github.com/tanmayai23/README-Editor-skill"
MAX_FINDINGS = 20
MAX_CLAIMS = 50
MAX_COMMENT = 60000  # GitHub's hard limit is 65536 characters
PR_EVENTS = ("pull_request", "pull_request_target")


class CommentError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


# ----------------------------------------------------------------------------- running the scripts
def run_json(cmd, cwd=None):
    """Run a script that prints JSON. Returns (data or None, error text or None)."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=300, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    out = proc.stdout.decode("utf-8", "replace")
    try:
        return json.loads(out), None
    except ValueError:
        err = proc.stderr.decode("utf-8", "replace").strip() or out.strip()
        return None, (err.splitlines() or ["no output"])[-1][:300]


def score_file(readme, repo, scripts_dir):
    script = Path(scripts_dir) / "score_readme.py"
    return run_json([sys.executable, str(script), str(readme), "--repo", str(repo), "--json"])


def verify_file(readme, repo, scripts_dir):
    """Returns (data, error). data is None and error is None when the verifier is not installed."""
    script = Path(scripts_dir) / "verify_readme.py"
    if not script.is_file():
        return None, None
    return run_json([sys.executable, str(script), str(readme), "--repo", str(repo), "--json"])


def accuracy_of(verify):
    """(verified, checked, percent or None) from verify_readme JSON."""
    if not verify:
        return 0, 0, None
    s = verify.get("summary") or {}
    verified = int(s.get("verified") or 0)
    checked = int(s.get("checked") or (verified + int(s.get("not_found") or 0)))
    if checked > 0:
        return verified, checked, round(100.0 * verified / checked, 1)
    acc = s.get("accuracy")
    if isinstance(acc, (int, float)):
        return verified, checked, round(acc * 100 if acc <= 1 else acc, 1)
    return verified, checked, None


def evaluate(readme, repo, scripts_dir):
    result = {"path": str(readme), "score": None, "verify": None, "error": None, "verify_error": None}
    if not Path(readme).is_file():
        result["error"] = "file not found"
        return result
    score, err = score_file(readme, repo, scripts_dir)
    if score is None or "score" not in score:
        result["error"] = "scorer failed: " + (err or "unexpected output")
    result["score"] = score if score and "score" in score else None
    verify, verr = verify_file(readme, repo, scripts_dir)
    result["verify"] = verify
    result["verify_error"] = verr
    return result


# ----------------------------------------------------------------------------- markdown
def esc(text):
    """Make untrusted text safe inside a Markdown table cell or list item."""
    text = str(text if text is not None else "")
    text = text.replace("\r", " ").replace("\n", " ")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("|", "\\|").replace("@", "&#64;")  # no table breaks, no @mention pings
    return text


def code(text):
    """Inline code span that survives backticks and pipes in the text."""
    text = str(text if text is not None else "").replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    ticks = max((len(m) for m in re.findall(r"`+", text)), default=0)
    fence = "`" * (ticks + 1)
    pad = " " if text.startswith("`") or text.endswith("`") or not text.strip() else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def bar(ratio, width=20):
    ratio = max(0.0, min(1.0, ratio))
    filled = int(round(width * ratio))
    return "█" * filled + "░" * (width - filled)


def plural(n, word, many=None):
    return f"{n} {word if n == 1 else (many or word + 's')}"


def render_file(res, min_score=0.0, min_accuracy=0.0):
    lines = []
    score = res["score"]
    if score is None:
        lines.append(f"### {code(res['path'])}")
        lines.append("")
        lines.append(f"> **Could not score this README:** {esc(res['error'])}")
        return "\n".join(lines)

    total = score.get("score", 0)
    grade = score.get("grade", "?")
    lines.append(f"### {code(res['path'])} · {total}/100 · grade {grade}")
    lines.append("")
    lines.append(f"`{bar(total / 100.0)}` **{total}**/100")
    lines.append("")

    verified, checked, pct = accuracy_of(res["verify"])
    if res["verify"] is not None:
        if checked:
            lines.append(f"**Accuracy:** {verified}/{checked} commands, env vars and paths in the README "
                         f"match the code ({pct:g}%).")
        else:
            lines.append("**Accuracy:** no commands, env vars or paths to check.")
    elif res.get("verify_error"):
        lines.append(f"_Claim check failed: {esc(res['verify_error'])}_")
    else:
        lines.append("_Claim check unavailable in this version of readme-forge._")
    lines.append("")

    problems = []
    if min_score and total < min_score:
        problems.append(f"score {total} is below the minimum of {min_score:g}")
    if min_accuracy and pct is not None and pct < min_accuracy:
        problems.append(f"accuracy {pct:g}% is below the minimum of {min_accuracy:g}%")
    if problems:
        lines.append("> **Check failed:** " + "; ".join(problems) + ".")
        lines.append("")

    cats = score.get("categories") or {}
    if cats:
        lines.append("| Category | Score | |")
        lines.append("|---|---:|---|")
        for name, v in cats.items():
            got, mx = v.get("score", 0), v.get("max", 0) or 1
            lines.append(f"| {esc(name)} | {got:g}/{mx:g} | `{bar(got / float(mx), 10)}` |")
        lines.append("")

    findings = [f for f in score.get("findings") or [] if f.get("level") in ("ERROR", "WARN")]
    if findings:
        errs = sum(1 for f in findings if f["level"] == "ERROR")
        warns = len(findings) - errs
        lines.append(f"<details><summary>{plural(errs, 'error')}, {plural(warns, 'warning')}</summary>")
        lines.append("")
        for f in findings[:MAX_FINDINGS]:
            loc = f" (line {f['line']})" if f.get("line") else ""
            lines.append(f"- **{f['level']}** `{esc(f.get('category', ''))}` {esc(f.get('message', ''))}{loc}")
        if len(findings) > MAX_FINDINGS:
            lines.append(f"- ...and {len(findings) - MAX_FINDINGS} more. Run `score_readme.py` locally for the full list.")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    missing = [c for c in (res["verify"] or {}).get("claims") or [] if c.get("status") == "not_found"]
    if missing:
        lines.append(f"<details><summary>{plural(len(missing), 'claim')} not found in the code</summary>")
        lines.append("")
        lines.append("| Line | Kind | Claim | Evidence |")
        lines.append("|---:|---|---|---|")
        for c in missing[:MAX_CLAIMS]:
            lines.append(f"| {esc(c.get('line', ''))} | {esc(c.get('kind', ''))} | {code(c.get('text', ''))} "
                         f"| {esc(c.get('evidence', ''))} |")
        if len(missing) > MAX_CLAIMS:
            lines.append(f"| | | ...and {len(missing) - MAX_CLAIMS} more | |")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines).rstrip()


def render(results, min_score=0.0, min_accuracy=0.0):
    parts = [MARKER, "## README report", ""]
    for res in results:
        parts.append(render_file(res, min_score, min_accuracy))
        parts.append("")
    parts.append(f"<sub>Generated by [readme-forge]({PROJECT_URL}). "
                 "Scores are heuristic; the claim check compares the README against the repository.</sub>")
    return "\n".join(parts) + "\n"


# ----------------------------------------------------------------------------- thresholds and outputs
def summarize(results):
    """Outputs reflect the weakest README: lowest score, lowest accuracy."""
    scored = [r for r in results if r["score"] is not None]
    out = {"score": "", "grade": "", "accuracy": ""}
    if scored:
        worst = min(scored, key=lambda r: r["score"].get("score", 0))
        out["score"] = str(worst["score"].get("score", ""))
        out["grade"] = str(worst["score"].get("grade", ""))
    accs = [accuracy_of(r["verify"])[2] for r in results]
    accs = [a for a in accs if a is not None]
    if accs:
        out["accuracy"] = f"{min(accs):g}"
    return out


def check_thresholds(results, min_score=0.0, min_accuracy=0.0):
    """List of failure messages (empty means pass)."""
    failures = []
    for r in results:
        if r["score"] is None:
            failures.append(f"{r['path']}: {r['error']}")
            continue
        total = r["score"].get("score", 0)
        if min_score and total < min_score:
            failures.append(f"{r['path']}: README score {total} is below min-score {min_score:g}")
        pct = accuracy_of(r["verify"])[2]
        if min_accuracy and pct is not None and pct < min_accuracy:
            failures.append(f"{r['path']}: claim accuracy {pct:g}% is below min-accuracy {min_accuracy:g}%")
    return failures


def workflow_escape(text):
    return str(text).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def annotate(level, message):
    print(f"::{level}::{workflow_escape(message)}", flush=True)


def write_outputs(path, values):
    with open(path, "a", encoding="utf-8") as fh:
        for k, v in values.items():
            v = str(v).replace("\r", " ").replace("\n", " ")
            fh.write(f"{k}={v}\n")


def parse_threshold(value, percent=False):
    try:
        x = float(value or 0)
    except ValueError:
        raise SystemExit(f"error: threshold must be a number, got {value!r}")
    if percent and 0 < x <= 1:
        x *= 100  # accept 0.9 as 90%
    return x


# ----------------------------------------------------------------------------- PR comment
def http_request(method, url, token, data=None):
    """Minimal GitHub REST call. Returns (status, parsed JSON or None). Never raises on HTTP errors."""
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "readme-forge-action")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace") if exc.fp else ""
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, None
    except (urllib.error.URLError, OSError) as exc:
        raise CommentError(f"network error talking to GitHub: {exc}")


def find_marker_comment(comments):
    ours = [c for c in comments if MARKER in (c.get("body") or "")]
    bots = [c for c in ours if (c.get("user") or {}).get("type") == "Bot"]
    pick = bots or ours
    return pick[0] if pick else None


def upsert_comment(api, repo, number, token, body, request=None):
    """Update the existing report comment or create one. Returns ("updated"|"created", comment id)."""
    request = request or http_request
    base = f"{api.rstrip('/')}/repos/{repo}/issues"
    comments, page = [], 1
    while page <= 50:
        status, data = request("GET", f"{base}/{number}/comments?per_page=100&page={page}", token)
        if status != 200 or not isinstance(data, list):
            raise CommentError(f"listing comments failed (HTTP {status})", status)
        comments.extend(data)
        if len(data) < 100:
            break
        page += 1
    existing = find_marker_comment(comments)
    if existing:
        status, data = request("PATCH", f"{base}/comments/{existing['id']}", token, {"body": body})
        if status == 200:
            return "updated", existing["id"]
        if status not in (403, 404):  # not ours to edit: fall through and post a fresh one
            raise CommentError(f"updating comment failed (HTTP {status})", status)
    status, data = request("POST", f"{base}/{number}/comments", token, {"body": body})
    if status != 201:
        raise CommentError(f"creating comment failed (HTTP {status})", status)
    return "created", (data or {}).get("id")


def pr_number(event_path):
    try:
        with open(event_path, encoding="utf-8") as fh:
            event = json.load(fh)
    except (OSError, ValueError, TypeError):
        return None
    n = (event.get("pull_request") or {}).get("number") or event.get("number")
    return n if isinstance(n, int) else None


def maybe_comment(body, env=None, request=None):
    """Post or update the PR comment when the environment allows it. Never raises.
    Returns a short status string for logs/tests."""
    env = os.environ if env is None else env
    if env.get("GITHUB_EVENT_NAME") not in PR_EVENTS:
        return "skipped: not a pull_request event"
    token = env.get("RF_GITHUB_TOKEN") or env.get("GITHUB_TOKEN")
    repo = env.get("GITHUB_REPOSITORY")
    number = pr_number(env.get("GITHUB_EVENT_PATH"))
    if not token:
        return "skipped: no github-token"
    if not repo or not number:
        return "skipped: no repository or PR number in the event"
    if len(body) > MAX_COMMENT:
        body = body[:MAX_COMMENT] + "\n\n_Report truncated; see the job summary for the full version._\n"
    api = env.get("GITHUB_API_URL") or "https://api.github.com"
    try:
        action, cid = upsert_comment(api, repo, number, token, body, request=request)
        return f"{action} comment {cid}"
    except CommentError as exc:
        if exc.status == 403:
            annotate("warning", "readme-forge could not comment on this PR (HTTP 403). Pull requests from "
                     "forks get a read-only token; the report is in the job summary instead. "
                     "For same-repo PRs, grant 'pull-requests: write' in the workflow permissions.")
        else:
            annotate("warning", f"readme-forge could not comment on this PR: {exc}")
        return f"failed: {exc}"
    except Exception as exc:  # commenting must never fail the job
        annotate("warning", f"readme-forge could not comment on this PR: {exc}")
        return f"failed: {exc}"


# ----------------------------------------------------------------------------- main
def parse_args(argv):
    p = argparse.ArgumentParser(description="Score README files and report on GitHub pull requests.")
    p.add_argument("paths", nargs="*", help="README files (default README.md)")
    p.add_argument("--paths", dest="paths_list", default="",
                   help="space- or newline-separated README list (used by action.yml)")
    p.add_argument("--repo", default=".", help="repository root the README describes")
    p.add_argument("--min-score", default="0", help="fail when a README scores below this (0 = never)")
    p.add_argument("--min-accuracy", default="0", help="fail when claim accuracy is below this percent")
    p.add_argument("--comment", default="true", help="true/false: comment on pull requests")
    p.add_argument("--no-comment", action="store_true", help="never talk to the GitHub API")
    p.add_argument("--report-file", default="", help="also write the Markdown report here")
    p.add_argument("--scripts-dir", default=str(DEFAULT_SCRIPTS), help=argparse.SUPPRESS)
    return p.parse_args(argv)


def main(argv=None, env=None):
    env = os.environ if env is None else env
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    paths = list(args.paths) + args.paths_list.split()
    paths = list(dict.fromkeys(paths)) or ["README.md"]
    min_score = parse_threshold(args.min_score)
    min_accuracy = parse_threshold(args.min_accuracy, percent=True)
    comment = (not args.no_comment) and str(args.comment).strip().lower() in ("true", "1", "yes", "on")
    in_actions = env.get("GITHUB_ACTIONS") == "true"

    results = [evaluate(p, args.repo, args.scripts_dir) for p in paths]
    markdown = render(results, min_score, min_accuracy)

    report_file = args.report_file
    if report_file:
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        Path(report_file).write_text(markdown, encoding="utf-8")

    if in_actions:
        # README text is untrusted: stop workflow-command parsing while echoing it to the log
        token = secrets.token_hex(16)
        print(f"::stop-commands::{token}")
        print(markdown)
        print(f"::{token}::", flush=True)
    else:
        print(markdown)

    if env.get("GITHUB_STEP_SUMMARY"):
        with open(env["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(markdown + "\n")

    outputs = summarize(results)
    outputs["report"] = str(Path(report_file).resolve()) if report_file else ""
    if env.get("GITHUB_OUTPUT"):
        write_outputs(env["GITHUB_OUTPUT"], outputs)

    if comment:
        status = maybe_comment(markdown, env)
        print(f"readme-forge: PR comment {status}", file=sys.stderr)

    failures = check_thresholds(results, min_score, min_accuracy)
    for msg in failures:
        if in_actions:
            annotate("error", msg)
        else:
            print(f"error: {msg}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
