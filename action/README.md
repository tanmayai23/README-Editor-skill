# readme-forge GitHub Action

Scores your README from 0 to 100 on every pull request. It also checks that the commands, scripts, env vars and paths the README mentions exist in the code. The action posts one comment on the PR and edits that same comment on every later push, so the thread doesn't fill up with copies. Everything runs on the runner's own Python (3.8+). It needs no Docker image or Node packages and makes no calls outside the GitHub API.

## Usage

```yaml
name: README check
on: pull_request
permissions: { contents: read, pull-requests: write }
jobs:
  readme:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: tanmayai23/README-Editor-skill@v1
        with: { min-score: 80 }
```

To check several files, list them in `path`, separated by spaces or newlines:

```yaml
      - uses: tanmayai23/README-Editor-skill@v1
        with:
          path: |
            README.md
            packages/cli/README.md
          min-accuracy: 90
```

## Inputs

| Input | Default | What it does |
|---|---|---|
| `path` | `README.md` | README file(s) to check, separated by spaces or newlines |
| `repo-root` | `.` | Repository root the README describes |
| `min-score` | `0` | Fails the step when any README scores below this. `0` never fails |
| `min-accuracy` | `0` | Fails the step when the percent of checked claims found in the code is below this (`0.9` also means 90%). `0` never fails |
| `comment` | `true` | Posts or updates the PR comment on `pull_request` / `pull_request_target` events |
| `github-token` | `${{ github.token }}` | Token used to comment. Needs `pull-requests: write` |

## Outputs

| Output | Meaning |
|---|---|
| `score` | Score from 0 to 100. With several files, this is the lowest one |
| `grade` | Letter grade from A to F for that score |
| `accuracy` | Lowest percent of claims that match the code. Empty when nothing was checked |
| `report` | Path to the Markdown report file |

The same report is also written to the job summary.

## Pull requests from forks

On pull requests from forks, GitHub gives the workflow a read-only token, so the action can't comment. In that case it logs a warning and the report still shows up in the job summary. Score and accuracy thresholds are still enforced. A failed comment never fails the job. You can use `pull_request_target` to comment on fork PRs, but only if you understand [the risks](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/). This action never runs code from the PR, but other steps in the job might.

## Run it locally

```bash
python action/report.py README.md --repo . --no-comment
```

## Sample comment

> ## README report
>
> ### `README.md` · 45/100 · grade F
>
> `█████████░░░░░░░░░░░` **45**/100
>
> **Accuracy:** 1/2 commands, env vars and paths in the README match the code (50%).
>
> > **Check failed:** score 45 is below the minimum of 80.
>
> | Category | Score | |
> |---|---:|---|
> | getting-started | 13/25 | `█████░░░░░` |
> | community | 3/15 | `██░░░░░░░░` |
> | quality | 3.6/20 | `██░░░░░░░░` |
>
> <details><summary>4 errors, 6 warnings</summary>
>
> - **ERROR** `community` no License section
> - **ERROR** `accessibility` image without alt text: screenshot.png (line 10)
> - **WARN** `quality` filler/marketing phrase 'blazing fast' — replace with a concrete fact (line 3)
>
> </details>
>
> <details><summary>1 claim not found in the code</summary>
>
> | Line | Kind | Claim | Evidence |
> |---:|---|---|---|
> | 8 | script | `npm run serve` | package.json scripts: dev, build, start, test |
>
> </details>
