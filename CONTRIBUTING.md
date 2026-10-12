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
cp -r readme-forge ~/.claude/skills/readme-forge   # use your local copy as the skill
```

## Before you open a PR

Run the same checks as CI:

```bash
python -m py_compile readme-forge/scripts/*.py
python readme-forge/scripts/score_readme.py README.md --repo .
python readme-forge/scripts/analyze_repo.py demo/sample-app --compact
```

- Branch from `main`: `git checkout -b feat/short-description`.
- Keep each PR to one change, and add a line to `CHANGELOG.md` under **Unreleased**.
- Write commit messages in the imperative mood ("Add X", "Fix Y").

## Rules the skill depends on

- **Scripts stay standard-library only.** Nobody should need a `pip install` step.
- **Never invent facts.** Anything the analyzer can't find becomes a `TODO`, not a guess.
- **Banners:** ship a dark and a light SVG, make the first frame complete, and honour `prefers-reduced-motion`. Generate them with `make_banner.py`.
- **Widgets:** add a URL to `references/widgets.md` only after `check_links.py` returns 200 for it, and note the date you tested it.
- **Templates:** every placeholder uses `{{UPPER_SNAKE}}` so the scorer flags any that are left over.

## Code of conduct

By participating you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
