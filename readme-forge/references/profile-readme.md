# Profile README guide

A profile README is a **landing page about a person (or org)**. Readers are recruiters, collaborators, and other developers, and they spend 10–30 seconds on it. It should answer: who are you, what do you work on, what are you good at, what have you shipped, and how do I reach you?

## Interview (ask once, batched)
1. GitHub username (needed for every widget URL).
2. Name, role/title, location (optional), one-line headline.
3. Current focus: working on, learning, open to (jobs, collaboration, mentoring).
4. Top skills: ask the user, or derive from their public repos' languages if they allow (`https://api.github.com/users/USER/repos?per_page=100`, network permitting). **Cap at 15.**
5. 2–4 projects to feature (repo names + one line each), plus any blog, talks, or publications.
6. Contact/social links (email, LinkedIn, X/Bluesky, personal site, dev.to/Medium/Hashnode, Kaggle, LeetCode, HF).
7. Style archetype (below) and theme preference (dark, light, or both).
8. Optional automation: snake, latest posts, WakaTime, metrics.

If the user says "just make it", produce the **minimal** or **stats-dashboard** archetype with the information you have, delete sections with no data, and list what's missing.

## Archetypes (`templates/profile/`)
Taken from the categories used by awesome-github-profile-readme and its gallery. Pick one, or combine at most two.

| Archetype | File | Best for | Signature elements |
|---|---|---|---|
| Minimal | `minimal.md` | senior devs, researchers | 5–10 lines: headline, focus, links. No widgets. |
| Stats dashboard | `stats-dashboard.md` | active OSS contributors | stats + top-langs + streak (themed), skill icons |
| Creative / animated | `creative.md` | frontend/design devs | banner, typing SVG, snake, GIF (≤ 2 animations) |
| Code mode | `code-mode.md` | backend/systems devs | an "about me" as a code block (`const me = {…}` / Python dataclass) |
| Data / ML | `data-scientist.md` | ML/DS/AI | HF, Kaggle, papers, models/datasets table, notebooks |
| Student | `student.md` | students, bootcamp grads | learning journey, coursework projects, hackathons, open to internships |
| OSS maintainer | `oss-maintainer.md` | maintainers | projects table with stars/downloads badges, sponsor links |
| Retro / terminal | `retro.md` | fun, hobbyist | ASCII art in `text` blocks, terminal-style sections |
| Badges wall | `badges-wall.md` | quick, colorful | for-the-badge rows for stack and socials |
| Actions-dynamic | `actions-dynamic.md` | bloggers, tinkerers | auto-updated latest posts, WakaTime, metrics, snake |
| Organization | `org-profile.md` | companies, communities | mission, products, how to contribute, links, hiring |

## Layout rules
- **Top:** greeting + name (H1 or H2), then a one-line headline. Optional banner (1200×300 or so, with alt text).
- **About:** 3–5 bullets: working on, learning, ask me about, fun fact (optional), how to reach me.
- **Skills:** icon row(s) with a single descriptive alt, or a grouped table (Languages / Frameworks / Tools / Cloud).
- **Featured work:** a 2–4 row table or pinned-card widgets. Each item gets one line saying what it does and its result.
- **Stats:** at most 2–3 cards side by side, themed to match each other.
- **Contact:** a badge row or plain links.
- Optional: latest posts (Action-driven), a quote, visitor counter (a vanity metric, keep it small).

## Side-by-side cards
```html
<p align="center">
  <img height="165" alt="USER's GitHub stats" src="…api?username=USER&show_icons=true&hide_border=true&theme=tokyonight">
  <img height="165" alt="USER's most used languages" src="…top-langs/?username=USER&layout=compact&hide_border=true&theme=tokyonight">
</p>
```
Use the same `height` and theme, and `hide_border=true`, so the cards look like one set.

## Org profile (`ORG/.github` → `profile/README.md`)
Mission in one line, products/projects table, getting involved (good first issues, discussions, Discord), links (site, docs, blog, careers), code of conduct, and security contact. No personal stats widgets. Use the org's brand banner with dark/light versions.

## Checklist before handing over
- [ ] Every `USER` and placeholder is replaced. Sections without data are deleted.
- [ ] All widget URLs come from widgets.md (no herokuapp). Fallback comment above Tier-B cards.
- [ ] Theme: `<picture>` or transparent params, and the cards match each other.
- [ ] Alt text on every image. The typing SVG alt contains all its lines.
- [ ] ≤ 4 dynamic cards, ≤ 2 animations, ≤ 15 skill icons.
- [ ] `score_readme.py --profile` ≥ 85; `check_links.py` clean (if network is allowed).
- [ ] Tell the user: the repo must be named exactly the username, be public, and have README.md at the root. Workflows need Actions read/write permission plus any listed secrets.
