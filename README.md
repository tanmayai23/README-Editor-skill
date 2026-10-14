<a id="top"></a>
<a href="#readme-forge">
  <picture><source media="(prefers-color-scheme: dark)" srcset=".github/assets/header-dark.svg"><img alt="readme-forge logo, a ghost inside a circuit chip, above the title readme-forge and the line: Your code is the source of truth. Your README should be too." src=".github/assets/header-light.svg" width="100%"></picture>
</a>

<p align="center"><b>A Claude skill that writes, designs, scores and fixes READMEs using facts from your actual code.</b></p>

<p align="center">
  <a href="#quickstart"><picture><source media="(prefers-color-scheme: dark)" srcset=".github/assets/cta-primary-dark.svg"><img alt="Get started" src=".github/assets/cta-primary-light.svg" height="44"></picture></a>
  &nbsp;
  <a href="#banner-gallery"><picture><source media="(prefers-color-scheme: dark)" srcset=".github/assets/cta-secondary-dark.svg"><img alt="Banner gallery" src=".github/assets/cta-secondary-light.svg" height="44"></picture></a>
</p>

<p align="center"><sub>MIT licensed · Python standard library only · Works in Claude Code, claude.ai and Claude Desktop</sub></p>

<p align="center">
  <a href="https://github.com/tanmayai23/README-Editor-skill/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/tanmayai23/README-Editor-skill?style=flat&color=13A7D5&logo=github"></a>
  <a href="https://github.com/tanmayai23/README-Editor-skill/actions/workflows/ci.yml"><img alt="CI status" src="https://github.com/tanmayai23/README-Editor-skill/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/tanmayai23/README-Editor-skill/releases"><img alt="Latest release" src="https://img.shields.io/github/v/release/tanmayai23/README-Editor-skill?color=13A7D5"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-13A7D5"></a>
  <img alt="Claude Agent Skill" src="https://img.shields.io/badge/Claude-Agent%20Skill-13A7D5">
  <img alt="Scripts: Python 3.8+, standard library only" src="https://img.shields.io/badge/python-3.8%2B%20stdlib-13A7D5?logo=python&logoColor=white">
</p>

<br>

<p align="center">
  <img src="demo/readme-forge-demo.gif" width="820" alt="Demo: a README scoring 43/100 (grade F) is rewritten by one /readme-forge command in Claude Code. The new README has a quickstart, an API table and an architecture diagram, and scores 95/100 (grade A).">
</p>

<!-- Inline video player: edit this README on github.com, drag demo/readme-forge-cinematic.mp4 into the editor,
     and put the https://github.com/user-attachments/assets/… link GitHub inserts on its own line here. -->
<p align="center"><a href="demo/readme-forge-cinematic.mp4"><b>▶ Watch the full 34-second demo in HD</b></a> · <sub>43/100 → 95/100 on a real sample app, with one command</sub></p>

<details>
<summary><b>Reproduce the 43 → 95 demo yourself</b> (no Claude account needed)</summary>

```bash
git clone https://github.com/tanmayai23/README-Editor-skill.git
cd README-Editor-skill/demo/sample-app
cp README.before.md README.md && python ../../readme-forge/scripts/score_readme.py README.md --repo .   # 43/100, grade F
cp README.after.md README.md && python ../../readme-forge/scripts/score_readme.py README.md --repo .    # 95/100, grade A
```

`README.after.md` is the README the skill wrote for this sample app. The scorer is plain Python, so you can run it on your own README the same way.

</details>

<details>
<summary><b>Contents</b></summary>

- [Why](#why)
- [Quickstart](#quickstart)
- [Banner gallery](#banner-gallery)
- [What you can ask](#what-you-can-ask)
- [Templates included](#templates-included)
- [How it works](#how-it-works)
- [Scripts](#scripts)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

</details>

## Why

Most README generators fill one template. Most profile galleries ask you to copy someone else's file. Neither reads your code, and neither designs anything. readme-forge does both:

| | Other tools | readme-forge |
|---|---|---|
| **Facts** | Typed in by hand, or read from `package.json` only | Detects 15+ ecosystems, scripts, env vars, Docker, CI, routes; never invents commands |
| **Visuals** | A logo if you have one | Mermaid architecture **from real imports**, plus 16 animated banner styles and CTA buttons with dark/light variants |
| **Widgets** | Hard-coded public URLs (some now return HTTP 402) | Tested endpoints, self-hosted SVGs that can't rate-limit, reliability tiers |
| **Quality** | None | A 0–100 score and linter: structure, accessibility, dead links, drift, design |
| **Platforms** | GitHub only | GitHub, Hugging Face cards, PyPI, npm, GitLab |

## Quickstart

**Claude Code (recommended).** Install it once from any terminal (PowerShell, Git Bash, macOS or Linux). It then works in every project:

```bash
claude plugin install readme-forge --marketplace tanmayai23/README-Editor-skill
```

Or type it inside a Claude Code chat in the terminal (Claude Code 2.1.275 or later):

```text
/plugin install readme-forge --marketplace tanmayai23/README-Editor-skill
```

> [!TIP]
> **Seeing "/plugin isn't available in this environment"?** Some chat panels, such as the VS Code extension, don't support the `/plugin` command. Run the `claude plugin install …` line above in a normal terminal instead, then start a new chat. The skill is available everywhere after that, including VS Code.

<details>
<summary>Older Claude Code, project-only install, updating, or manual install</summary>

Older versions add the marketplace first:

```bash
claude plugin marketplace add tanmayai23/README-Editor-skill
claude plugin install readme-forge@readme-forge
```

To install for one project only, and share it with your team through `.claude/settings.json`, add `--scope project`.

Get new versions with:

```bash
claude plugin marketplace update readme-forge
claude plugin update readme-forge@readme-forge
```

Or copy the skill folder yourself:

```bash
git clone https://github.com/tanmayai23/README-Editor-skill.git
cp -r README-Editor-skill/readme-forge ~/.claude/skills/readme-forge
```

</details>

Then open Claude Code in any project and run:

```text
/readme-forge write a README for this repo, with a header and footer
```

Plugin skills are namespaced. If another command already uses the name, type `/readme-forge:readme-forge` instead. You can also skip the command and say "improve my README"; Claude loads the skill on its own.

**From the terminal, without a chat:**

```bash
claude -p "/readme-forge audit README.md and fix every error"
```

**claude.ai or Claude Desktop:** download `readme-forge.zip` from the [latest release](https://github.com/tanmayai23/README-Editor-skill/releases/latest) and upload it under **Settings → Capabilities → Skills**.

**No Claude at all:** the scripts work on their own as a free README linter. See [Scripts](#scripts).

## Banner gallery

Inspired by ShaderGradient, Supahero, Call to Inspiration, dark-design galleries and Dribbble, then rebuilt for what GitHub can render. Every banner is a **self-contained animated SVG** that you commit to your repo, so there are no external services, rate limits or broken images. Each comes in a dark and a light variant (switch your GitHub theme to see both), shows a complete first frame, and stops moving for visitors who turn on reduce motion.

<table>
<tr>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/shader-dark.svg"><img alt="shader banner style: grainy 3D colour field (ShaderGradient)" src="readme-forge/assets/banners/shader-light.svg" width="100%"></picture>

<b><code>--style shader</code></b><br><sub>grainy 3D colour field (ShaderGradient)</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/spotlight-dark.svg"><img alt="spotlight banner style: landing-page hero: grid, beam, pill" src="readme-forge/assets/banners/spotlight-light.svg" width="100%"></picture>

<b><code>--style spotlight</code></b><br><sub>landing-page hero: grid, beam, pill</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/ribbon-dark.svg"><img alt="ribbon banner style: twisting silk strands, 3D depth" src="readme-forge/assets/banners/ribbon-light.svg" width="100%"></picture>

<b><code>--style ribbon</code></b><br><sub>twisting silk strands, 3D depth</sub>

</td>
</tr>
<tr>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/aurora-dark.svg"><img alt="aurora banner style: drifting mesh-gradient light" src="readme-forge/assets/banners/aurora-light.svg" width="100%"></picture>

<b><code>--style aurora</code></b><br><sub>drifting mesh-gradient light</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/synthwave-dark.svg"><img alt="synthwave banner style: 3D perspective grid + striped sun" src="readme-forge/assets/banners/synthwave-light.svg" width="100%"></picture>

<b><code>--style synthwave</code></b><br><sub>3D perspective grid + striped sun</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/isometric-dark.svg"><img alt="isometric banner style: 3D floating isometric cubes" src="readme-forge/assets/banners/isometric-light.svg" width="100%"></picture>

<b><code>--style isometric</code></b><br><sub>3D floating isometric cubes</sub>

</td>
</tr>
<tr>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/orbit-dark.svg"><img alt="orbit banner style: 3D tilted orbits, revolving planets" src="readme-forge/assets/banners/orbit-light.svg" width="100%"></picture>

<b><code>--style orbit</code></b><br><sub>3D tilted orbits, revolving planets</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/glass-dark.svg"><img alt="glass banner style: frosted glass over moving colour" src="readme-forge/assets/banners/glass-light.svg" width="100%"></picture>

<b><code>--style glass</code></b><br><sub>frosted glass over moving colour</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/terminal-dark.svg"><img alt="terminal banner style: code window that retypes the title" src="readme-forge/assets/banners/terminal-light.svg" width="100%"></picture>

<b><code>--style terminal</code></b><br><sub>code window that retypes the title</sub>

</td>
</tr>
<tr>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/neon-dark.svg"><img alt="neon banner style: glowing neon outline" src="readme-forge/assets/banners/neon-light.svg" width="100%"></picture>

<b><code>--style neon</code></b><br><sub>glowing neon outline</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/wave-dark.svg"><img alt="wave banner style: layered animated waves" src="readme-forge/assets/banners/wave-light.svg" width="100%"></picture>

<b><code>--style wave</code></b><br><sub>layered animated waves</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/blueprint-dark.svg"><img alt="blueprint banner style: engineering drawing that redraws" src="readme-forge/assets/banners/blueprint-light.svg" width="100%"></picture>

<b><code>--style blueprint</code></b><br><sub>engineering drawing that redraws</sub>

</td>
</tr>
<tr>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/constellation-dark.svg"><img alt="constellation banner style: twinkling particle network" src="readme-forge/assets/banners/constellation-light.svg" width="100%"></picture>

<b><code>--style constellation</code></b><br><sub>twinkling particle network</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/minimal-dark.svg"><img alt="minimal banner style: clean type, one sweeping accent" src="readme-forge/assets/banners/minimal-light.svg" width="100%"></picture>

<b><code>--style minimal</code></b><br><sub>clean type, one sweeping accent</sub>

</td>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/bold-dark.svg"><img alt="bold banner style: oversized type, moving gradient" src="readme-forge/assets/banners/bold-light.svg" width="100%"></picture>

<b><code>--style bold</code></b><br><sub>oversized type, moving gradient</sub>

</td>
</tr>
<tr>
<td width="33%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/pulse-dark.svg"><img alt="pulse banner style: soft rings breathing behind the title" src="readme-forge/assets/banners/pulse-light.svg" width="100%"></picture>

<b><code>--style pulse</code></b><br><sub>soft rings breathing behind the title</sub>

</td>
<td width="33%" valign="top"></td>
<td width="33%" valign="top"></td>
</tr>
</table>

```bash
python readme-forge/scripts/make_banner.py --style isometric --palette ocean --title "kubeforge" --subtitle "Clusters in one command" --out .github/assets
python readme-forge/scripts/make_banner.py --style spotlight --logo logo.png --palette ghost --title "my-app" --height 400 --out .github/assets
python readme-forge/scripts/make_banner.py --kind footer --style wave --title "Thanks for visiting" --out .github/assets
```

<details>
<summary><b>ShaderGradient presets, CTA buttons, footers and dividers</b></summary>
<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/footer-wave-dark.svg"><img alt="Wave footer: Thanks for reading" src="readme-forge/assets/banners/footer-wave-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/footer-minimal-dark.svg"><img alt="Minimal footer with an accent rule: Made with readme-forge" src="readme-forge/assets/banners/footer-minimal-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/divider-aurora-dark.svg"><img alt="Animated gradient section divider" src="readme-forge/assets/banners/divider-aurora-light.svg" width="100%"></picture>

**ShaderGradient presets** (`--style shader --palette …`):

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/presets/shader-halo-dark.svg"><img alt="Shader banner with the halo preset" src="readme-forge/assets/banners/presets/shader-halo-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/presets/shader-pensive-dark.svg"><img alt="Shader banner with the pensive preset" src="readme-forge/assets/banners/presets/shader-pensive-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/presets/shader-interstella-dark.svg"><img alt="Shader banner with the interstella preset" src="readme-forge/assets/banners/presets/shader-interstella-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/presets/shader-universe-dark.svg"><img alt="Shader banner with the universe preset" src="readme-forge/assets/banners/presets/shader-universe-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/presets/shader-mandarin-dark.svg"><img alt="Shader banner with the mandarin preset" src="readme-forge/assets/banners/presets/shader-mandarin-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/presets/shader-nighty-dark.svg"><img alt="Shader banner with the nighty preset" src="readme-forge/assets/banners/presets/shader-nighty-light.svg" width="100%"></picture>

**CTA buttons** (`--kind button --variant primary|secondary`), clickable because each one is an image inside a link:

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/button-primary-dark.svg"><img alt="Get started" src="readme-forge/assets/banners/button-primary-light.svg" height="44"></picture> <picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/button-secondary-dark.svg"><img alt="Read the docs" src="readme-forge/assets/banners/button-secondary-light.svg" height="44"></picture>

Palettes: `ember` · `ocean` · `violet` · `mint` · `sunset` · `mono` · `cyber` · dark-design `midnight` · `carbon` · `obsidian` · ShaderGradient `halo` · `pensive` · `interstella` · `universe` · `mandarin` · `nighty`, or pass any brand colour with `--accent "#HEX"`.

</details>

## What you can ask

| You say | You get |
|---|---|
| "Write a README for this repo" | Project README from code facts, a designed header and footer, and an architecture diagram |
| "Make my GitHub profile README, creative style" | A profile from 11 archetypes with a hero banner, working widgets and an optional 3D contribution calendar |
| "Review my README and fix it" | A score, drift report and ranked fixes, then a rewrite in your voice |
| "Give my README a better header" | 2–3 banner options in your brand colour, ready to paste |
| "Create a model card for this fine-tune" | A Hugging Face card with validated YAML |
| "Make this repo open-source ready" | README + CONTRIBUTING, SECURITY, Code of Conduct, issue/PR templates |
| "Make a PyPI version of my README" | A copy with absolute image links and no GitHub-only syntax, so it renders on PyPI and npm |

## Templates included

| Kind | Templates |
|---|---|
| **Profile READMEs** (11) | `minimal` · `creative` · `stats-dashboard` · `code-mode` · `badges-wall` · `retro` · `student` · `data-scientist` · `oss-maintainer` · `actions-dynamic` · `org-profile` |
| **Project READMEs** (7) | `api` · `cli` · `library` · `webapp` · `ml-project` · `monorepo` · `minimal` |
| **Hugging Face** (3) | model card · dataset card · Space README, each with validated YAML frontmatter |
| **Design blocks** (6) | centered header · profile header · landing-page hero · CTA section · SVG footer · quiet footer |
| **Companion docs** | CONTRIBUTING · CODE_OF_CONDUCT · SECURITY · SUPPORT · CHANGELOG · CITATION.cff · FUNDING · issue forms · PR template |
| **Profile Actions** (5) | contribution snake · latest blog posts · WakaTime stats · metrics · 3D contribution calendar |

Every widget URL in the profile templates was checked with `check_links.py`. Services that now fail, such as the public trophy and activity-graph hosts that return HTTP 402, are left out or replaced by self-hosted Actions.

## How it works

```mermaid
flowchart LR
    accTitle: readme-forge workflow
    accDescr: Scripts read the repository, then Claude writes and designs the README from those facts, then the scorer checks it in a loop.
    repo[("Your repo")] --> facts["analyze_repo.py<br/>stack, commands, env, CI"]
    repo --> imports["import_graph.py<br/>architecture draft"]
    facts --> claude["Claude + references"]
    imports --> claude
    claude --> design["make_banner.py<br/>header, footer, dividers"]
    claude --> readme["README.md"]
    design --> readme
    readme --> score["score_readme.py<br/>score, lint, drift, design"]
    score -->|"fix until it passes"| claude
```

Every script runs on its own with Python 3.8+ and no dependencies. See the [skill docs](readme-forge/README.md).

## Scripts

| Script | What it does | Example |
|---|---|---|
| `analyze_repo.py` | Prints the repo's facts as JSON: languages, package manager, scripts, env vars, Docker, CI, license, Hugging Face files | `python readme-forge/scripts/analyze_repo.py . --compact` |
| `import_graph.py` | Draws a Mermaid architecture draft from real imports (Python, JS/TS, Go, Rust) | `python readme-forge/scripts/import_graph.py . --mermaid` |
| `score_readme.py` | Scores a README 0–100, lints it and checks it against the code | `python readme-forge/scripts/score_readme.py README.md --repo . --min 85` |
| `check_links.py` | Finds dead links, broken badges and widgets that return error cards | `python readme-forge/scripts/check_links.py README.md` |
| `make_banner.py` | Generates animated SVG headers, footers, dividers and buttons | `python readme-forge/scripts/make_banner.py --list` |

Use `score_readme.py --min 85` in CI to stop a README from getting worse. This repo's own [CI](.github/workflows/ci.yml) does exactly that.

## Troubleshooting

| Problem | Fix |
|---|---|
| `/plugin isn't available in this environment` | Run `claude plugin install readme-forge --marketplace tanmayai23/README-Editor-skill` in a normal terminal, then open a new chat |
| `Unknown command: /readme-forge` after installing | Start a new Claude Code session. Plugins load at startup |
| Two `readme-forge` skills, or the wrong one runs | You have both the plugin and a manual copy. Use `/readme-forge:readme-forge`, or delete `~/.claude/skills/readme-forge` |
| `python: command not found` | Install Python 3.8+. On macOS and Linux, tell Claude to use `python3`. The skill accepts either |
| Old behaviour after an update | `claude plugin marketplace update readme-forge`, then `claude plugin update readme-forge@readme-forge`, then restart |
| Garbled `█` bars in Windows PowerShell | Run `[Console]::OutputEncoding = [Text.Encoding]::UTF8` once, or use Windows Terminal |
| Widget images broken on your profile | Run `python readme-forge/scripts/check_links.py README.md`, then [report the widget](https://github.com/tanmayai23/README-Editor-skill/issues/new?template=broken_widget.yml) |

Something else? [Open an issue](https://github.com/tanmayai23/README-Editor-skill/issues/new?template=bug_report.yml) with your OS, Claude Code version (`claude --version`) and the error.

## FAQ

<details>
<summary><b>Does it send my code anywhere?</b></summary>

The scripts only read files on your machine. Only `check_links.py` uses the network, and only for the URLs already in your README. What Claude sees is governed by your normal Claude Code settings.
</details>

<details>
<summary><b>What if it can't find something, like the install command?</b></summary>

It leaves a `TODO` in the README and lists every TODO back to you. It never makes up commands, versions or benchmark numbers.
</details>

<details>
<summary><b>Will the animated banners work on PyPI, npm or Hugging Face?</b></summary>

GitHub renders them, including dark and light variants. Other platforms ignore `<picture>`, so ask for "a PyPI version" and the skill switches to absolute URLs and single images.
</details>

<details>
<summary><b>Which languages get architecture diagrams?</b></summary>

Python, JavaScript/TypeScript, Go and Rust. For other languages the skill still writes the README and sketches the diagram from the folder layout, marked as a draft.
</details>

## Roadmap

- [x] Project, profile and Hugging Face READMEs grounded in code
- [x] 0–100 scorer with drift detection
- [x] 16 animated banner styles with dark/light variants
- [x] Claude Code plugin install
- [ ] GitHub Action that comments the README score on pull requests ([#1](https://github.com/tanmayai23/README-Editor-skill/issues/1))
- [ ] Architecture diagrams for Java/Kotlin ([#3](https://github.com/tanmayai23/README-Editor-skill/issues/3)), C# ([#4](https://github.com/tanmayai23/README-Editor-skill/issues/4)), PHP and Ruby ([#5](https://github.com/tanmayai23/README-Editor-skill/issues/5))
- [ ] Check that documented CLI flags and API routes exist in the code ([#6](https://github.com/tanmayai23/README-Editor-skill/issues/6))
- [ ] More banner styles from the community ([#10](https://github.com/tanmayai23/README-Editor-skill/issues/10))
- [ ] Weekly automatic widget health check ([#2](https://github.com/tanmayai23/README-Editor-skill/issues/2))
- [ ] Mermaid pre-rendering for PyPI, npm and Hugging Face ([#7](https://github.com/tanmayai23/README-Editor-skill/issues/7))

See all [open issues](https://github.com/tanmayai23/README-Editor-skill/issues), or start with a [`good first issue`](https://github.com/tanmayai23/README-Editor-skill/issues?q=is%3Aopen+label%3A%22good+first+issue%22).

<div align="center">

### Start writing READMEs people actually read

One command reads your code, designs the page and checks it.

<a href="#quickstart"><picture><source media="(prefers-color-scheme: dark)" srcset=".github/assets/cta-primary-dark.svg"><img alt="Get started" src=".github/assets/cta-primary-light.svg" height="44"></picture></a>

<sub>Free and open source · 2-minute setup</sub>

</div>

## Contributing

Issues and pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. Good places to start:

- **Report a broken widget** with the [widget form](https://github.com/tanmayai23/README-Editor-skill/issues/new?template=broken_widget.yml). Widget hosts change often, and this keeps the profile templates working.
- **Add a banner style.** Include both the dark and light renders and keep the first frame complete.
- **Share a README you made** in [Discussions](https://github.com/tanmayai23/README-Editor-skill/discussions).

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues privately as described in [SECURITY.md](SECURITY.md).

### Contributors

Thanks to everyone who has helped build readme-forge. Code, design, docs, ideas and bug reports all count ([emoji key](https://allcontributors.org/emoji-key/)).

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

### Star history

<a href="https://star-history.com/#tanmayai23/README-Editor-skill&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=tanmayai23/README-Editor-skill&type=Date&theme=dark">
    <img alt="Star history chart for readme-forge" src="https://api.star-history.com/svg?repos=tanmayai23/README-Editor-skill&type=Date" width="600">
  </picture>
</a>

## Acknowledgements

Built after studying [readme-md-generator](https://github.com/kefranabg/readme-md-generator), [The Documentation Compendium](https://github.com/race2infinity/The-Documentation-Compendium), [awesome-github-profile-readme](https://github.com/abhisheknaiidu/awesome-github-profile-readme), [awesome-github-profile-readme-templates](https://github.com/durgeshsamariya/awesome-github-profile-readme-templates) and [Best-README-Template](https://github.com/othneildrew/Best-README-Template). Widgets by [shields.io](https://shields.io), [github-readme-stats](https://github.com/anuraghazra/github-readme-stats), [readme-typing-svg](https://github.com/DenverCoder1/readme-typing-svg) and [skill-icons](https://github.com/tandpfun/skill-icons).

## License

Distributed under the MIT License. See [LICENSE](LICENSE).

---

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/footer-dark.svg">
  <img alt="Made with readme-forge" src=".github/assets/footer-light.svg" width="100%">
</picture>

<p align="right"><a href="#top">Back to top ↑</a></p>
