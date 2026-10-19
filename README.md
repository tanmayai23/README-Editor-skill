<a id="top"></a>

<a href="#readme-forge">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/header-dark.svg">
    <img alt="readme-forge: Your code is the source of truth. Your README should be too." src=".github/assets/header-light.svg" width="100%">
  </picture>
</a>

<p align="center"><b>A Claude skill that writes READMEs from your code, then checks every command, env var and path in them against the repo.</b></p>

<p align="center">
  <a href="https://github.com/tanmayai23/README-Editor-skill/actions/workflows/ci.yml"><img alt="CI status" src="https://github.com/tanmayai23/README-Editor-skill/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/tanmayai23/README-Editor-skill/releases"><img alt="Latest release" src="https://img.shields.io/github/v/release/tanmayai23/README-Editor-skill?color=19C3EC"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-19C3EC"></a>
</p>

<p align="center"><sub>Python standard library only · Works in Claude Code, claude.ai and Claude Desktop</sub></p>

<p align="center"><a href="#why">Why</a> · <a href="#quickstart">Quickstart</a> · <a href="#check-readmes-in-ci">CI</a> · <a href="#what-it-does">What it does</a> · <a href="#scripts">Scripts</a> · <a href="#optional-design-and-profiles">Design</a> · <a href="#faq">FAQ</a> · <a href="#roadmap">Roadmap</a></p>

## Why

A README generator that guesses is worse than none: a wrong install command costs a new user more than a missing one. readme-forge reads the repo first, writes only what it can point to in a file, and leaves a `TODO` where it can't. Then `verify_readme.py` checks the result claim by claim:

This is its real output on a test fixture: a pnpm app whose README was seeded with five mistakes.

```text
$ python readme-forge/scripts/verify_readme.py README.bad.md --repo tests/fixtures/verify/node-app
✓    6  command         npm install  [package.json exists]
✗    6  package_manager npm  [repo uses pnpm (pnpm-lock.yaml), not npm]
✗    7  script          pnpm run deploy  [no 'deploy' script in package.json (scripts: dev, test)]
✓    7  package_manager pnpm  [pnpm-lock.yaml matches pnpm]
✗    8  env_var         REDIS_URL  [not referenced in any code, config or .env file]
✗    9  command         docker compose up worker  [no service worker in docker-compose.yml (services: api, db)]
✗   12  path            docs/setup.md  [no docs/setup.md in the repo]
claims: 7 checked · 2 verified · 5 not found · 0 unverifiable · 1 generic · accuracy 28.6%
```

Every `✗` is something the README says that the code doesn't have. The skill doesn't finish until there are none.

Try it on the sample app in this repo, no Claude account needed:

```bash
git clone https://github.com/tanmayai23/README-Editor-skill.git
cd README-Editor-skill
python readme-forge/scripts/verify_readme.py demo/sample-app/README.after.md --repo demo/sample-app   # 12 of 12 claims match
python readme-forge/scripts/score_readme.py demo/sample-app/README.before.md --repo demo/sample-app   # 43/100, grade F
python readme-forge/scripts/score_readme.py demo/sample-app/README.after.md --repo demo/sample-app    # 95/100, grade A
```

<details>
<summary><b>Watch the demo</b> (a 43/100 README rewritten by one command)</summary>
<br>

<p align="center">
  <img src="demo/readme-forge-demo.gif" width="820" alt="Demo: a README scoring 43/100 (grade F) is rewritten by one /readme-forge command in Claude Code. The new README has a quickstart, an API table and an architecture diagram, and scores 95/100 (grade A).">
</p>

<a href="demo/readme-forge-cinematic.mp4">Full 34-second demo in HD</a>. The scorer is this repo's own, so treat the score as a checklist, not proof; the claim check is the part you can audit line by line.

</details>

## Quickstart

Install the skill once from any terminal. It then works in every project:

```bash
claude plugin install readme-forge --marketplace tanmayai23/README-Editor-skill
```

Then, in Claude Code:

```text
/readme-forge write a README for this repo
```

You can also just say "improve my README" or "is my README accurate?". From a script: `claude -p "/readme-forge audit README.md and fix every error"`.

**claude.ai or Claude Desktop:** download `readme-forge.zip` from the [latest release](https://github.com/tanmayai23/README-Editor-skill/releases/latest) and upload it under **Settings → Capabilities → Skills**.

**No Claude at all:** the scripts run on their own as a free README linter and fact checker. See [Scripts](#scripts).

<details>
<summary>Older Claude Code, project-only install, updating, or manual install</summary>

Older versions add the marketplace first:

```bash
claude plugin marketplace add tanmayai23/README-Editor-skill
claude plugin install readme-forge@readme-forge
```

Add `--scope project` to install for one project and share it with your team. Update with `claude plugin marketplace update readme-forge`, then `claude plugin update readme-forge@readme-forge`. To install by hand, copy the `readme-forge` folder to `~/.claude/skills/readme-forge`.

</details>

## Check READMEs in CI

The repo is also a GitHub Action. It scores and fact-checks the README on every pull request and keeps one comment up to date:

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
        with: { min-score: 80, min-accuracy: 100 }
```

Inputs, outputs and a sample comment are in [action/README.md](action/README.md).

## What it does

| | |
|---|---|
| **Facts** | `analyze_repo.py` reads manifests, lockfiles, scripts, env vars, Docker, CI and routes for 15 ecosystems: Node, Python, Rust, Go, JVM, Ruby, PHP, Dart, Elixir, .NET, C/C++, Deno, Swift, Zig and Haskell. Each one has a fixture and a unit test. |
| **Claim check** | `verify_readme.py` checks commands, package-manager scripts, CLI flags, env vars and paths against the repo. |
| **Architecture** | `import_graph.py` drafts a Mermaid diagram from real imports in Python, JS/TS, Go and Rust. |
| **Score and drift** | `score_readme.py` grades structure, accessibility, links and drift from 0 to 100. |
| **Platforms** | GitHub READMEs, Hugging Face model/dataset/Space cards with validated YAML, and PyPI/npm/GitLab ports. |
| **Companion docs** | CONTRIBUTING, SECURITY, Code of Conduct, CITATION.cff, issue and PR templates. |

```mermaid
flowchart LR
    accTitle: readme-forge workflow
    accDescr: Scripts read the repository, Claude writes the README from those facts, then the verifier and scorer check it in a loop.
    repo[("Your repo")] --> facts["analyze_repo.py<br/>stack, commands, env, CI"]
    repo --> imports["import_graph.py<br/>architecture draft"]
    facts --> claude["Claude + references"]
    imports --> claude
    claude --> readme["README.md"]
    readme --> verify["verify_readme.py<br/>every claim vs the repo"]
    readme --> score["score_readme.py<br/>score, lint, drift"]
    verify -->|"fix or TODO each miss"| claude
    score -->|"fix until it passes"| claude
```

## Scripts

| Script | What it does | Example |
|---|---|---|
| `analyze_repo.py` | Prints the repo's facts as JSON | `python readme-forge/scripts/analyze_repo.py . --compact` |
| `verify_readme.py` | Checks every claim in a README against the repo | `python readme-forge/scripts/verify_readme.py README.md --repo .` |
| `score_readme.py` | Scores a README 0–100, lints it and checks drift | `python readme-forge/scripts/score_readme.py README.md --repo . --min 85` |
| `import_graph.py` | Draws a Mermaid architecture draft from real imports | `python readme-forge/scripts/import_graph.py . --mermaid` |
| `check_links.py` | Finds dead links, broken badges and widgets that return error cards | `python readme-forge/scripts/check_links.py README.md` |

This README passes its own checks: [CI](.github/workflows/ci.yml) runs `verify_readme.py --min-accuracy 100` and `score_readme.py --min 85` on it, plus the unit tests in `tests/`.

## Optional: design and profiles

Banners, CTA buttons and GitHub profile READMEs live in a separate plugin, so the core skill stays about accuracy:

```bash
claude plugin install readme-forge-design --marketplace tanmayai23/README-Editor-skill
```

It generates self-contained animated SVG headers in 20 styles. The newest four rebuild the look of WebGL shader scenes in plain SVG and CSS, so GitHub can render them: a spinning vortex, a light beam racing around the edge, voronoi glass and RGB-split blinds. The header above is `--style vortex` with the logo in its eye.

<table>
<tr>
<td width="50%"><picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge-design/assets/banners/beam-dark.svg"><img alt="beam banner style: a light beam racing around the edge over a nebula glow" src="readme-forge-design/assets/banners/beam-light.svg" width="100%"></picture></td>
<td width="50%"><picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge-design/assets/banners/prism-dark.svg"><img alt="prism banner style: RGB-split light blinds with a swipe reveal" src="readme-forge-design/assets/banners/prism-light.svg" width="100%"></picture></td>
</tr>
</table>

It also has 19 profile README archetypes with tested widgets and 6 profile Actions. See the [design README](readme-forge-design/README.md) for every style.

## Troubleshooting

<details>
<summary>Install and run problems</summary>

| Problem | Fix |
|---|---|
| `/plugin isn't available in this environment` | Run `claude plugin install readme-forge --marketplace tanmayai23/README-Editor-skill` in a normal terminal, then open a new chat |
| `Unknown command: /readme-forge` after installing | Start a new Claude Code session. Plugins load at startup |
| Two `readme-forge` skills, or the wrong one runs | You have the plugin and a manual copy. Use `/readme-forge:readme-forge`, or delete `~/.claude/skills/readme-forge` |
| `python: command not found` | Install Python 3.8+. On macOS and Linux, tell Claude to use `python3` |
| Garbled `█` bars in Windows PowerShell | Run `[Console]::OutputEncoding = [Text.Encoding]::UTF8` once, or use Windows Terminal |

</details>

Something else? [Open an issue](https://github.com/tanmayai23/README-Editor-skill/issues/new?template=bug_report.yml) with your OS, Claude Code version (`claude --version`) and the error.

## FAQ

<details>
<summary><b>Does it send my code anywhere?</b></summary>

The scripts only read files on your machine. Only `check_links.py` uses the network, and only for the URLs already in your README. What Claude sees is governed by your normal Claude Code settings.
</details>

<details>
<summary><b>What can't the claim check verify?</b></summary>

It works offline, so it can't tell whether `pip install NAME` resolves on PyPI or whether a command succeeds at runtime. Those claims are reported as unverifiable, never as correct. Commands written in plain prose, outside code, aren't extracted.
</details>

<details>
<summary><b>What if it can't find something, like the install command?</b></summary>

It leaves a `TODO` in the README and lists every TODO back to you.
</details>

## Roadmap

- [x] Project and Hugging Face READMEs grounded in code, with tests for 15 ecosystems
- [x] Claim-by-claim verification of commands, flags, env vars and paths
- [x] GitHub Action that comments the score and claim check on pull requests ([#1](https://github.com/tanmayai23/README-Editor-skill/issues/1))
- [ ] Published benchmark against Claude without the skill on 20 pinned third-party repos ([#12](https://github.com/tanmayai23/README-Editor-skill/issues/12))
- [ ] Architecture diagrams for Java/Kotlin ([#3](https://github.com/tanmayai23/README-Editor-skill/issues/3)), C# ([#4](https://github.com/tanmayai23/README-Editor-skill/issues/4)), PHP and Ruby ([#5](https://github.com/tanmayai23/README-Editor-skill/issues/5))
- [ ] Check documented API routes against the code ([#6](https://github.com/tanmayai23/README-Editor-skill/issues/6))
- [ ] Mermaid pre-rendering for PyPI, npm and Hugging Face ([#7](https://github.com/tanmayai23/README-Editor-skill/issues/7))

See all [open issues](https://github.com/tanmayai23/README-Editor-skill/issues), or start with a [`good first issue`](https://github.com/tanmayai23/README-Editor-skill/issues?q=is%3Aopen+label%3A%22good+first+issue%22).

## Contributing

Issues and pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first; `python -m unittest discover -s tests` runs the same tests as CI. Using readme-forge or the Action in your own repo? [Tell us in Discussions](https://github.com/tanmayai23/README-Editor-skill/discussions); real-world reports are the most useful feedback we get.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues privately as described in [SECURITY.md](SECURITY.md).

### Contributors

Code, design, docs, ideas and bug reports all count ([emoji key](https://allcontributors.org/emoji-key/)).

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/tanmayai23"><img src="https://avatars.githubusercontent.com/u/212147996?v=4?s=100" width="100px;" alt="Tanmay kala"/><br /><sub><b>Tanmay kala</b></sub></a><br /><a href="https://github.com/tanmayai23/README-Editor-skill/commits?author=tanmayai23" title="Code">💻</a> <a href="https://github.com/tanmayai23/README-Editor-skill/tree/main/readme-forge/assets" title="Design">🎨</a> <a href="https://github.com/tanmayai23/README-Editor-skill/commits?author=tanmayai23" title="Documentation">📖</a> <a href="https://github.com/tanmayai23/README-Editor-skill/tree/main/.github/workflows" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/tanmayai23/README-Editor-skill/pulls?q=is%3Apr+reviewed-by%3Atanmayai23" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Sultanast01"><img src="https://avatars.githubusercontent.com/u/173893361?v=4?s=100" width="100px;" alt="Sultanast01"/><br /><sub><b>Sultanast01</b></sub></a><br /><a href="https://github.com/tanmayai23/README-Editor-skill/pull/17" title="Code">💻</a> <a href="https://github.com/tanmayai23/README-Editor-skill/pull/15" title="Design">🎨</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## License

Distributed under the MIT License. See [LICENSE](LICENSE).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/divider-dark.svg">
  <img alt="Section divider" src=".github/assets/divider-light.svg" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/footer-dark.svg">
  <img alt="Made with readme-forge" src=".github/assets/footer-light.svg" width="100%">
</picture>

<p align="right"><a href="#top">Back to top ↑</a></p>
