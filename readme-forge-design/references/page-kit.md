# Page kit: a whole README built from SVG cards

Banners decorate the top and bottom of a README. The page kit designs **every block in between**: one JSON spec in, a full set of matching cards (light + dark) and a finished `README.md` out. The look is "keynote": soft neutral cards, bold tight sans headlines with an italic serif accent phrase, small mono caps labels, and four-colour sparkles.

```bash
python SKILL_DIR/scripts/make_page.py --init profile > page.json      # or: --init project
# fill page.json from the user's real data (every {{…}} must go)
python SKILL_DIR/scripts/make_page.py --spec page.json --preview preview.html
python SKILL_DIR/scripts/make_page.py --list                          # themes, visuals, blocks, icon names
```

The script writes `<assets>/<name>-light.svg` + `<name>-dark.svg` for every card and the README next to the spec (override with `--readme`). It refuses to run while any `{{PLACEHOLDER}}` is left. Working examples: `examples/keynote-profile/` (a personal profile), `examples/keynote-coder/` (a developer profile with the code, portrait, badge-wall and project-link features) and `examples/keynote-project/` (a project README).

## When to use it

| Situation | Use |
|---|---|
| GitHub profile that should look like a designed landing page | page kit, `--init profile` |
| Project README for an app, product or showcase repo, where the user asks for a "designed" or "professional" look | page kit, `--init project`: cards for the hero, features and stack, **real Markdown** for install and usage |
| Library or CLI README that people copy commands from | a banner (Mode G) + plain Markdown. Cards would hide the text |
| User only wants a header or footer | `make_banner.py` (Mode G) |

## Spec

```jsonc
{
  "theme": "keynote",            // keynote · aurora · sunset · ocean · forest · mono
  "accents": ["#4285F4", "..."], // optional: 1–4 brand colours instead of the theme's
  "motion": "ambient",           // ambient (default) · entrance · static
  "github": "USER",              // used by the stats block
  "readme": "README.md",         // relative to the spec
  "assets": "assets/hello",      // relative to the README
  "blocks": [ … ]                // rendered top to bottom
}
```

Text fields accept `*accent phrase*` (italic serif in the accent colour) and `**bold**` where noted.

| Block | Fields | Card |
|---|---|---|
| `hero` | `window`, `prompt`, `greeting` (serif line), `title` (bold line), `meta` [≤ 4 strings, `**bold**` ok] or `roles` [2–5 strings that rotate, with a blinking caret; the first is visible in frame 0], `status` (pill), `logo` (image path) or `initials`, `drips` (default true), `href` | 1200×600 terminal window with a dripping edge (1200×460 with `"drips": false`) |
| `dock` | `items`: [{`label`, `handle`, `icon`, `href`}] (≤ 7) | 144×176 icon tiles, side by side |
| `section` | `title`, `subtitle` (serif) | 1200×112 numbered header, `01 / 05` counted automatically |
| `about` | `eyebrow`, `headline` (`*accent*`), `body`, `quote`, `eyebrow_right`, `items`: [{`label`, `text`}] (≤ 5) | two-column card |
| `code` | `data` (a JSON object: strings, numbers, lists, one level of nesting), `lang` (`yaml` / `json`), `file` (tab name). A string with `  # note` gets a comment | "about me as code": an editor window with line numbers and syntax colours |
| `portrait` | `image` (PNG), `dots` (16–72, default 46), `caption`, `subtitle`, `color` (`accent` gradient / `ink`), `tone` (`photo`, the default: dark mode draws brightness so faces stay positive; `shape`: both themes draw the dark parts, for logos and silhouettes), `width` (default `50%`) | dot-matrix (halftone) portrait. Only the dots are stored, never the photo |
| `stack` | `groups`: [{`label`, `items`: [icon name or {`name`, `icon`, `color`}]}] | icon grid, 7 per row |
| `projects` | `items`: [{`size`: `feature` / `card` / `link`, `tag`, `color` (0–3), `title`, `subtitle`, `description`, `metrics` [{`value`, `label`}] (feature), `highlight` (card chip), `tech` [], `visual`, `cta`, `icon` (link), `href`, `links` [{`label`, `href`}] (card)}] | feature 1200 wide, cards in pairs (49%), links in threes (32%). When any card has `links`, the cards go in a two-column table with a `Live ↗ · Code ↗` row under each |
| `certs` | `items`: [{`name`, `issuer`, `icon` or `image` (badge PNG/SVG), `year`}], `columns` (2–5, default 4) | badge / certification wall: one card of tiles |
| `achievements` | `items`: [{`eyebrow`, `title`, `subtitle`, `description`, `chip`, `image` (photo path) or `icon`, `href`}] | 590×430 cards in pairs, photo or colour emblem on the left |
| `stats` | `user`, `snake` / `stats` / `streak` (default on), `languages`, `calendar3d` (true or [light, dark] file names), `views` (bools, default off), `leetcode`, `codeforces` (usernames), `all_commits`, `title`, `snake_repo`, `snake_files` [light, dark] | themed stats, streak and top-languages cards, LeetCode and Codeforces cards, the 3D calendar and snake from your own Actions, and a view counter |
| `markdown` | `text` | real Markdown, outside the centred card column |
| `footer` | same as `hero`; the card is mirrored so the drips rise | contact call to action |

Paired cards (project `card`s, achievements) get the same height automatically. Every block also takes `alt` to override the generated alt text.

**Visuals** for project cards: `network` (nodes and a dashed route), `wave` (voice bars), `chart` (rising line), `grid` (vision / pixels), `chat` (message bubbles), `orbit` (planets), `code` (code lines). Pick the one that matches what the project does.

**Icons:** 117 brand icons from Simple Icons (`--list` prints them), plus line icons `mail`, `globe`, `link`, `file`, `phone`, `pin`, `rss`, `code`, `terminal`, `star`. Common aliases work (`aws`, `gcp`, `node`, `next`, `k8s`, `postgres`, `gemini`, `java`, `html`, `css`, `cf`, `lc`, `email`, `website`, `twitter`). Anything else becomes a two-letter monogram, so a missing icon never breaks the page.

## Learning from a sample README

Users often paste a README they like ("make mine like this"). Read it for **patterns**, map each one to the kit, and leave its content behind (rule 0). The patterns seen most often, and what to use instead:

| Pattern in the sample | Page-kit equivalent | Why |
|---|---|---|
| capsule-render wave header or footer, custom header services | `hero` card (or `make_banner.py --style wave` for a classic banner) | self-hosted, real dark variant, text not hidden in a third-party URL |
| readme-typing-svg banner ("Hi, I'm …; Developer; …") | `hero` with `roles` | rotates without an external service, and the first role shows in frame 0 and in link previews |
| Big portrait / dot-matrix photo | `portrait` | halftone dots in the theme colours, the photo itself never leaves the user's machine |
| `about.yaml` / `const me = {…}` code block | `code` | same idea, with syntax colours, line numbers and a real dark mode |
| Bullet "about me" (🔭 working on, 🌱 learning…) | `about` items (`Building`, `Exploring`, `Open to`) | same facts, readable at a glance |
| for-the-badge social badges, skillicons social icons | `dock` | one consistent tile per link, with the handle under it |
| skillicons wall of 30+ logos | `stack` with 3–5 groups, ≤ 7 per row | grouped stacks read as expertise; walls read as noise. Cut to the tools the user really uses |
| Project table with logo, description, stack, "Live · Code" | `projects` cards with `links` | equal-height cards, an illustration per project, the links kept as real links |
| Wall of certification badge images | `certs` (`image` per tile if the user has the badge files) | aligned tiles with name, issuer and year instead of mismatched image sizes |
| LeetCode / Codeforces cards | `stats` `leetcode` / `codeforces` | themed for light and dark, linked to the profile |
| github-readme-stats, top languages, streak | `stats` `stats` / `languages` / `streak` | colours match the page; `include_all_commits` stays off (it errors on the public instance) |
| 3D contribution calendar, snake | `stats` `calendar3d` / `snake` + the Actions in `templates/profile/workflows/` | generated in the user's repo, no shared host |
| Trophies, activity graph, MonkeyType card, `*.herokuapp.com` widgets | leave out | their public hosts are dead or disabled (402/404, checked Oct 2026); see `widgets.md` |
| Profile-view counter, quotes, coding GIFs | optional; offer, don't add | vanity or decoration that competes with the work |
| Repeated emoji headings, `---` between every section | `section` cards | numbered headers carry the rhythm on their own |

Keep what makes the sample personal (its order of sections, its tone, the projects it leads with), but rebuild it with the user's facts.

## Rules

0. **A sample README is a design reference, not content.** When the user shares their own README to show the look they want, copy its layout, rhythm and card types, never its words. Their name, contacts, projects and photos go only into *their* README, never into this skill's files, examples or templates. Shipped examples use the fictional persona in `examples/keynote-profile/` (`example.com` links, the `octocat` account), and a unit test enforces that.
1. **Facts come from the user or the repo.** Never invent metrics, awards, employers or descriptions. If a project has no description, leave the field out; the card still looks complete. For project READMEs, run the core skill first and keep every command in a `markdown` block, where `verify_readme.py` can check it.
2. **Searchable text stays text.** For projects, put the pitch, badges, install and usage in `markdown` blocks. Cards are for the visual layer, and their alt text repeats what they say.
3. **Short copy.** Hero title ≤ 18 characters, greeting ≤ 30, section titles 1–3 words, subtitles ≤ 5 words, project descriptions ≤ 2 sentences, `highlight` and `chip` ≤ 20 characters. The script shrinks text to fit, but short copy is what makes it look designed.
4. **One theme per page.** Pick it from the brand or the person: `keynote` for Google-ish four colours, `aurora` for AI and creative work, `ocean` for infra and data, `forest` for sustainability and climate, `sunset` for consumer and playful, `mono` for minimal and serious. Pass `accents` to match a logo.
5. **Motion:** `ambient` animates only decoration (sparkles, ripples, bars), so the first frame is complete. `entrance` also slides each block in. It looks livelier, but frame 0 is blank in link previews, so use it only on profiles and only when asked. `static` turns all animation off (also the right choice for Figma). CSS only, so `prefers-reduced-motion` stops everything.
6. **Weight:** about 5–45 KB per card without photos. Resize achievement photos to ~600 px wide first (the script warns above 250 KB).

## Workflow

1. Gather the content (profile: the batched interview in `profile-readme.md`; project: the core skill's facts).
2. `--init`, fill the spec, delete blocks that have no data.
3. Run with `--preview preview.html` and open it. It shows both themes on GitHub's page colours. Check that no text is clipped and the paired cards line up.
4. Run the core skill's `score_readme.py` (`--profile` for profiles) and `check_links.py` when network is allowed.
5. Tell the user where the files go and any setup: the snake needs `templates/profile/workflows/snake.yml`; stats cards are a shared public instance (Tier B in `widgets.md`).

Re-run the script after every spec change. Don't hand-edit the SVGs, because the next run overwrites them.
