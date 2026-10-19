# Contributing to readme-forge

Thanks for helping. This guide gets you from clone to merged PR.

## Ways to contribute

- **Report a bug:** [open an issue](https://github.com/tanmayai23/README-Editor-skill/issues/new?template=bug_report.yml) with the command you ran and what you expected.
- **Report a broken widget:** profile widget hosts change often. [Open a widget report](https://github.com/tanmayai23/README-Editor-skill/issues/new?template=broken_widget.yml) with the URL that fails.
- **Suggest a feature:** [open a feature request](https://github.com/tanmayai23/README-Editor-skill/issues/new?template=feature_request.yml) and describe the problem before the solution.
- **Add a banner style, palette or template:** read the rules below first.
- **Pick up an issue:** look for [`good first issue`](https://github.com/tanmayai23/README-Editor-skill/issues?q=is%3Aopen+label%3A%22good+first+issue%22) and comment that you're taking it.

## Development setup

You need Python 3.8+ (standard library only). To try the skill end to end you also need [Claude Code](https://code.claude.com).

```bash
git clone https://github.com/tanmayai23/README-Editor-skill.git
cd README-Editor-skill
cp -r readme-forge ~/.claude/skills/readme-forge                 # core skill: facts, verification, scoring
cp -r readme-forge-design ~/.claude/skills/readme-forge-design   # optional: banners and profile READMEs
```

## Before you open a PR

Run the same checks as CI:

```bash
python -m unittest discover -s tests -v
python -m py_compile readme-forge/scripts/*.py readme-forge-design/scripts/*.py action/report.py
python readme-forge/scripts/score_readme.py README.md --repo . --min 85
python readme-forge/scripts/verify_readme.py README.md --repo . --min-accuracy 100
```

Changed detection logic in `analyze_repo.py`, `import_graph.py` or `verify_readme.py`? Add a fixture under `tests/fixtures/` and a test that fails without your change.

- Branch from `main`: `git checkout -b feat/short-description`.
- Keep each PR to one change, and add a line to `CHANGELOG.md` under **Unreleased**.
- Write commit messages in the imperative mood ("Add X", "Fix Y").

## Rules the skill depends on

- **Scripts stay standard-library only.** Nobody should need a `pip install` step.
- **Never invent facts.** Anything the analyzer can't find becomes a `TODO`, not a guess.
- **Every claim in a README must pass `verify_readme.py`.** That includes this repo's own README.
- **Banners** (`readme-forge-design`): ship a dark and a light SVG, make the first frame complete, and animate with CSS, not SMIL, so `prefers-reduced-motion` stops it. Regenerate the gallery with `python readme-forge-design/scripts/make_banner.py --gallery readme-forge-design/assets/banners`.
- **Widgets:** add a URL to `readme-forge-design/references/widgets.md` only after `check_links.py` returns 200 for it, and note the date you tested it.
- **Templates:** every placeholder uses `{{UPPER_SNAKE}}` so the scorer flags any that are left over.

## Code of conduct

By participating you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
