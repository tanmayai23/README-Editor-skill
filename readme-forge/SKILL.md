---
name: readme-forge
description: Create, audit and fix README files grounded in the real codebase, so every command, env var and path in them is checked against the code. Covers project READMEs (any language, monorepos), Hugging Face model/dataset/Space cards, PyPI/npm-ready variants and companion docs (CONTRIBUTING, SECURITY, CITATION.cff, etc.). Reads facts from 15 ecosystems, draws Mermaid architecture diagrams from actual imports, verifies every claim in the README against the repo, scores READMEs 0-100 with a linter, and detects drift between README and code. Use whenever the user mentions README, readme.md, model card, dataset card, Space README, project documentation front page, "improve my readme", "is my README accurate", "make my repo look good", or badges. For animated banners and GitHub profile READMEs, hand off to the readme-forge-design skill if it is installed.
---

# readme-forge

Write READMEs that are **true to the code**, **fast to scan**, and **correct for the platform** they render on.

Skill directory: `SKILL_DIR` = the folder containing this file. Scripts are stdlib-only Python 3.8+ (`python` or `python3`).

## Step 0 — Pick the mode

| User wants | Mode | Read first |
|---|---|---|
| README for a code project (new or from scratch) | **A. Project** | `references/project-readme.md` |
| Hugging Face model / dataset / Space | **C. Hugging Face** | `references/huggingface.md` |
| "Improve / review / fix / audit my README", "is it accurate?" | **D. Audit** | `references/quality-rubric.md` |
| Same README for PyPI / npm / HF / GitLab | **E. Port** | `references/platforms.md` |
| CONTRIBUTING, SECURITY, CITATION, CHANGELOG, templates | **F. Companion docs** | `templates/extras/` |
| GitHub profile README, animated banner/header/footer, CTA buttons, "make it look amazing" | **Design** | the **readme-forge-design** skill (see below) |

Modes combine (e.g. A + C for an ML repo that ships to GitHub and HF; A + F for "make this repo open-source ready"). Always also apply `references/writing-style.md`.

**Design and profiles live in a separate, optional skill.** If the user asks for a banner, a visual redesign or a GitHub profile README, use the `readme-forge-design` skill when it is available. If it isn't installed, say so in one line (`claude plugin install readme-forge-design --marketplace tanmayai23/README-Editor-skill`) and write a plain, accurate README with a text header instead. Never let design work replace the fact-gathering and verification steps below.

## Hard rules (never break)

1. **Never invent facts.** Commands, flags, env vars, versions, benchmarks, features, URLs, and screenshots come only from (a) `analyze_repo.py` output, (b) files you read, or (c) the user. If unknown, write `<!-- TODO: ... -->` and list it in your final message.
2. **Every README you write or change passes `verify_readme.py` with no `not_found` claims.** A `not_found` claim is a hallucination: fix it or replace it with a TODO.
3. **Commands must be copy-paste runnable** from a fresh clone, in the right order, using the project's real package manager (pnpm vs npm, uv vs pip, etc.).
4. **First screen answers:** what is it, why care, how to start. One-line pitch + quickstart within the first ~25 lines.
5. **Every image/badge has meaningful alt text.** Animated content gets a static fallback or is optional.
6. **Heading levels never skip** (H1 → H2 → H3). Exactly one H1.
7. **Use only features the target platform renders** (see `references/platforms.md`). Mermaid, `> [!NOTE]`, and `<picture>` are GitHub-only-ish.
8. **No filler** ("blazing fast", "simply", "easy-to-use", "robust", "seamless", "leverage"…). Show, don't claim.
9. **Respect existing content** in audit mode: keep the user's voice, project-specific facts, and custom sections; change what's wrong.
10. **Use real file names** from the facts: link `license.file` (e.g. `LICENSE.txt`, not an assumed `LICENSE`), the real CI workflow file, and the real entrypoint. Templates use generic names, so adjust them.
11. **Badges:** pick from `references/badges.md` for registries and CI the facts actually show; 3–6 max in the header.

## Mode A — Project README

0. **README already exists?** (`existing_readme` in facts) Score and verify it first. Unless the user explicitly asked for a from-scratch rewrite, switch to Mode D (improve in place) so custom content isn't lost. For a fresh rewrite, overwrite `README.md` only if it's tracked by git (recoverable). Otherwise write `README.new.md` and say so.

1. **Gather facts**
   ```bash
   python SKILL_DIR/scripts/analyze_repo.py <repo_path>            # JSON facts
   python SKILL_DIR/scripts/import_graph.py <repo_path> --mermaid  # architecture draft
   ```
   `analyze_repo.py` detects: languages (by LOC), manifests for 15 ecosystems (Node npm/pnpm/Yarn/Bun, Python pip/uv/Poetry/PDM/Hatch/Pipenv/conda, Rust, Go, Maven/Gradle, Ruby, PHP, Dart/Flutter, Elixir, .NET, CMake, Deno, Swift, Zig, Haskell), package manager, scripts/make/just targets, entrypoints/bins, frameworks, env vars (from `.env.example` and code), Docker/compose services, CI providers, license, tests dir, docs, monorepo workspaces, HF artifacts, existing README, git remote (owner/repo). Folders named `demo`, `examples`, `samples`, `fixtures` or `testdata` are left out of the facts and listed in `example_dirs`; link them from an **Examples** section instead of treating their env vars and routes as the project's own.
   Then read the 3–8 most important files it lists (`key_files`) to understand purpose and flow. Do not skim the whole repo.
   Also read the files named in `config_hints` (Viper/pydantic-settings/dotenv/CLI option definitions). They tell you the config-file location, env-var overrides and flags that the Configuration section must document.
   `import_graph.py` switches to one node per file for single-package repos. Pass `--depth N` to force package grouping.
   **CLI `--help` output:** run the real command when it is safe and cheap (`go run . --help`, `python -m pkg --help`, `node bin/cli.js --help`, `cargo run -q -- --help`). If it can't be built, reconstruct it from the flag definitions and add `<!-- reconstructed from source; verify with --help -->` above the block.

2. **Classify** the project: library · CLI · web app · API/service · ML/data · monorepo · research/paper · template/starter · infra/devops · mobile · game. Pick the blueprint in `references/project-readme.md` and the template in `templates/project/`.

3. **Ask only what facts can't answer** (max 3 questions, batched): one-line pitch if not inferable, audience (users vs contributors), target platforms, whether to include demo media they have. If the user said "just do it", skip questions and leave TODOs.

4. **Build visuals** (`references/diagrams.md`):
   - Architecture: refine the `import_graph.py` draft into a readable diagram (group by layer, ≤ 15 nodes, label edges with verbs). Add a sequence diagram for the main request/data flow if the project is a service/pipeline.
   - Data: ER diagram if there are models/schemas; Mermaid `xychart-beta` / table for benchmarks only with real numbers.
   - Badges from detected registries/CI (`references/badges.md`).
   - Dark/light hero/logo via `<picture>` when the user has both assets.

5. **Write** following the blueprint. Recommended order: title + pitch + badges → (demo) → Features (3–7 concrete bullets) → Quickstart → Installation (all methods) → Usage (real examples) → Configuration (env var table) → Architecture → Project structure (trimmed tree) → Development / Testing → Deployment → Roadmap/FAQ (only if real) → Contributing → License → Acknowledgments. Add a TOC when > 6 H2 sections.

6. **Verify every claim, then score**
   ```bash
   python SKILL_DIR/scripts/verify_readme.py README.md --repo <repo_path>
   python SKILL_DIR/scripts/score_readme.py README.md --repo <repo_path>
   ```
   `verify_readme.py` extracts every command, flag, script, env var and path from the README and checks each one against the repository (`✓` verified, `✗` not found, `?` can't be checked offline). Fix every `✗`: correct it from the facts or replace it with a TODO. Then fix every scorer `ERROR` and most `WARN`s; iterate until the score is ≥ 85 (or explain what blocks it, usually TODOs needing user input).

7. **Offer** (one line each, don't do unasked): companion docs (Mode F), a platform port (Mode E), a `check_links.py` run, the design pass (readme-forge-design), and the PR check from this repo's GitHub Action (`uses: tanmayai23/README-Editor-skill@v1`) to stop drift.

## Mode C — Hugging Face cards

1. Read `references/huggingface.md`. Detect type: **model** (`config.json`, `*.safetensors`, `*.bin`, `adapter_config.json`, `*.gguf`), **dataset** (data files, `dataset_infos.json`, loading script), **Space** (`app.py` + gradio/streamlit, `Dockerfile` for docker SDK).
2. Fill YAML frontmatter with only valid keys/values (license ids, `pipeline_tag`, `library_name` — required explicitly for new repos, `base_model` + `base_model_relation`, Space `colorFrom/colorTo` from the allowed 8 colors).
3. Use `templates/huggingface/*`. Model cards must include intended use, out-of-scope use, bias/risks/limitations, how to use (runnable snippet), training data/procedure, evaluation (real numbers only), citation. Missing info → explicit "More information needed" rather than invented text.
4. If the project also has a GitHub README, keep facts in sync and cross-link both.
5. Run `score_readme.py --hf` to validate frontmatter, and `verify_readme.py` on any code snippets that reference repo files.

## Mode D — Audit / Improve

1. `verify_readme.py README.md --repo <path> --json` → every claim with its status. Each `not_found` is a hallucination or stale fact.
2. `score_readme.py README.md --repo <path> --json` → score, per-category breakdown, findings.
3. `analyze_repo.py <path>` → compare to README for **drift**: commands that no longer exist, missing env vars, wrong package manager, stale versions/Node/Python requirements, dead relative links, missing new features (bins, routes, packages).
4. Report to the user: claim accuracy (`X of Y checked claims match the code`), score, top 5 fixes ranked by impact, drift list. Then apply fixes (unless they asked only for a review), preserving their voice and custom sections.
5. Re-run both scripts and show before → after.

## Mode E — Port to another platform

Read `references/platforms.md`. Typical transforms: relative → absolute URLs (raw.githubusercontent / jsDelivr for images), Mermaid → pre-rendered image or removed, GitHub alerts → blockquotes with bold label, `<picture>` → single image, strip HTML not on the allowlist, add HF frontmatter, set `long_description_content_type="text/markdown"` / `readme = "README.md"` in pyproject. Write ported files next to the original (e.g. `README.pypi.md`) unless asked to overwrite.

## Mode F — Companion docs

Copy and fill from `templates/extras/`: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1 — requires a contact method; ask), `SECURITY.md`, `SUPPORT.md`, `CHANGELOG.md` (Keep a Changelog), `CITATION.cff` (research/academic), `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md`. Fill commands from analyzer facts. Link each from the README.

## Final message to the user

Keep it short: what files you wrote, the claim check (`N claims checked, all match the code` or what's left), the final score, the list of TODOs that need their input (screenshots, demo URL, contact email…), and any setup they must do.
