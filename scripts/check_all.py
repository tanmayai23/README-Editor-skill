#!/usr/bin/env python3
"""Run all CI validation checks locally using standard library only.

Mirrors .github/workflows/ci.yml step-by-step with clean pass/fail reporting.
"""

from __future__ import annotations

import glob
import os
import subprocess
import sys
from typing import List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_step(name: str, cmd: List[str] | str, shell: bool = False, env: dict | None = None) -> bool:
    print(f"\n[RUNNING] {name}...")
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            shell=shell,
            env=run_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            print(f"[PASSED]  {name}")
            return True
        else:
            print(f"[FAILED]  {name} (exit code {proc.returncode})")
            print(proc.stdout)
            return False
    except Exception as e:
        print(f"[ERROR]   {name}: {e}")
        return False


def main() -> int:
    os.chdir(REPO_ROOT)
    print("=" * 60)
    print("README-Editor-skill: Local CI Verification Suite")
    print(f"Working Directory: {REPO_ROOT}")
    print(f"Python Version:    {sys.version.split()[0]}")
    print("=" * 60)

    # 1. Compile scripts
    py_files = (
        glob.glob("readme-forge/scripts/*.py")
        + glob.glob("readme-forge-design/scripts/*.py")
        + ["action/report.py"]
    )
    compile_cmd = [sys.executable, "-m", "py_compile"] + py_files

    # 2. Template scoring helper commands
    hf_templates = glob.glob("readme-forge/templates/huggingface/*.md")
    profile_templates = glob.glob("readme-forge-design/templates/profile/*.md")

    steps: List[Tuple[str, List[str] | str, bool, dict | None]] = [
        ("Compile scripts", compile_cmd, False, None),
        ("Unit tests (15 ecosystems, import graphs, verifier, report)",
         [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], False, None),
        ("Analyze repo on demo sample-app",
         [sys.executable, "readme-forge/scripts/analyze_repo.py", "demo/sample-app", "--compact"], False, None),
        ("Import graph on demo sample-app",
         [sys.executable, "readme-forge/scripts/import_graph.py", "demo/sample-app"], False, None),
        ("Project README scores 85+",
         [sys.executable, "readme-forge/scripts/score_readme.py", "README.md", "--repo", ".", "--min", "85"], False, None),
        ("Every checked claim in project README matches code",
         [sys.executable, "readme-forge/scripts/verify_readme.py", "README.md", "--repo", ".", "--min-accuracy", "100"], False, None),
        ("Skill READMEs score 85+",
         f"{sys.executable} readme-forge/scripts/score_readme.py readme-forge/README.md --min 85 && "
         f"{sys.executable} readme-forge/scripts/score_readme.py readme-forge-design/README.md --min 85", True, None),
        ("Hugging Face card templates score",
         " && ".join([f"{sys.executable} readme-forge/scripts/score_readme.py \"{f}\" --hf" for f in hf_templates]), True, None),
        ("Profile templates score",
         " && ".join([f"{sys.executable} readme-forge/scripts/score_readme.py \"{f}\" --profile > /dev/null" for f in profile_templates]), True, None),
        ("Banner generator writes repo-relative paths",
         f"{sys.executable} readme-forge-design/scripts/make_banner.py --style aurora --title CI --out \"$PWD/ci-out\" | grep -q 'srcset=\"ci-out/header-dark.svg\"'", True, None),
        ("Banner generator embeds a logo",
         f"{sys.executable} readme-forge-design/scripts/make_banner.py --style spotlight --palette ghost --logo .github/assets/logo-320.png --title CI --out ci-logo > /dev/null && "
         f"grep -q 'href=\"data:image/png;base64,' ci-logo/header-dark.svg", True, None),
        ("Linked banner snippet keeps <a> and <picture> on separate lines",
         f"{sys.executable} readme-forge-design/scripts/make_banner.py --kind button --title Go --href \"#go\" --out ci-btn | grep -qx '<a href=\"#go\">'", True, None),
        ("Page kit examples and README cards rebuild without changes",
         f"{sys.executable} readme-forge-design/scripts/make_page.py --spec readme-forge-design/examples/keynote-profile/page.json && "
         f"{sys.executable} readme-forge-design/scripts/make_page.py --spec readme-forge-design/examples/keynote-project/page.json && "
         f"{sys.executable} readme-forge-design/scripts/make_page.py --spec readme-forge-design/examples/keynote-coder/page.json && "
         f"{sys.executable} readme-forge-design/scripts/make_page.py --spec .github/page.json && "
         f"git diff --exit-code -- readme-forge-design/examples .github/assets/page .github/readme-cards.md", True, None),
        ("Page kit README passes scorer design checks",
         [sys.executable, "readme-forge/scripts/score_readme.py", "readme-forge-design/examples/keynote-profile/README.md", "--profile", "--min", "85"], False, None),
        ("Fancy text maps letters, digits and Unicode holes",
         f"test \"$({sys.executable} readme-forge-design/scripts/fancy_text.py 'Hi 7' --style sans-bold)\" = \"𝗛𝗶 𝟳\" && "
         f"test \"$({sys.executable} readme-forge-design/scripts/fancy_text.py 'RCh' --style double-struck)\" = \"ℝℂ𝕙\"", True, {"PYTHONIOENCODING": "utf-8"}),
        ("Tic-tac-toe game lifecycle validation",
         f"T=\"$PWD/readme-forge-design/templates/profile/game/tictactoe.py\" && "
         f"rm -rf ttt && mkdir ttt && cd ttt && "
         f"printf '<!-- TICTACTOE:START -->\\n<!-- TICTACTOE:END -->\\n' > README.md && "
         f"{sys.executable} \"$T\" --repo a/a --render && "
         f"for m in \"a 1\" \"b 4\" \"c 2\" \"d 5\"; do set -- $m; {sys.executable} \"$T\" --repo a/a --title \"ttt|move|$2\" --user \"$1\"; done && "
         f"! {sys.executable} \"$T\" --repo a/a --title \"ttt|move|1\" --user e && "
         f"! {sys.executable} \"$T\" --repo a/a --title 'ttt|move|3; rm -rf ~' --user e && "
         f"{sys.executable} \"$T\" --repo a/a --title \"ttt|move|3\" --user e | grep -q \"wins\" && "
         f"grep -q '\"X\": 1' .github/game/tictactoe.json && cd .. && rm -rf ttt", True, {"PYTHONIOENCODING": "utf-8"}),
    ]

    results: List[Tuple[str, bool]] = []
    for name, cmd, shell, env in steps:
        passed = run_step(name, cmd, shell=shell, env=env)
        results.append((name, passed))

    # Cleanup artifacts from tests
    for temp_dir in ["ci-out", "ci-logo", "ci-btn", "ttt"]:
        if os.path.exists(temp_dir):
            subprocess.run(["rm", "-rf", temp_dir], check=False)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str:4}] {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("All CI validation checks passed successfully.")
        return 0
    else:
        print("Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
