# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.3.0] - 2026-10-24

### Added

- Page kit in readme-forge-design (`scripts/make_page.py`): designs a whole README, not only the header and footer. One JSON spec becomes a set of matching SVG cards in light and dark plus the finished README. Blocks: terminal-window hero with a dripping edge, contact dock, numbered section headers, about card, tech-stack grid, project cards (feature / card / link), achievement cards (photo or emblem), themed stats widgets, Markdown passthrough and a mirrored footer. Six themes (`keynote`, `aurora`, `sunset`, `ocean`, `forest`, `mono`) or custom `accents`; `ambient`, `entrance` and `static` motion, CSS only. Paired cards share a height, linked cards are written on one line so GitHub keeps dark mode and the link, and the script refuses specs with `{{placeholders}}` left. Mode K in SKILL.md, `references/page-kit.md`, starter specs in `templates/page/`, and two examples (`examples/keynote-profile/`, `examples/keynote-project/`).
- `assets/icons.json`: 103 brand icons from Simple Icons (CC0) for the stack and dock cards, with aliases (`aws`, `gcp`, `node`, `k8s`…) and line icons for mail, website, résumé and more. Unknown names fall back to a monogram tile.
- Page kit blocks learned from popular profile READMEs: `code` (about-me as a YAML or JSON editor card with syntax colours), `portrait` (dot-matrix halftone drawn from a PNG by a stdlib PNG decoder; only the dots are stored), `certs` (badge and certification wall), hero `roles` (rotating role line that replaces readme-typing-svg and shows the first role in frame 0), project `links` (cards in a table with a Live · Code row under each), and `stats` options for top languages, LeetCode, Codeforces, the 3D contribution calendar and a view counter. 14 more brand icons (117), including Codeforces, HackerRank, CodeChef, GeeksforGeeks, Java (OpenJDK), HTML and CSS. New fictional example `examples/keynote-coder/`.
- `references/page-kit.md`: "Learning from a sample README", a table that maps common profile patterns (capsule-render headers, typing banners, YAML about-me, badge walls, project tables, coding-profile cards) to page-kit blocks and lists the widgets whose hosts are dead.

### Changed

- README: the install command now sits on the first screen; a Limitations section collects what the claim check, score, diagrams and analyzer can't do (moved out of the FAQ); a Support section and `.github/FUNDING.yml` add a Buy Me a Coffee link and GitHub's Sponsor button.
- The page kit's stats card no longer sets `include_all_commits`: the public github-readme-stats instance answers "Could not fetch total commits" for many users. Turn it back on with `"all_commits": true` when self-hosting. `widgets.md` notes this, adds the Codeforces card and marks the MonkeyType card as dead (HTTP 404).
- The project README is built from page-kit cards (`.github/page.json`): a hero with a dripping edge, three ways-to-use-it cards, a claim-check feature card with four feature cards, a validated-score card and a mirrored footer. Headings, commands and data stay as real Markdown, so anchors and the claim check still work.
- `score_readme.py --profile` counts page-kit section cards (alt text like `02 — Tech stack`) as section headings, so a card-built profile is scored on its content instead of losing points for missing Markdown headings.

### Fixed

- The demo GIF and video ended on `/plugin install readme-forge`, which fails on its own. The end card now shows the repository address, `github.com/tanmayai23/README-Editor-skill`, where the README has the working install command.

## [1.2.0] - 2026-10-19

This release makes accuracy the headline: every README the skill writes is checked claim by claim against the code, and the design features move to an optional plugin.

### Added

- `scripts/verify_readme.py`: extracts every command, script, flag, env var and path from a README and checks each one against the repository. Reports verified / not found / unverifiable and an accuracy percentage; `--min-accuracy` gates CI. The skill now requires zero "not found" claims before it finishes.
- GitHub Action (`uses: tanmayai23/README-Editor-skill@v1`): scores and fact-checks READMEs on pull requests, upserts one PR comment, writes the job summary, and can fail below `min-score` / `min-accuracy`. Forked PRs degrade to a warning (#1).
- Unit tests (`python -m unittest discover -s tests`) with fixtures for all 15 ecosystems `analyze_repo.py` detects, for `import_graph.py` in Python, JS/TS, Go and Rust, for the verifier and for the Action.
- Swift (SwiftPM), Zig and Haskell (Stack, Cabal) detection; Deno tasks and `Deno.env.get`; `mix phx.server` for Phoenix.
- Shader banner styles in readme-forge-design, rebuilt in SVG from the look of no-code WebGL shader scenes: `vortex` (spinning blades, liquified contour swirl, condensed serif caps; logo sits in the eye), `beam` (light racing around the edge over a nebula), `shatter` (voronoi glass with glowing cracks), `prism` (RGB-split blinds with a swipe reveal). `vortex` footer, `beam` divider, and `inferno` and `prism` palettes. All four animate with CSS only, so reduced motion stops them.

- `make_banner.py --style pulse`: soft concentric rings breathing behind the title, with dark and light variants (#15, thanks @Sultanast01).
- `make_banner.py --href URL` for headers and footers: prints the banner already wrapped in a link, in the form GitHub renders correctly.
- 8 profile archetypes covering every category of the [awesome-github-profile](https://zzetao.github.io/awesome-github-profile/) gallery: `game-mode`, `typing`, `anime-art`, `fancy-fonts`, `descriptive`, `simple-innovative`, `icons` and `just-image`. `profile-readme.md` maps each of the gallery's 16 categories to a template.
- Community tic-tac-toe for profiles (`workflows/tictactoe.yml` + `game/tictactoe.py`): visitors click a square, which opens an issue, and an Action plays the move, redraws the board, keeps a scoreboard and closes the issue. Issue titles are validated and passed through `env`, never into the shell.
- `scripts/fancy_text.py`: converts text to Unicode bold, italic, sans, mono and double-struck styles, including the letters outside the math block (ℎ, ℂ, ℝ…).
- `score_readme.py` warns when styled Unicode text runs past headings and a tagline, since screen readers spell it letter by letter.
- Spotify now-playing widget (kittinan/spotify-github-profile) in `widgets.md`.
- `score_readme.py` reports a `<picture>` that GitHub empties, either opened after `<a href>` on the same line or glued to the paragraph line above it.

### Changed

- **Split into two plugins.** `readme-forge` keeps facts, verification, scoring, Hugging Face cards and companion docs. Banners, CTA buttons, design templates, profile READMEs, widgets and `fancy_text.py` move to the optional `readme-forge-design` plugin (`claude plugin install readme-forge-design --marketplace tanmayai23/README-Editor-skill`). Releases ship `readme-forge.zip` and `readme-forge-design.zip`.
- The project README leads with the claim check, drops the banner gallery (now in readme-forge-design), the badge wall and the star-history chart, passes `verify_readme.py` at 100%, and uses the new vortex header.
- `pulse` banners animate with CSS instead of SMIL, so reduced motion stops them.
- The release job fails when the tag doesn't match the plugin version or the CHANGELOG has no section for it (#19).

### Fixed

- `score_readme.py` counted `<img>` written inside inline code or code blocks as a real image and reported missing alt text.
- `analyze_repo.py`: Java's `src/main/java/com/example/` was treated as a sample folder, hiding its env vars; Go modules with only `cmd/<x>` got an `go install` path that fails; justfile assignments were listed as recipes and recipes with default parameters were missed.
- `import_graph.py`: tsconfig path aliases were lost when the file had a `//` comment; `from . import x` linked to `__init__.py` instead of the submodule; `go.mod` in a subfolder wasn't found; Rust `mod x;` inside `net/mod.rs` and nested `use crate::` paths resolved to the wrong file (#25, #31).
- Linked banners and CTA buttons showed the light variant in dark mode and opened the SVG file instead of the link. `make_banner.py --kind button` printed `<a href><picture>` on one line with the `<source>` on the next, and GitHub drops the `<source>` from that form. The snippet now puts `<a>`, `<picture>` and `</a>` on separate lines.
- `hero-landing.md`, `header-profile.md` and `header-centered.md` templates: blank line after `<a id="top"></a>`, so the header `<picture>` no longer gets emptied.

## [1.1.0] - 2026-10-13

### Added

- `make_banner.py --logo FILE`: embeds a PNG, SVG, WebP, JPG or GIF logo in a header, with a soft accent glow so dark logos stay visible on dark banners. Spotlight centres it above the title; other styles place it on the left and keep the title clear of it.
- `ghost` palette (cyan, blue and purple on deep navy), matching the readme-forge logo.
- readme-forge logo, rebranded header, footer and CTA buttons, and a 1280×640 social preview image.

### Changed

- Demo video and GIF: local paths, plan name and installed-plugin list are blurred.

## [1.0.1] - 2026-10-12

### Fixed

- `score_readme.py --hf` crashed on model cards (a regex was split at `|` inside a group).
- `analyze_repo.py` no longer reports env vars, routes and tests from `demo/`, `examples/`, `samples/`, `fixtures/` and `testdata/` as the project's own. They are listed in `example_dirs` instead.
- `make_banner.py` printed absolute paths (`C:/Users/...`) in the README snippet when `--out` was absolute. Paths are now relative to the repository root.

### Added

- Terminal install command (`claude plugin install ...`) for environments where `/plugin` isn't available, such as the VS Code extension.
- Troubleshooting section in the README.
- CI checks for Hugging Face cards and the plugin manifests.

## [1.0.0] - 2026-10-12

### Added

- `readme-forge` skill: project READMEs from real code facts, GitHub profile READMEs (11 archetypes), Hugging Face model/dataset/Space cards, and PyPI/npm/GitLab variants.
- `analyze_repo.py`: detects languages, package managers, scripts, env vars, Docker, CI, license and Hugging Face artifacts.
- `import_graph.py`: Mermaid architecture diagrams from Python, JS/TS, Go and Rust imports.
- `score_readme.py`: 0–100 score, linter, accessibility checks and code-drift detection.
- `check_links.py`: dead-link and dead-widget checker.
- `make_banner.py`: 15 animated SVG banner styles with dark/light variants, footers, dividers and CTA buttons.
- Companion doc templates, profile GitHub Actions, and a Claude Code plugin marketplace.
- Demo reel and GIF.
