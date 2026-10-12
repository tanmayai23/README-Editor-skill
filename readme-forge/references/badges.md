# Badges — pick from facts, not vibes

Header rule: **3–6 badges** that answer "does it work, what version, can I use it". Extra badges (downloads, chat, sponsors) go lower or nowhere. Every badge = `[![ALT](IMG)](LINK)` with an alt that reads as a sentence fragment ("CI status", "PyPI version", "License: MIT").

Use analyzer facts: `ci[]` → build badge, `package.publishable_*` → registry badge, `license.spdx` → license badge, `coverage_service` → coverage, `docker` → image badge, `huggingface` → HF badge.

## Build / CI
| Source | Image | Link |
|---|---|---|
| GitHub Actions (native, preferred) | `https://github.com/OWNER/REPO/actions/workflows/FILE.yml/badge.svg` (`?branch=main`) | `https://github.com/OWNER/REPO/actions/workflows/FILE.yml` |
| GitHub Actions (shields) | `https://img.shields.io/github/actions/workflow/status/OWNER/REPO/FILE.yml?branch=main&label=CI` | same |
| GitLab CI | `https://gitlab.com/OWNER/REPO/badges/main/pipeline.svg` | `https://gitlab.com/OWNER/REPO/-/pipelines` |
| CircleCI | `https://img.shields.io/circleci/build/github/OWNER/REPO/main` | circleci project URL |

Choose the workflow that runs tests (name contains test/ci/build), not release or labeler workflows.

## Coverage
- Codecov: `https://codecov.io/gh/OWNER/REPO/graph/badge.svg` → `https://codecov.io/gh/OWNER/REPO`
- Coveralls: `https://coveralls.io/repos/github/OWNER/REPO/badge.svg?branch=main`

## Registries
| Ecosystem | Version | Extra |
|---|---|---|
| npm | `https://img.shields.io/npm/v/PKG` | downloads `…/npm/dm/PKG`, bundle size `https://img.shields.io/bundlephobia/minzip/PKG`, types `…/npm/types/PKG` |
| JSR | `https://jsr.io/badges/@SCOPE/PKG` | |
| PyPI | `https://img.shields.io/pypi/v/PKG` | Python versions `…/pypi/pyversions/PKG`, downloads `https://static.pepy.tech/badge/PKG/month` |
| conda-forge | `https://img.shields.io/conda/vn/conda-forge/PKG` | |
| crates.io | `https://img.shields.io/crates/v/CRATE` | docs `https://docs.rs/CRATE/badge.svg` → docs.rs |
| Go | `https://pkg.go.dev/badge/MODULE.svg` → `https://pkg.go.dev/MODULE` | report card `https://goreportcard.com/badge/MODULE` |
| Maven Central | `https://img.shields.io/maven-central/v/GROUP/ARTIFACT` | |
| NuGet | `https://img.shields.io/nuget/v/PKG` | |
| RubyGems | `https://img.shields.io/gem/v/GEM` | |
| Packagist | `https://img.shields.io/packagist/v/VENDOR/PKG` | |
| pub.dev | `https://img.shields.io/pub/v/PKG` | |
| Docker Hub | `https://img.shields.io/docker/v/OWNER/IMAGE?sort=semver` | pulls `…/docker/pulls/OWNER/IMAGE`; GHCR has no shields endpoint — link the package page |
| VS Code ext | `https://img.shields.io/visual-studio-marketplace/v/PUBLISHER.EXT` | |
| GitHub release | `https://img.shields.io/github/v/release/OWNER/REPO` | for projects without a registry |

## Meta
- License: `https://img.shields.io/github/license/OWNER/REPO` or static `https://img.shields.io/badge/license-MIT-blue` (static if repo is private/not on GitHub).
- Hugging Face: `https://huggingface.co/datasets/huggingface/badges/resolve/main/model-on-hf-md.svg` (also `dataset-on-hf-md.svg`, `open-in-hf-spaces-md.svg`; sizes `sm|md|lg|xl`, dark variants `-dark`) → link to the model/dataset/Space.
- Open in Colab: `https://colab.research.google.com/assets/colab-badge.svg` → `https://colab.research.google.com/github/OWNER/REPO/blob/main/PATH.ipynb`
- arXiv: `https://img.shields.io/badge/arXiv-2401.00000-b31b1b` → paper.
- DOI (Zenodo): `https://zenodo.org/badge/DOI/10.5281/zenodo.NNN.svg`.
- Docs site: `https://img.shields.io/badge/docs-latest-blue` → docs URL (only if docs exist).
- Discord: `https://img.shields.io/discord/SERVER_ID?label=Discord&logo=discord` (needs the numeric server id — ask).
- OpenSSF Scorecard: `https://api.securityscorecards.dev/projects/github.com/OWNER/REPO/badge`.
- Stars (social proof, optional): `https://img.shields.io/github/stars/OWNER/REPO?style=social`.

## Style
- One style per row: `flat` (default) or `flat-square`. `for-the-badge` only for profile/social rows.
- Logos: `&logo=python&logoColor=white`.
- Avoid "made with ❤️", "maintained: yes", "PRs welcome" badges in the header — they carry no information; say it in text.
- Many badges? Group as a table or put secondary ones in `<details><summary>More badges</summary>…</details>`.

## Example header
```md
[![CI status](https://github.com/acme/rocket/actions/workflows/ci.yml/badge.svg)](https://github.com/acme/rocket/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/rocket)](https://pypi.org/project/rocket/)
[![Python versions](https://img.shields.io/pypi/pyversions/rocket)](https://pypi.org/project/rocket/)
[![License: MIT](https://img.shields.io/github/license/acme/rocket)](LICENSE)
```
