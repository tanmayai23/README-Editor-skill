# Contributing to {{NAME}}

Thanks for helping. This guide gets you from clone to merged PR.

## Ways to contribute

- **Report a bug:** [open an issue]({{ISSUES_URL}}/new?template=bug_report.yml) with steps to reproduce.
- **Suggest a feature:** [open a feature request]({{ISSUES_URL}}/new?template=feature_request.yml) and describe the problem before the solution.
- **Fix something:** look for [`good first issue`]({{ISSUES_URL}}?q=is%3Aopen+label%3A%22good+first+issue%22) issues and comment that you're taking one.
- **Improve docs:** typo fixes are welcome without an issue.

## Development setup

Requires {{PREREQUISITES}}.

```bash
git clone {{REPO_URL}}
cd {{REPO_DIR}}
{{INSTALL}}
{{RUN_DEV}}
```

## Before you open a PR

```bash
{{LINT}}
{{TEST}}
```

- Create a branch from `{{DEFAULT_BRANCH}}`: `git checkout -b fix/short-description`.
- Keep each PR to one change. Add or update tests and docs alongside the code.
- Write commit messages in the imperative mood ("Add X", "Fix Y"). {{Conventional Commits if used: `feat:`, `fix:`, `docs:`}}
- Fill in the PR template and link the issue (`Closes #123`).

## Code style

{{FORMATTER / LINTER / CONVENTIONS, e.g. "Formatted with Prettier; run `pnpm format`."}}

## Review process

A maintainer usually responds within {{TIMEFRAME}}. CI must pass before merge. We may ask for changes; that's normal.

## Code of conduct

By participating you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
