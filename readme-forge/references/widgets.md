# Widget catalog (profile & project READMEs)

Replace `USER` / `OWNER/REPO`. Every widget below is an `<img>`: **always** give alt text, and prefer `<picture>` for dark/light. Keep ≤ 4 dynamic cards per profile. Check with `scripts/check_links.py --images-only` when network is allowed.

## Reliability tiers

| Tier | Meaning | Use |
|---|---|---|
| **A — static/self-contained** | shields.io, skillicons.dev, files committed by your own Action | default choice |
| **B — shared public instance** | readme-stats, streak, trophy, activity-graph (Vercel/demolab hosted) | OK, but add the fallback comment; they rate-limit popular accounts |
| **C — dead** | anything on `*.herokuapp.com` (Heroku free tier removed Nov 2022); public `github-profile-trophy.vercel.app` and `github-readme-activity-graph.vercel.app` (HTTP 402, Oct 2026) | never use the public URL; replace or self-host |

Hosted services change. When network is allowed, **always run `check_links.py`** on the result. It catches 402/404s and widgets that return an error card instead of a chart.

Fallback comment to put above any Tier-B card:
```html
<!-- Shared public instance can be rate-limited. For reliability, self-host (fork + deploy to Vercel with a PAT)
     or generate the SVG with a scheduled GitHub Action and commit it (see workflows/metrics.yml). -->
```

## Dark / light pattern (GitHub)

```html
<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="https://…&theme=dark">
  <source media="(prefers-color-scheme: light)" srcset="https://…&theme=default">
  <img alt="USER's GitHub stats: stars, commits, PRs, issues" src="https://…&theme=default">
</picture>
```
Simpler alternative: transparent background params (`bg_color=00000000`, `hide_border=true`, `theme=transparent`) work in both modes when text color is mid-contrast.
Legacy alternative: `![alt](url#gh-dark-mode-only)` + `![alt](url#gh-light-mode-only)` (GitHub only; on Hugging Face use `#hf-dark-mode-only` / `#hf-light-mode-only`).

## Stats cards — anuraghazra/github-readme-stats (Tier B)

| Card | URL |
|---|---|
| Stats | `https://github-readme-stats.vercel.app/api?username=USER&show_icons=true&hide_border=true&theme=THEME` |
| Top languages | `https://github-readme-stats.vercel.app/api/top-langs/?username=USER&layout=compact&hide_border=true&theme=THEME` |
| Repo pin | `https://github-readme-stats.vercel.app/api/pin/?username=USER&repo=REPO&theme=THEME` |
| WakaTime | `https://github-readme-stats.vercel.app/api/wakatime?username=WAKAUSER&layout=compact&theme=THEME` |

Useful params: `include_all_commits=true`, `count_private=true` (only meaningful self-hosted with your PAT), `hide=issues,contribs`, `rank_icon=github|percentile`, `card_width=`, `langs_count=8`, `exclude_repo=a,b`, `hide_title=true`, `locale=`.
Themes: `default`, `dark`, `radical`, `merko`, `gruvbox`, `tokyonight`, `onedark`, `cobalt`, `synthwave`, `highcontrast`, `dracula`, `github_dark`, `transparent`, `catppuccin_latte`, `catppuccin_mocha`, `nord`, `rose_pine`, `vue`, `buefy`…
Top-languages caveat: it's bytes in public repos, so vendored/notebook code skews it — mention to the user, or `exclude_repo` the outliers.

## Streak — DenverCoder1/github-readme-streak-stats (Tier B)
`https://streak-stats.demolab.com?user=USER&theme=THEME&hide_border=true` (themes: `default`, `dark`, `radical`, `tokyonight`, `github-dark-blue`, `transparent`…). Old `github-readme-streak-stats.herokuapp.com` URLs are dead → replace.

## Trophies — ryo-ma/github-profile-trophy (**self-host only**)
The public `github-profile-trophy.vercel.app` instance returned **HTTP 402 (Vercel deployment disabled)** when checked in Oct 2026, so copied embeds show a broken image. Only include trophies if the user self-hosts (fork → deploy to Vercel → set `GITHUB_TOKEN`), then use `https://YOUR-DEPLOYMENT.vercel.app/?username=USER&theme=onedark&no-frame=true&no-bg=true&row=1&column=7`. Otherwise use the streak card or lowlighter/metrics `plugin_achievements`.

## Activity graph — Ashutosh00710/github-readme-activity-graph (**self-host only**)
The public `github-readme-activity-graph.vercel.app` instance also returned **HTTP 402** in Oct 2026, and the old herokuapp URL is dead. Self-host it (`/graph?username=USER&theme=github-compact&hide_border=true&area=true`; dark themes `github-compact`, `tokyo-night`, `react-dark`; light `minimal`, `github-light`), or use lowlighter/metrics `plugin_isocalendar` / the snake as the "activity" visual.

## Typing animation — DenverCoder1/readme-typing-svg (Tier A-ish)
`https://readme-typing-svg.demolab.com?font=Fira+Code&weight=500&size=22&pause=1000&color=COLORHEX&center=true&vCenter=true&width=600&lines=Line+one;Line+two;Line+three`
Accessibility: animated + text in an image. **Alt must contain all lines** (e.g. `alt="Typing: Backend engineer; Rust & Go; Open-source maintainer"`). Use at most one. Offer a static `<h3>` alternative for minimal styles.

## Skill icons — tandpfun/skill-icons (Tier A)
`https://skillicons.dev/icons?i=py,ts,react,nodejs,docker,postgres,aws&theme=dark&perline=8`
- `theme=light|dark`. Wrap in `<picture>` for both.
- **Only icons for skills the user actually uses** (≤ 15). Derive from their languages if they allow; never pad.
- Common ids: `js ts py go rust java kotlin cpp c cs php ruby swift dart r scala elixir haskell lua bash powershell html css sass tailwind bootstrap react nextjs vue nuxt svelte angular astro nodejs deno bun express nestjs fastapi flask django spring dotnet rails laravel graphql postgres mysql mongodb redis sqlite supabase firebase prisma docker kubernetes aws gcp azure vercel netlify cloudflare nginx linux git github gitlab githubactions terraform ansible pytorch tensorflow sklearn opencv figma vscode vim neovim unity unreal godot flutter androidstudio arduino raspberrypi`.
- Accessible alt: `alt="Skills: Python, TypeScript, React, Node.js, Docker, PostgreSQL, AWS"`.
Alternatives: Devicon (`https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg`, 40px, one `<img>` per skill with its own alt — best for screen readers), shields "for-the-badge" with `logo=`.

## Contribution snake — Platane/snk (Tier A via your own Action)
Generated by `templates/profile/workflows/snake.yml` into the `output` branch:
```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/USER/USER/output/github-snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/USER/USER/output/github-snake.svg">
  <img alt="Animated snake eating USER's GitHub contribution graph" src="https://raw.githubusercontent.com/USER/USER/output/github-snake.svg">
</picture>
```
User must: enable Actions write permissions (Settings → Actions → Workflow permissions → Read and write), then run the workflow once manually.

## lowlighter/metrics (Tier A via Action)
Rich SVG (isocalendar, languages, habits, achievements, stars, followup…), committed to the repo by `workflows/metrics.yml`. Needs a classic PAT stored as secret `METRICS_TOKEN`. Embed: `![USER's GitHub metrics](/github-metrics.svg)`.

## Latest blog posts — gautamkrishnar/blog-post-workflow (Tier A via Action)
README markers:
```md
### Latest posts
<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->
```
Workflow `workflows/blog-posts.yml`, `feed_list:` dev.to `https://dev.to/feed/USER`, Medium `https://medium.com/feed/@USER`, Hashnode `https://BLOG.hashnode.dev/rss.xml`, any RSS/Atom.

## WakaTime — athul/waka-readme (Action) or readme-stats wakatime card
Action needs `WAKATIME_API_KEY` secret and markers `<!--START_SECTION:waka-->` / `<!--END_SECTION:waka-->`.

## Other popular widgets
| Widget | URL / note |
|---|---|
| Profile views | `https://komarev.com/ghpvc/?username=USER&style=flat-square&color=blue&label=Profile+views` — vanity metric; optional |
| LeetCode card | `https://leetcard.jacoblin.cool/LCUSER?theme=dark&font=Fira%20Code&ext=heatmap` |
| Stack Overflow | `https://stackoverflow-card.vercel.app/?userID=ID&theme=dark` (Tier B) |
| Spotify now playing | novatorem/novatorem — **requires self-hosting** with Spotify API keys |
| Star history (project) | `https://api.star-history.com/svg?repos=OWNER/REPO&type=Date` (+`&theme=dark` in a `<picture>` source) |
| Contributors grid (project) | `https://contrib.rocks/image?repo=OWNER/REPO` (alt: "Contributors to REPO") |
| Repobeats activity (project) | generate an embed at repobeats.axiom.co (unique key per repo — can't be guessed) |
| Readme quotes / jokes / memes | low signal, Tier B; include only for "creative" archetype on request |

## Social badges (shields.io, Tier A)
`https://img.shields.io/badge/LABEL-HEXCOLOR?style=for-the-badge&logo=SLUG&logoColor=white`
Slugs from Simple Icons: `github`, `x`, `bluesky`, `mastodon`, `youtube`, `instagram`, `discord`, `devdotto`, `medium`, `hashnode`, `kaggle`, `leetcode`, `stackoverflow`, `huggingface`, `gmail`, `substack`, `buymeacoffee`, `kofi`, `githubsponsors`.
**LinkedIn** (and some other brands) were removed from Simple Icons on brand request — `logo=linkedin` may not render; use the badge without a logo (`https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge`) or a Devicon image.
Always wrap: `[![LinkedIn: Jane Doe](badge-url)](https://linkedin.com/in/…)` — alt says platform + who.

## Headers, banners and 3D visuals

**Default: generate your own** with `scripts/make_banner.py` (15 animated styles, dark and light versions, frame 0 always complete). It is self-hosted, so it can't rate-limit or go down. See `design.md`. Use the hosted services below only when the user asks for them.

| Tool | What it does | Reliability | Notes |
|---|---|---|---|
| kyechan99/capsule-render | Wave, egg, shark, slice, rect, soft, rounded, cylinder, venom, … headers and footers. `https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=NAME&fontSize=60&animation=fadeIn` (`section=footer` for footers) | Tier B (public Vercel instance) | Text can't contain `#`, `&` or `/`. `animation=fadeIn` makes frame 0 empty. `make_banner.py --style wave` is the self-hosted equivalent. |
| wei/socialify | 1280×640 project card (name, description, stars, language, logo, pattern). `https://socialify.git.ci/OWNER/REPO/image?theme=Dark&pattern=Circuit%20Board&language=1&stargazers=1` | Tier B | Better as the repo's **social preview** (Settings → Social preview) than as the README header. |
| yoshi389111/github-profile-3d-contrib | **3D isometric contribution calendar** with radar and pie charts, for profiles | Tier A (your own Action) | Workflow: `templates/profile/workflows/profile-3d.yml`. Files: `profile-green-animate.svg`, `profile-night-rainbow.svg`, `profile-season-animate.svg`, `profile-gitblock.svg`, … Use `<picture>` to pair a night theme (dark) with a green/season theme (light). |
