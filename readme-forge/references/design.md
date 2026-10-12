# README visual design system

A README is a page. Good design here comes from **hierarchy, rhythm, restraint, and a consistent palette**, not from piling on widgets. GitHub controls the body font, so your tools are layout, spacing, imagery, badges, and SVG assets you generate.

Generate every visual asset locally with `scripts/make_banner.py` and commit it, usually under `.github/assets/` (or `assets/` for profile repos). Never depend on a third-party render service for the header.

## 1. Hard technical facts (SVG inside a README)

| Works | Doesn't work |
|---|---|
| Inline `<style>` + CSS `@keyframes` | `<script>`, so no JS at all |
| SMIL `<animate>`, `<animateTransform>`, `<animateMotion>` | External resources: Google Fonts `@import`, `<link>`, external `<image href>` |
| Base64 `@font-face` data URIs (subset it, ≤ 30 KB) | Clicks or hovers inside the SVG. Wrap the `<img>` in `<a>` instead |
| `<picture>` + `prefers-color-scheme` around the `<img>` | `prefers-color-scheme` *inside* the SVG (it follows the OS, not the GitHub theme, and the mobile apps always report light) |
| `#gh-dark-mode-only` / `#gh-light-mode-only` (GitHub only) | `<foreignObject>` for anything essential (fragile on mobile and other renderers) |

**Rules that follow from this**
1. Use system font stacks only, unless the user provides a font to embed. `make_banner.py` uses `Segoe UI, -apple-system, Helvetica Neue, Inter, Roboto, Arial` and a matching mono stack.
2. **Ship dark and light variants** and switch them with `<picture>`. Never rely on in-SVG theme media queries.
3. **The first frame must be complete.** Animate decoration, never the text's existence. Thumbnails, link previews, slow loads and rasterisers show frame 0.
4. Ambient loops are slow (≥ 4 s). There are no strobes, and `prefers-reduced-motion` stops everything (a progressive enhancement).
5. Keep header SVGs under 20 KB (100 KB at most). Always set `viewBox`, and use `width="100%"` on the `<img>`.
6. Text that must be searchable or translatable (the pitch) also goes in Markdown, below the banner. The banner's `alt` repeats the title and tagline.

## 2. Header patterns

Pick one per README. Research on top projects (bun, next.js, uv, excalidraw, ollama, tauri, supabase, shadcn/ui):

### A. Centered stack (default for projects)
```html
<a href="https://github.com/OWNER/REPO">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/header-dark.svg">
    <img alt="NAME: one-line pitch" src=".github/assets/header-light.svg" width="100%">
  </picture>
</a>

<p align="center"><b>One-line pitch, 12 words or fewer.</b></p>

<p align="center">
  BADGES (3–5, one style)
</p>

<p align="center">
  <a href="DOCS">Documentation</a> •
  <a href="DEMO">Live demo</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="DISCORD">Community</a>
</p>
```

### B. Minimal left-aligned (libraries, CLIs, terse tools)
H1 + one-sentence pitch + one badge row + a 5–15 line code sample. Use no banner, or a `minimal`/`terminal` banner at `height 220`.

### C. Full-bleed splash (apps, games, design tools)
A wide banner or a product screenshot with dark/light versions, then badges, then the pitch. Uses `glass`, `aurora` or `synthwave`.

### D. Profile hero (personal / org profiles)
A banner with the name as the title and the role as the subtitle, then 3–5 "about" bullets, then the skills row. Profiles can carry richer motion (`wave`, `neon`, `synthwave`, `constellation`, `terminal`).

## 3. Footer patterns (every README ends deliberately)

| Pattern | Use | Markup |
|---|---|---|
| **Quiet** (projects, default) | libraries, tools, companies | `---` → License line → "Made by …" / sponsor logos → back-to-top link |
| **Rule** | polished projects | `make_banner.py --kind footer --style minimal --title "Made with care by NAME"` + back-to-top |
| **Wave** | profiles, playful projects | `--kind footer --style wave --title "Thanks for visiting"`, reusing the header's palette |

Back-to-top: put `<a id="top"></a>` before the header, then `<p align="right"><a href="#top">Back to top ↑</a></p>` in the footer.
Section dividers (optional, for long profiles only): `--kind divider`, at most 2–3 per page.

## 4. Choosing a banner style

| Project / person | Style(s) | Palette |
|---|---|---|
| SaaS, web app, API platform | `aurora`, `glass` | violet, ocean |
| CLI, library, dev tool | `terminal`, `minimal`, `blueprint` | mint, mono, ocean |
| Infra, cloud, DevOps, data platform | `isometric`, `blueprint` | ocean |
| AI/ML, data science, research | `constellation`, `orbit`, `aurora` | ember, violet |
| Ecosystem / framework / monorepo | `orbit`, `isometric` | ember, ocean |
| Game, creative coding, music | `neon`, `synthwave` | cyber, sunset |
| Retro / hobby / fun profile | `synthwave`, `neon` | sunset, cyber |
| Corporate / enterprise / docs | `minimal`, `wave` | mono, ocean |
| Personal profile, general | `wave`, `aurora`, `terminal`, `constellation` | any; match the person's accent colour |
| Announcement, big launch | `bold` | ember, sunset |

If the project has a brand colour, use `--accent "#HEX"` with the closest palette. Show the user 2–3 options (generate them, then render previews) when the choice isn't obvious.

## 5. Colour system
- **One accent, one neutral pair.** Badges, banner accent, links you style, and footer accent all use the same accent family. Mixed palettes look amateur.
- Every palette in `make_banner.py` has dark and light variants with title/subtitle contrast checked at ≥ 4.5:1 against their backgrounds. Light variants use darker accents so they don't wash out.
- Badges: one shields style across the page (`flat` for projects, `for-the-badge` only for profiles). Use Simple Icons brand colours for tech badges, and your accent for project badges (`&color=HEX` without the `#`).
- Don't use colour alone to mean something. Pair it with text or icons.

## 6. Typography and rhythm (in Markdown)
GitHub sets the font, so typography means **hierarchy and spacing**:
- One H1 (or the banner as the H1 equivalent, with the title in `alt`), H2 for sections, H3 sparingly. Never skip levels.
- Section titles are 1–3 words, in sentence case or Title Case, used consistently. Use at most one emoji per heading, and the heading must still have words.
- Paragraphs are 1–3 sentences. Line length is controlled by the content; avoid tables wider than 5 columns because they scroll on phones.
- Rhythm: header block → a gap (`<br>` once) → content → `---` before the footer. Don't stack `<br>`s for spacing.
- Centered alignment only for the header and footer blocks. Body text stays left-aligned.
- Code blocks always have a language tag. Keep inline code for literals (`--flag`, `ENV_VAR`), not for emphasis.
- Bold for key nouns in feature lists. Use italics rarely. No ALL CAPS sentences (small-caps tags inside banners are fine).

## 7. Layout recipes (HTML that GitHub allows)
- **Two columns:** a `<table>` with two `<td valign="top" width="50%">` cells. Leave a blank line after `<td>` so Markdown renders inside it.
- **Feature grid:** a 2×2 or 3×2 table with a bold title and one line each. Keep it scannable.
- **Side-by-side cards** (stats, screenshots): `<p align="center"><img height="160" …> <img height="160" …></p>`, with equal heights and matching themes.
- **Collapsible depth:** `<details><summary><b>Advanced configuration</b></summary> … </details>`, which keeps the first screen clean.
- **Image sizing:** use `width="100%"` for banners and `width="800"` for screenshots. Never use giant raw images.

## 8. Quality bar ("designer pass" checklist)
- [ ] Banner has dark + light variants inside `<picture>`, real alt text, and is wrapped in a link.
- [ ] First frame complete; motion is slow and decorative.
- [ ] One palette across banner, badges and footer; one badge style.
- [ ] Header block: banner → pitch → badges → link row, all centered, no more than one screen tall.
- [ ] Body left-aligned, consistent heading style, no wall of text.
- [ ] Footer present: license + credit + back-to-top (+ footer SVG for profiles).
- [ ] Checked in both GitHub themes and at phone width.
- [ ] `score_readme.py` shows no design warnings.

## 9. Generator quick reference
```bash
python scripts/make_banner.py --list
python scripts/make_banner.py --style aurora --title "orbit-api" --subtitle "Subscription billing for SaaS" --tag "open source" --out .github/assets
python scripts/make_banner.py --kind footer --style wave --title "Thanks for visiting" --out .github/assets
python scripts/make_banner.py --kind divider --palette ember --out .github/assets
python scripts/make_banner.py --style isometric --palette ocean --accent "#0EA5E9" --height 260 --title "kubeforge" --out .github/assets --name hero
python scripts/make_banner.py --gallery /tmp/banners      # preview every style
```
It prints the `<picture>` snippet to paste. Add `--static` to get a version with no motion.

## 10. Inspiration library → what we borrow
Web design galleries use WebGL, JS and hover states. A README can't. This is how each source translates into something GitHub *can* render:

| Source | What it teaches | readme-forge equivalent |
|---|---|---|
| **ShaderGradient** (shadergradient.co) | Three colours bleeding over a curved 3D surface, very slow drift, film grain | `--style shader` with the real presets as palettes: `halo`, `pensive`, `interstella`, `universe`, `mandarin`, `nighty` (`--palette …`) |
| **Supahero** (hero gallery: Linear, Stripe, Raycast, Resend…) | Hero anatomy: announcement pill → 56–80px title, tight tracking, white→60% gradient → 18–20px sub-copy → CTA pair → social proof. Grid or dot field fading out radially, top spotlight glow, 1px horizon beam | `--style spotlight` (pill = `--tag`) + CTA buttons + proof line: `templates/design/hero-landing.md` |
| **Call to Inspiration** (CTA gallery) | Verb-first labels, one bright primary + one ghost secondary, trailing →, a friction reducer underneath, the CTA repeated at the end | `--kind button --variant primary|secondary` (clickable: each button is its own image inside `<a>`) + `templates/design/cta-section.md` |
| **Dark design galleries** | Never pure black (#08090A–#121212). Elevation through lighter surfaces (+3–6%) and white 5–10% borders. Text at 100/62/40%. One desaturated accent, glow on a single focal element | Palettes `midnight` (Linear-like), `carbon` (Vercel-like), `obsidian` (Supabase-like). All have light variants too |
| **Dribbble 2025–26 trends** | Bento grids, soft layered gradients, flowing lines, restrained glass, dark mode | `--style ribbon` (silk strands), `glass`, `aurora`, plus bento layout recipe (§7, a 2–3 column table of short cards) |
| **Figma** | Where designers tweak visuals | Drag any generated SVG into Figma to edit colours and layout. Figma drops SMIL/CSS animation and noise filters, so use `--static` for the Figma copy, edit it, export as SVG, then regenerate the animated version with the same palette (`--accent`). For hand-made Figma banners: frame 1280 wide, outline text, export SVG, and keep them under 100 KB. |

### Landing-page hero recipe (supahero pattern)
```bash
python SKILL_DIR/scripts/make_banner.py --style spotlight --palette midnight --title "Acme" --subtitle "Ship docs your users actually read" --tag "New · v2.0 is out" --out .github/assets
python SKILL_DIR/scripts/make_banner.py --kind button --variant primary   --title "Get started" --href "#quickstart" --out .github/assets --name cta-primary
python SKILL_DIR/scripts/make_banner.py --kind button --variant secondary --title "Read the docs" --href "DOCS_URL" --out .github/assets --name cta-secondary
```
Then fill `templates/design/hero-landing.md`. Rules: one primary CTA per screen, labels are 1–3 words starting with a verb, and the primary is the brightest element. Below the buttons, add at most one line of real proof ("Used by N repos", "MIT licensed", "No sign-up"). Never invent numbers.

### Dark design tokens (for hand-written HTML and colour choices)
| Token | midnight | carbon | obsidian |
|---|---|---|---|
| canvas | #08090A | #000000 | #0E1111 |
| surface | #141518 | #111111 | #1A1F1F |
| border | white 6–8% | white 10% | white 8% |
| text | #F7F8F8 | #EDEDED | #EDEFEF |
| text-secondary | #8A8F98 | #A1A1A1 | #8F9A99 |
| accent | #7C83FF | #FFFFFF / #3B82F6 | #3ECF8E |
Badge colour = the accent hex without `#` (e.g. `&color=7C83FF`), and use the same accent for the banner (`--accent`).
