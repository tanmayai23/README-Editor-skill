---
name: readme-forge
description: Create, audit, and improve README files grounded in the real codebase — project READMEs (any language, monorepos), GitHub personal and organization profile READMEs with working widgets, Hugging Face model/dataset/Space cards, and PyPI/npm-ready variants. Generates Mermaid architecture diagrams from actual imports, picks badges from detected registries and CI, scores READMEs 0-100 with a linter, designs the page (animated SVG header/footer banners in 16 styles including ShaderGradient-style grain, landing-page spotlight hero, 3D synthwave, isometric, orbit, ribbon and pulse, plus clickable CTA buttons, palettes, typography, layout), handles dark/light images and accessibility, and writes companion docs (CONTRIBUTING, SECURITY, CITATION.cff, etc.). Use whenever the user mentions README, readme.md, profile README, GitHub profile, model card, dataset card, Space README, project documentation front page, "improve my readme", "make my repo look good", README banner/header/footer design, or badges/stats widgets.
---

# readme-forge

Write READMEs that are **true to the code**, **fast to scan**, and **correct for the platform** they render on.

Skill directory: `SKILL_DIR` = the folder containing this file. Scripts are stdlib-only Python 3.8+ (`python` or `python3`).

## Step 0 — Pick the mode

| User wants | Mode | Read first |
|---|---|---|
| README for a code project (new or from scratch) | **A. Project** | `references/project-readme.md` |
| Personal GitHub profile (`username/username` repo) or org profile (`.github/profile/README.md`) | **B. Profile** | `references/profile-readme.md`, `references/widgets.md` |
| Hugging Face model / dataset / Space | **C. Hugging Face** | `references/huggingface.md` |
| "Improve / review / fix / audit my README" | **D. Audit** | `references/quality-rubric.md` |
| Same README for PyPI / npm / HF / GitLab | **E. Port** | `references/platforms.md` |
| CONTRIBUTING, SECURITY, CITATION, CHANGELOG, templates | **F. Companion docs** | `templates/extras/` |
| Banner / header / footer / "make it look amazing" / redesign | **G. Design** | `references/design.md` |

Modes combine (e.g. A + C for an ML repo that ships to GitHub and HF; A + F for "make this repo open-source ready"). Always also apply `references/writing-style.md`. **Every new project or profile README ends with the Mode G design pass** (header + footer + palette) unless the user wants plain Markdown or the target platform can't render it (PyPI, npm).

## Hard rules (never break)

1. **Never invent facts.** Commands, flags, env vars, versions, benchmarks, features, URLs, and screenshots come only from (a) `analyze_repo.py` output, (b) files you read, or (c) the user. If unknown, write `<!-- TODO: ... -->` and list it in your final message.
2. **Commands must be copy-paste runnable** from a fresh clone, in the right order, using the project's real package manager (pnpm vs npm, uv vs pip, etc.).
3. **First screen answers:** what is it, why care, how to start. One-line pitch + quickstart within the first ~25 lines.
4. **Every image/badge has meaningful alt text.** Animated content gets a static fallback or is optional.
5. **Heading levels never skip** (H1 → H2 → H3). Exactly one H1.
6. **Use only features the target platform renders** (see `references/platforms.md`). Mermaid, `> [!NOTE]`, and `<picture>` are GitHub-only-ish.
7. **No filler** ("blazing fast", "simply", "easy-to-use", "robust", "seamless", "leverage"…). Show, don't claim.
8. **Respect existing content** in audit mode: keep the user's voice, project-specific facts, and custom sections; change what's wrong.
9. **Use real file names** from the facts: link `license.file` (e.g. `LICENSE.txt`, not an assumed `LICENSE`), the real CI workflow file, and the real entrypoint. Templates use generic names, so adjust them.
10. **Widgets/badges:** use endpoints from `references/widgets.md` / `references/badges.md`, with theme params matched to dark/light. Don't hard-depend on a single rate-limited public instance without mentioning the fallback.

## Mode A — Project README

0. **README already exists?** (`existing_readme` in facts) Score it first. Unless the user explicitly asked for a from-scratch rewrite, switch to Mode D (improve in place) so custom content isn't lost. For a fresh rewrite, overwrite `README.md` only if it's tracked by git (recoverable). Otherwise write `README.new.md` and say so.

1. **Gather facts**
   ```bash
   python SKILL_DIR/scripts/analyze_repo.py <repo_path>            # JSON facts
   python SKILL_DIR/scripts/import_graph.py <repo_path> --mermaid  # architecture draft
   ```
   `analyze_repo.py` detects: languages (by LOC), manifests (package.json, pyproject, setup.py, requirements, Cargo, go.mod, pom/gradle, Gemfile, composer, pubspec, *.csproj, mix.exs), package manager, scripts/make targets, entrypoints/bins, frameworks, env vars (from `.env.example` and code), Docker/compose services, CI providers, license, tests dir, docs, monorepo workspaces, HF artifacts, existing README, git remote (owner/repo). Folders named `demo`, `examples`, `samples`, `fixtures` or `testdata` are left out of the facts and listed in `example_dirs`; link them from an **Examples** section instead of treating their env vars and routes as the project's own.
   Then read the 3–8 most important files it lists (`key_files`) to understand purpose and flow. Do not skim the whole repo.
   Also read the files named in `config_hints` (Viper/pydantic-settings/dotenv/CLI option definitions). They tell you the config-file location, env-var overrides and flags that the Configuration section must document.
   `import_graph.py` switches to one node per file for single-package repos. Pass `--depth N` to force package grouping.
   **CLI `--help` output:** run the real command when it is safe and cheap (`go run . --help`, `python -m pkg --help`, `node bin/cli.js --help`, `cargo run -q -- --help`). If it can't be built, reconstruct it from the flag definitions and add `<!-- reconstructed from source; verify with --help -->` above the block.

2. **Classify** the project: library · CLI · web app · API/service · ML/data · monorepo · research/paper · template/starter · infra/devops · mobile · game. Pick the blueprint in `references/project-readme.md` and the template in `templates/project/`.

3. **Ask only what facts can't answer** (max 3 questions, batched): one-line pitch if not inferable, audience (users vs contributors), target platforms, whether to include demo media they have. If the user said "just do it", skip questions and leave TODOs.

4. **Build visuals** (`references/diagrams.md`):
   - Architecture: refine the `import_graph.py` draft into a readable diagram (group by layer, ≤ 15 nodes, label edges with verbs). Add a sequence diagram for the main request/data flow if the project is a service/pipeline.
   - Data: ER diagram if there are models/schemas; Mermaid `xychart-beta` / table for benchmarks only with real numbers.
   - Badges from detected registries/CI (`references/badges.md`) — 3–6 max in the header, rest in a details block or omitted.
   - Dark/light hero/logo via `<picture>` when the user has both assets.

5. **Write** following the blueprint. Recommended order: title + pitch + badges → (demo) → Features (3–7 concrete bullets) → Quickstart → Installation (all methods) → Usage (real examples) → Configuration (env var table) → Architecture → Project structure (trimmed tree) → Development / Testing → Deployment → Roadmap/FAQ (only if real) → Contributing → License → Acknowledgments. Add a TOC when > 6 H2 sections.

6. **Score & fix**
   ```bash
   python SKILL_DIR/scripts/score_readme.py README.md --repo <repo_path>
   ```
   Fix every `ERROR`, most `WARN`s; iterate until score ≥ 85 (or explain what blocks it — usually TODOs needing user input).

7. **Offer** (one line each, don't do unasked): companion docs (Mode F), a platform port (Mode E), a `check_links.py` run, a CI job running `score_readme.py --min 80` to stop drift.

## Mode B — Profile README

1. Read `references/profile-readme.md`. Collect (batch in one question): GitHub username, name/role/one-liner, current focus, top skills (or derive from their public repos if they allow), socials, preferred **archetype** (minimal · stats dashboard · creative/animated · code-mode · data/ML · student · OSS maintainer · retro · badges wall · Actions-dynamic · org · game mode · typing · anime/art · fancy fonts · descriptive · simple-but-innovative · icons · just an image; if they name an awesome-github-profile category, use the mapping in profile-readme.md), and dark-mode preference.
2. Start from `templates/profile/<archetype>.md`. Replace every `{{PLACEHOLDER}}`; delete sections with no data rather than leaving placeholders. Generate the profile hero banner and footer with `make_banner.py` (Mode G) in the user's accent colour. Offer the 3D contribution calendar (`workflows/profile-3d.yml`) for profiles that want a 3D visual.
3. Widgets: pick from `references/widgets.md`. Rules: ≤ 4 dynamic cards; use `<picture>` or theme params for dark/light; give each a descriptive alt; add the self-host / Actions fallback comment for stats cards; skill icons only for skills the user really uses (≤ 15).
4. If the archetype needs automation (snake, latest blog posts, WakaTime, metrics, the tic-tac-toe game), also write the workflow from `templates/profile/workflows/` (the game also needs `templates/profile/game/tictactoe.py` at `.github/scripts/`) and tell the user which secrets/settings to add.
   For **fancy fonts**, generate every styled string with `python SKILL_DIR/scripts/fancy_text.py "TEXT" --style <style>`; never type the Unicode yourself.
5. Run `score_readme.py --profile` and `check_links.py` (if network allowed) and fix failures.
6. Tell the user exactly where it goes: repo named exactly like their username, public, `README.md` at root (org: `.github` repo → `profile/README.md`).

## Mode C — Hugging Face cards

1. Read `references/huggingface.md`. Detect type: **model** (`config.json`, `*.safetensors`, `*.bin`, `adapter_config.json`, `*.gguf`), **dataset** (data files, `dataset_infos.json`, loading script), **Space** (`app.py` + gradio/streamlit, `Dockerfile` for docker SDK).
2. Fill YAML frontmatter with only valid keys/values (license ids, `pipeline_tag`, `library_name` — required explicitly for new repos, `base_model` + `base_model_relation`, Space `colorFrom/colorTo` from the allowed 8 colors).
3. Use `templates/huggingface/*`. Model cards must include intended use, out-of-scope use, bias/risks/limitations, how to use (runnable snippet), training data/procedure, evaluation (real numbers only), citation. Missing info → explicit "More information needed" rather than invented text.
4. If the project also has a GitHub README, keep facts in sync and cross-link both.
5. Run `score_readme.py --hf` to validate frontmatter.

## Mode D — Audit / Improve

1. `score_readme.py README.md --repo <path> --json` → score, per-category breakdown, findings.
2. `analyze_repo.py <path>` → compare to README for **drift**: commands that no longer exist, missing env vars, wrong package manager, stale versions/Node/Python requirements, dead relative links, missing new features (bins, routes, packages).
3. Report to the user: score, top 5 fixes ranked by impact, drift list. Then apply fixes (unless they asked only for a review), preserving their voice and custom sections.
4. Re-score and show before → after.

## Mode E — Port to another platform

Read `references/platforms.md`. Typical transforms: relative → absolute URLs (raw.githubusercontent / jsDelivr for images), Mermaid → pre-rendered image or removed, GitHub alerts → blockquotes with bold label, `<picture>` → single image, strip HTML not on the allowlist, add HF frontmatter, set `long_description_content_type="text/markdown"` / `readme = "README.md"` in pyproject. Write ported files next to the original (e.g. `README.pypi.md`) unless asked to overwrite.

## Mode G — Design (header, footer, banners)

Read `references/design.md` first.
1. Choose the header pattern (centered stack / minimal / splash / profile hero) and a banner style + palette from the style table (project type, brand colour, audience). If it isn't obvious, generate 2–3 options and show the user.
2. Generate the assets (dark + light, self-contained, committed to the repo):
   ```bash
   python SKILL_DIR/scripts/make_banner.py --style <style> [--palette <p>] [--accent "#HEX"] [--logo <file>] --title "<name>" --subtitle "<pitch ≤ 12 words>" [--tag "<category>"] --out .github/assets
   python SKILL_DIR/scripts/make_banner.py --kind footer --style <minimal|wave> --title "<credit line>" --out .github/assets
   ```
   For profiles, put the assets in `assets/`. For Hugging Face, use `#hf-dark-mode-only` / `#hf-light-mode-only` instead of `<picture>`.
3. Pass `--href <url>` so the printed snippet is already wrapped in a link, and paste it exactly as printed. Never type `<a href="…"><picture>` on one line with the `<source>` on the next: GitHub empties that `<picture>`, so the dark variant never shows and the click opens the SVG file. Then put the pitch, badges (one style, palette colour) and link row below it, as in design.md §2.
   **If the project has a logo** (look for `logo.*`, `icon.*`, `assets/brand/*`, or ask), pass `--logo`. It is embedded in the SVG (no external request). Spotlight centres it above the title; other styles place it on the left. Use a transparent PNG about 320 px wide or an SVG; a logo with a white box looks wrong on dark banners. Pick a palette (or `--accent`) that matches the logo's colours.
   For a **landing-page** feel (apps, SaaS, launches), use the spotlight hero + CTA buttons (`--kind button`) from design.md §10 and `templates/design/hero-landing.md`. Optionally repeat the CTA before the footer with `templates/design/cta-section.md`. For a **ShaderGradient** look, use `--style shader --palette halo|pensive|interstella|universe|mandarin|nighty`.
4. End with a footer (design.md §3): license line, credit, back-to-top, plus the footer SVG for polished projects and profiles.
5. Run `score_readme.py`. Fix the `design` findings (missing dark variant, mixed badge styles, external fonts in SVGs, oversized assets).
6. **Visual check:** if a browser is available, render the README or the SVGs and look at both themes. At minimum, open each SVG once to confirm the title is fully visible.

Never: hotlink a third-party banner by default, put the only copy of the pitch inside an image, use more than 2 animations above the fold, or animate the text in from blank.

## Mode F — Companion docs

Copy and fill from `templates/extras/`: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1 — requires a contact method; ask), `SECURITY.md`, `SUPPORT.md`, `CHANGELOG.md` (Keep a Changelog), `CITATION.cff` (research/academic), `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md`. Fill commands from analyzer facts. Link each from the README.

## Final message to the user

Keep it short: what files you wrote, the final score, the list of TODOs that need their input (screenshots, demo URL, contact email…), and any setup they must do (Actions secrets, enabling Pages, making profile repo public).
