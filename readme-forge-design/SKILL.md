---
name: readme-forge-design
description: Optional design layer for readme-forge. Generates self-contained animated SVG banners (20 styles, including WebGL-shader looks rebuilt in SVG — spinning vortex, edge light beam, voronoi shatter, RGB prism blinds — plus ShaderGradient grain, landing-page spotlight, synthwave, isometric, orbit, ribbon), footers, dividers and clickable CTA buttons in dark and light variants, and builds GitHub personal and organization profile READMEs from 19 archetypes with tested widgets and profile Actions. Use when the user asks for a README banner/header/footer, "make my README look amazing", a redesign, CTA buttons, or a GitHub profile README. For the README's facts, commands and accuracy, use the core readme-forge skill.
---

# readme-forge-design

Make READMEs and GitHub profiles look designed, without external services: every asset is an SVG committed to the repo.

Skill directory: `SKILL_DIR` = the folder containing this file. Scripts are stdlib-only Python 3.8+.

**Division of labour.** This skill owns the look. The core `readme-forge` skill owns the facts: it writes project READMEs from the code and checks every command, env var and path with `verify_readme.py`. When you design a project README, run the core skill's fact-gathering and verification first, or keep the existing text untouched. Scoring (`score_readme.py`) and link checks (`check_links.py`) also come from the core skill; if it isn't installed, tell the user in one line and skip those steps.

| User wants | Mode | Read first |
|---|---|---|
| Banner / header / footer / CTA buttons / "make it look amazing" | **G. Design** | `references/design.md` |
| Personal GitHub profile (`username/username` repo) or org profile (`.github/profile/README.md`) | **B. Profile** | `references/profile-readme.md`, `references/widgets.md` |

## Mode G — Design (header, footer, banners)

Read `references/design.md` first.
1. Choose the header pattern (centered stack / minimal / splash / profile hero) and a banner style + palette from the style table (project type, brand colour, audience). If it isn't obvious, generate 2–3 options and show the user.
2. Generate the assets (dark + light, self-contained, committed to the repo):
   ```bash
   python SKILL_DIR/scripts/make_banner.py --style <style> [--palette <p>] [--accent "#HEX"] [--logo <file>] --title "<name>" --subtitle "<pitch ≤ 12 words>" [--tag "<category>"] --out .github/assets
   python SKILL_DIR/scripts/make_banner.py --kind footer --style <minimal|wave|vortex> --title "<credit line>" --out .github/assets
   python SKILL_DIR/scripts/make_banner.py --kind divider --style <aurora|beam> --out .github/assets
   ```
   `python SKILL_DIR/scripts/make_banner.py --list` prints every style and palette. For profiles, put the assets in `assets/`. For Hugging Face, use `#hf-dark-mode-only` / `#hf-light-mode-only` instead of `<picture>`.
3. Pass `--href <url>` so the printed snippet is already wrapped in a link, and paste it exactly as printed. Never type `<a href="…"><picture>` on one line with the `<source>` on the next: GitHub empties that `<picture>`, so the dark variant never shows and the click opens the SVG file. Then put the pitch, badges (one style, palette colour) and link row below it, as in design.md §2.
   **If the project has a logo** (look for `logo.*`, `icon.*`, `assets/brand/*`, or ask), pass `--logo`. It is embedded in the SVG (no external request). Spotlight centres it above the title, vortex puts it in the eye of the vortex, and other styles place it on the left. Use a transparent PNG about 320 px wide or an SVG; a logo with a white box looks wrong on dark banners. Pick a palette (or `--accent`) that matches the logo's colours.
   **Shader looks:** `vortex` (default `inferno` palette: warm black, red-orange blades, condensed serif caps), `beam` (light racing around the edge over a nebula), `shatter` (voronoi glass), `prism` (RGB-split blinds with a swipe). These use CSS animation only, so they stop for visitors with reduced motion. For a **ShaderGradient** look, use `--style shader --palette halo|pensive|interstella|universe|mandarin|nighty`. For a **landing-page** feel, use the spotlight hero + CTA buttons (`--kind button`) from design.md §10 and `templates/design/hero-landing.md`, optionally repeating the CTA before the footer with `templates/design/cta-section.md`.
4. End with a footer (design.md §3): license line, credit, back-to-top, plus the footer SVG for polished projects and profiles.
5. Run the core skill's `score_readme.py` and fix the `design` findings (missing dark variant, mixed badge styles, external fonts in SVGs, oversized assets).
6. **Visual check:** if a browser is available, render the README or the SVGs and look at both themes. At minimum, open each SVG once to confirm the title is fully visible.

Never: hotlink a third-party banner by default, put the only copy of the pitch inside an image, use more than 2 animations above the fold, or animate the text in from blank.

## Mode B — Profile README

1. Read `references/profile-readme.md`. Collect (batch in one question): GitHub username, name/role/one-liner, current focus, top skills (or derive from their public repos if they allow), socials, preferred **archetype** (minimal · stats dashboard · creative/animated · code-mode · data/ML · student · OSS maintainer · retro · badges wall · Actions-dynamic · org · game mode · typing · anime/art · fancy fonts · descriptive · simple-but-innovative · icons · just an image; if they name an awesome-github-profile category, use the mapping in profile-readme.md), and dark-mode preference.
2. Start from `templates/profile/<archetype>.md`. Replace every `{{PLACEHOLDER}}`; delete sections with no data rather than leaving placeholders. Generate the profile hero banner and footer with `make_banner.py` (Mode G) in the user's accent colour. Offer the 3D contribution calendar (`workflows/profile-3d.yml`) for profiles that want a 3D visual.
3. Widgets: pick from `references/widgets.md`. Rules: ≤ 4 dynamic cards; use `<picture>` or theme params for dark/light; give each a descriptive alt; add the self-host / Actions fallback comment for stats cards; skill icons only for skills the user really uses (≤ 15). Never invent stats, employers, projects or links: they come from the user or their public profile.
4. If the archetype needs automation (snake, latest blog posts, WakaTime, metrics, the tic-tac-toe game), also write the workflow from `templates/profile/workflows/` (the game also needs `templates/profile/game/tictactoe.py` at `.github/scripts/`) and tell the user which secrets/settings to add.
   For **fancy fonts**, generate every styled string with `python SKILL_DIR/scripts/fancy_text.py "TEXT" --style <style>`; never type the Unicode yourself.
5. Run `score_readme.py --profile` and `check_links.py` from the core skill (if network allowed) and fix failures.
6. Tell the user exactly where it goes: repo named exactly like their username, public, `README.md` at root (org: `.github` repo → `profile/README.md`).

## Final message to the user

Keep it short: which assets and files you wrote, how to preview both themes, and any setup they must do (Actions secrets, making the profile repo public).
