<a id="top"></a>
<a href="#readme-forge">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/header-dark.svg">
    <img alt="readme-forge: READMEs that look as good as your code. A Claude skill." src=".github/assets/header-light.svg" width="100%">
  </picture>
</a>

<p align="center"><b>A Claude skill that writes, designs, scores and fixes READMEs using facts from your actual code.</b></p>

<p align="center">
  <img alt="Claude Agent Skill" src="https://img.shields.io/badge/Claude-Agent%20Skill-FF8A3D">
  <img alt="Scripts: Python 3.8+, standard library only" src="https://img.shields.io/badge/python-3.8%2B%20stdlib-FF8A3D?logo=python&logoColor=white">
  <img alt="12 animated banner styles" src="https://img.shields.io/badge/banners-12%20styles-FF8A3D">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-FF8A3D"></a>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> •
  <a href="#banner-gallery">Banner gallery</a> •
  <a href="#what-you-can-ask">What you can ask</a> •
  <a href="#how-it-works">How it works</a> •
  <a href="readme-forge/README.md">Skill docs</a>
</p>

<br>

<!-- To get an inline video player: edit this README on github.com, drag demo/readme-forge-cinematic.mp4 into the editor,
     and replace the poster block below with the https://github.com/user-attachments/assets/… link GitHub inserts. -->
<p align="center">
  <a href="demo/readme-forge-cinematic.mp4"><img alt="Demo video: a README scoring 43/100 becomes a designed, 95/100 README after one /readme-forge command" src="demo/video-poster.jpg" width="820"></a>
</p>

## Why

Most README generators fill one template. Most profile galleries ask you to copy someone else's file. Neither reads your code, and neither designs anything. readme-forge does both:

| | Other tools | readme-forge |
|---|---|---|
| **Facts** | Typed in by hand, or read from `package.json` only | Detects 15+ ecosystems, scripts, env vars, Docker, CI, routes; never invents commands |
| **Visuals** | A logo if you have one | Mermaid architecture **from real imports**, plus 12 animated banner styles with dark/light variants |
| **Widgets** | Hard-coded public URLs (some now return HTTP 402) | Tested endpoints, self-hosted SVGs that can't rate-limit, reliability tiers |
| **Quality** | None | A 0–100 score and linter: structure, accessibility, dead links, drift, design |
| **Platforms** | GitHub only | GitHub, Hugging Face cards, PyPI, npm, GitLab |

## Quickstart

<!-- TODO: replace OWNER with your GitHub username after publishing -->
```bash
git clone https://github.com/OWNER/readme-forge
cp -r readme-forge/readme-forge ~/.claude/skills/readme-forge
```

Then, in any project, open Claude Code and run:

```text
/readme-forge write a README for this repo, with a header and footer
```

On claude.ai or Claude Desktop, upload `readme-forge.zip` under **Settings → Capabilities → Skills**.

## Banner gallery

Every banner is a **self-contained animated SVG** that you commit to your repo, so there are no external services, rate limits or broken images. Each comes in a dark and a light variant (switch your GitHub theme to see both), shows a complete first frame, and stops moving for visitors who turn on reduce motion.

<table>
<tr>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/aurora-dark.svg"><img alt="aurora banner style: drifting mesh-gradient light" src="readme-forge/assets/banners/aurora-light.svg" width="100%"></picture>

<b><code>--style aurora</code></b><br><sub>drifting mesh-gradient light</sub>

</td>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/synthwave-dark.svg"><img alt="synthwave banner style: 3D perspective grid + striped sun" src="readme-forge/assets/banners/synthwave-light.svg" width="100%"></picture>

<b><code>--style synthwave</code></b><br><sub>3D perspective grid + striped sun</sub>

</td>
</tr>
<tr>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/isometric-dark.svg"><img alt="isometric banner style: 3D floating isometric cubes" src="readme-forge/assets/banners/isometric-light.svg" width="100%"></picture>

<b><code>--style isometric</code></b><br><sub>3D floating isometric cubes</sub>

</td>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/orbit-dark.svg"><img alt="orbit banner style: 3D tilted orbits, revolving planets" src="readme-forge/assets/banners/orbit-light.svg" width="100%"></picture>

<b><code>--style orbit</code></b><br><sub>3D tilted orbits, revolving planets</sub>

</td>
</tr>
<tr>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/glass-dark.svg"><img alt="glass banner style: frosted glass over moving colour" src="readme-forge/assets/banners/glass-light.svg" width="100%"></picture>

<b><code>--style glass</code></b><br><sub>frosted glass over moving colour</sub>

</td>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/terminal-dark.svg"><img alt="terminal banner style: code window that retypes the title" src="readme-forge/assets/banners/terminal-light.svg" width="100%"></picture>

<b><code>--style terminal</code></b><br><sub>code window that retypes the title</sub>

</td>
</tr>
<tr>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/neon-dark.svg"><img alt="neon banner style: glowing neon outline" src="readme-forge/assets/banners/neon-light.svg" width="100%"></picture>

<b><code>--style neon</code></b><br><sub>glowing neon outline</sub>

</td>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/wave-dark.svg"><img alt="wave banner style: layered animated waves" src="readme-forge/assets/banners/wave-light.svg" width="100%"></picture>

<b><code>--style wave</code></b><br><sub>layered animated waves</sub>

</td>
</tr>
<tr>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/blueprint-dark.svg"><img alt="blueprint banner style: engineering drawing that redraws" src="readme-forge/assets/banners/blueprint-light.svg" width="100%"></picture>

<b><code>--style blueprint</code></b><br><sub>engineering drawing that redraws</sub>

</td>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/constellation-dark.svg"><img alt="constellation banner style: twinkling particle network" src="readme-forge/assets/banners/constellation-light.svg" width="100%"></picture>

<b><code>--style constellation</code></b><br><sub>twinkling particle network</sub>

</td>
</tr>
<tr>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/minimal-dark.svg"><img alt="minimal banner style: clean type, one sweeping accent" src="readme-forge/assets/banners/minimal-light.svg" width="100%"></picture>

<b><code>--style minimal</code></b><br><sub>clean type, one sweeping accent</sub>

</td>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/bold-dark.svg"><img alt="bold banner style: oversized type, moving gradient" src="readme-forge/assets/banners/bold-light.svg" width="100%"></picture>

<b><code>--style bold</code></b><br><sub>oversized type, moving gradient</sub>

</td>
</tr>
</table>

```bash
python readme-forge/scripts/make_banner.py --style isometric --palette ocean --title "kubeforge" --subtitle "Clusters in one command" --out .github/assets
python readme-forge/scripts/make_banner.py --kind footer --style wave --title "Thanks for visiting" --out .github/assets
```

<details>
<summary><b>Footers and dividers</b></summary>
<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/footer-wave-dark.svg"><img alt="Wave footer: Thanks for reading" src="readme-forge/assets/banners/footer-wave-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/footer-minimal-dark.svg"><img alt="Minimal footer with an accent rule: Made with readme-forge" src="readme-forge/assets/banners/footer-minimal-light.svg" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="readme-forge/assets/banners/divider-aurora-dark.svg"><img alt="Animated gradient section divider" src="readme-forge/assets/banners/divider-aurora-light.svg" width="100%"></picture>

Palettes: `ember` · `ocean` · `violet` · `mint` · `sunset` · `mono` · `cyber`, or pass any brand colour with `--accent "#HEX"`.

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

## Contributing

Issues and pull requests are welcome. If you add a banner style, include both the dark and light renders and keep the first frame complete.

## License

Distributed under the MIT License. See [LICENSE](LICENSE).

---

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/footer-dark.svg">
  <img alt="Made with readme-forge" src=".github/assets/footer-light.svg" width="100%">
</picture>

<p align="right"><a href="#top">Back to top ↑</a></p>
