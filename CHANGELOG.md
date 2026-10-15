# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `make_banner.py --style pulse`: soft concentric rings breathing behind the title, with dark and light variants (#15, thanks @Sultanast01).
- `make_banner.py --href URL` for headers and footers: prints the banner already wrapped in a link, in the form GitHub renders correctly.
- 8 profile archetypes covering every category of the [awesome-github-profile](https://zzetao.github.io/awesome-github-profile/) gallery: `game-mode`, `typing`, `anime-art`, `fancy-fonts`, `descriptive`, `simple-innovative`, `icons` and `just-image`. `profile-readme.md` maps each of the gallery's 16 categories to a template.
- Community tic-tac-toe for profiles (`workflows/tictactoe.yml` + `game/tictactoe.py`): visitors click a square, which opens an issue, and an Action plays the move, redraws the board, keeps a scoreboard and closes the issue. Issue titles are validated and passed through `env`, never into the shell.
- `scripts/fancy_text.py`: converts text to Unicode bold, italic, sans, mono and double-struck styles, including the letters outside the math block (ℎ, ℂ, ℝ…).
- `score_readme.py` warns when styled Unicode text runs past headings and a tagline, since screen readers spell it letter by letter.
- Spotify now-playing widget (kittinan/spotify-github-profile) in `widgets.md`.
- `score_readme.py` reports a `<picture>` that GitHub empties, either opened after `<a href>` on the same line or glued to the paragraph line above it.

### Fixed

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
