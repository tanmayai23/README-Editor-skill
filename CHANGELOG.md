# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `make_banner.py --style pulse`: soft concentric rings breathing behind the title, with dark and light variants (#15, thanks @Sultanast01).

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
