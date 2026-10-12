# Quality rubric & lint rules

`scripts/score_readme.py` implements this rubric. Use the script for the numbers and your own judgment for what it can't see, such as whether the pitch is clear or whether the examples are realistic.

## Project README (100, or 110 with `--repo` normalized to 100)

| Category | Pts | Full marks when |
|---|---|---|
| Identity | 15 | H1 title · one-sentence pitch in the first 30 lines · 3–10 badges · Features/Overview section |
| Getting started | 25 | Install/Quickstart section in the first ~40% (or ≤ line 60) · shell code blocks · Usage/Examples · ≥ 2 code blocks · prerequisites |
| Structure | 15 | ≥ 3 H2 sections · TOC if > 6 sections · no empty sections · 25–700 lines |
| Visuals | 10 | architecture/how-it-works (Mermaid or section) · screenshot/demo/logo · dark/light handling |
| Community | 15 | License · Contributing · support/contact · development/testing instructions |
| Quality & a11y | 20 | lint findings subtract (ERROR 3, WARN 1.5, INFO 0.25; same kind counted ≤ 3×); scaled down for very short READMEs |
| Drift (`--repo`) | 10 | README commands, package manager, env vars, license and runtime versions match the repo |

Grades: **A ≥ 90 · B ≥ 80 · C ≥ 70 · D ≥ 55 · F**. Target ≥ 85 for a new README. A missing demo image costs about 4–5 points and doesn't block 85 by itself. Scores usually stall below 85 because of missing install/usage information or open TODOs that only the user can answer. Say which.

**Known blind spots** (check these yourself): the scorer doesn't verify that documented CLI flags or subcommands exist in the code, that a hand-written `--help` block matches real output, or that API endpoints in a table match the routes. A high drift score means "no contradictions found", not "everything is documented".

## Profile README (100)
Intro 20 (greeting/name, role, current focus) · Skills 15 (section/icons, ≤ 30 icons) · Projects 15 · Contact 15 (≥ 2 channels) · Widgets 15 (≤ 6, themed, no dead hosts) · Quality & a11y 20.

## Hugging Face card (100)
Frontmatter 40 (license valid, task/library/base_model for models; task_categories/size for datasets; sdk/title/colors/app_file for Spaces) · Sections 40 (the required sections for each card type, plus a runnable snippet) · Quality & a11y 20.

## Lint rules

| Level | Rule | Fix |
|---|---|---|
| ERROR | image without alt text | describe the content: "Dashboard showing weekly active users" |
| ERROR | relative link/image target missing | fix the path, or use an absolute URL |
| ERROR | unfilled placeholder (`{{X}}`, `your_username`, `YOUR_API_KEY`, lorem ipsum) | fill it in, or delete the line |
| ERROR | dead widget host (`*.herokuapp.com`) | replace using widgets.md |
| ERROR | README uses a package manager/script/make target that doesn't exist | use the analyzer's commands |
| WARN | multiple H1 · heading level skip · emoji-only heading | fix the hierarchy |
| WARN | non-descriptive alt ("image", "logo") or link text ("here", "click here") | make it descriptive |
| WARN | in-page anchor matches no heading | GitHub slug: lowercase, spaces → `-`, punctuation dropped |
| WARN | filler/marketing phrase | replace with a fact or a number |
| WARN | fragile widget host | add a fallback comment or self-host |
| WARN | > 2 animated images | keep 1–2, give static alternatives |
| WARN | env var in `.env.example` not documented | add it to the Configuration table |
| WARN | paragraph > ~150 words | split it, or turn it into a list |
| INFO | code block without a language | add `bash`, `python`, `ts`, etc. |
| INFO | long bare URL | `[descriptive text](url)` |
| INFO | TODO comments remaining | list them for the user |

## Things the script can't check: review these yourself
- [ ] Does the pitch say **what it is and who it's for** without jargon?
- [ ] Does the quickstart actually produce a visible result? Is the expected output shown?
- [ ] Are the examples realistic (real flags, real API names) and do they cover the most common task first?
- [ ] Is every claim backed by something visible: a number, a link, a code sample?
- [ ] Does the architecture diagram match the code, and is it ≤ 15 nodes with labeled edges?
- [ ] Is the README scannable: short paragraphs, meaningful headings, tables for reference data?
- [ ] Do dark and light modes both look right? Do images have a transparent or neutral background?
- [ ] Does it read well on a phone? No wide tables with more than 5 columns, no huge images.
- [ ] Has outdated content been removed (deprecated install methods, dead links, old screenshots)?
- [ ] Is the tone consistent and the person/tense consistent ("you" + present tense)?

## CI guard against drift
Offer this to users who want the README kept honest:
```yaml
# .github/workflows/readme.yml
name: README check
on:
  pull_request:
    paths: ["README.md", "package.json", "pyproject.toml", "Makefile", ".env.example"]
jobs:
  readme:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: python tools/readme-forge/score_readme.py README.md --repo . --min 80
```
(Copy `scripts/analyze_repo.py` and `scripts/score_readme.py` into `tools/readme-forge/` in their repo.)
