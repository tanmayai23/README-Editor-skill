# Scorer validation: exemplary vs neglected READMEs

Does `readme-forge/scripts/score_readme.py` give higher scores to READMEs that people hold up as good
than to READMEs nobody looked after? This folder holds the repo list, the scores and the scripts to
rerun the check. It is a proxy for human judgment, not a study of human raters.

## Method

All data was collected on 2026-10-19 (UTC). Every README is pinned to the default-branch commit SHA in
[`repos.csv`](repos.csv). The README text itself is not committed because it belongs to other people.
To get it back, fetch the files at those SHAs.

**Well-regarded (25).** Source: the `## Examples` section of
[matiassingers/awesome-readme](https://github.com/matiassingers/awesome-readme) at commit `67494300e0a6`.
Rule: take the GitHub links in list order (the list is alphabetical) and keep the first 25 that point to a
repository. Skip links that are not `owner/repo`, repos that no longer exist, archived repos, and repos
whose README is not Markdown. One repo was skipped: `ankitwasankar/mftool-java` (404). Renamed repos
are recorded under their current name: `dbt-labs/dbt-core` is now `dbt-labs/dbt` and
`doomemacs/doomemacs` is now `doomemacs/core`.

**Neglected (25).** For each of Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, PHP and C#, one
GitHub search was run with `sort=updated`, `order=desc` and `per_page=50`:

```
language:<LANG> stars:0..1 created:2019-01-01..2023-12-31 pushed:<2024-01-01 size:>50 fork:false archived:false
```

Repos were picked round-robin across the languages in that order until there were 25 (3 each, except
PHP and C# with 2). Repos without a Markdown README were skipped, which removed 12 candidates.

**Scoring.** Each README was scored with `score_readme.py <README> --json` in the default project mode.
`--repo` was not used because the code was not checked out, so the `drift` category is absent and the
total is out of the other six categories. The scorer checks that relative links and images exist on disk,
so two runs were made:

- **In-tree** ([`results.csv`](results.csv), the primary result): the README sits at the root of a stub
  copy of its repo. The stub has every path from the GitHub trees API at the pinned SHA, as empty files.
  No code was downloaded. This matches how the scorer is meant to be used.
- **README-only** ([`results-readme-only.csv`](results-readme-only.csv)): the README file on its own. Every
  working relative link becomes an ERROR, so this run is biased against well-illustrated READMEs. It is
  shown to make that bias visible.

No input crashed the scorer: all 50 files scored in both runs.

## Results

Output of `python bench/scorer-validation/analyze.py`, unedited:

| run | group | n | mean | median | stdev | min | max |
|---|---|---|---|---|---|---|---|
| in-tree | good | 25 | 67.5 | 68.0 | 11.1 | 42 | 83 |
| in-tree | neglected | 25 | 37.0 | 35.0 | 19.1 | 6 | 87 |
| README-only | good | 25 | 62.9 | 65.0 | 12.0 | 40 | 78 |
| README-only | neglected | 25 | 36.4 | 35.0 | 18.6 | 6 | 84 |

| run | AUC of total score | good ≥ 55 | neglected ≥ 55 | good ≥ 70 | neglected ≥ 70 |
|---|---|---|---|---|---|
| in-tree | **0.914** | 21/25 | 4/25 | 12/25 | 1/25 |
| README-only | 0.891 | 20/25 | 4/25 | 9/25 | 1/25 |
| *baseline: README line count* | *0.979* | | | | |

AUC is the chance that a randomly chosen good README scores higher than a randomly chosen neglected one,
with ties counted as half. It equals Mann–Whitney U / (n1·n2). 0.5 means no separation and 1.0 means
perfect separation.

**Per category (in-tree run).** The AUC column shows which parts of the rubric separate the two groups.

| category | max | good mean | neglected mean | diff | AUC |
|---|---|---|---|---|---|
| identity | 15 | 13.0 (87%) | 8.7 (58%) | +4.3 | 0.918 |
| getting-started | 25 | 14.8 (59%) | 5.8 (23%) | +9.0 | 0.786 |
| structure | 15 | 12.6 (84%) | 9.6 (64%) | +3.0 | 0.701 |
| visuals | 10 | 5.4 (54%) | 0.5 (5%) | +5.0 | 0.959 |
| community | 15 | 10.2 (68%) | 1.8 (12%) | +8.4 | 0.910 |
| quality | 20 | 11.5 (57%) | 10.7 (54%) | +0.7 | **0.539** |

In the README-only run, quality is inverted: good 6.7 against neglected 10.2, AUC 0.333.

### Failure cases (in-tree run)

Lowest-scored good READMEs:

| score | repo | main reason |
|---|---|---|
| 42 | chroline/well_app | A mobile app with store links rather than an install section, so getting-started scores 0. Uses six emoji H1 sections. The one-line pitch sits below the HTML badge block, past the first 40 lines that the scorer reads. Badges have no alt text. |
| 46 | alichtman/stronghold | Uses setext headings (`**Usage**` underlined with `---`), which the scorer does not parse. Its Usage and Installation sections are not seen, and its Markdown logo image does not count as a title. |
| 50 | CCOSTAN/Home-AssistantConfig | A configuration repo, so it has no install or usage section. 154 badges. |
| 54 | dmunish/reach | Has no install or usage section by design (a showcase README). Many icons have no alt text. |
| 56 | day8/re-frame | An essay-style README that sends readers to its docs site, so getting-started scores 0. |

Highest-scored neglected READMEs:

| score | repo | main reason |
|---|---|---|
| **87** | AdnanOlarmmi/School-Library | A coding-bootcamp README template filled in mechanically. It has every expected heading (TOC, Getting Started, Prerequisites, Usage, Tests, Contributing, FAQ, License). **This is the highest score of all 50 READMEs.** |
| 58 | jacksturt/questasyApp | The unmodified `create-next-app` boilerplate README. It describes Next.js, not the project. |
| 58 | AlessDeveloper01/Frontend-Ecommerce | The same `create-next-app` boilerplate. |
| 56 | henryosei/awc | A short but real README (overview, features, usage, license). This is arguably a fair score: the group label is noisy here. |
| 54 | oxakromax/Monitor_UipathMonitor | A real, useful Spanish README. A fair score, and arguably too low, because `Instalación` does not match the `install` pattern. |

## Rubric weaknesses observed

These are reported here and not fixed.

1. **It rewards template compliance, not content.** Most points come from section headings being present.
   A filled-in template (87) and framework boilerplate (58) beat five READMEs from awesome-readme. Nothing
   checks that the text is about this project.
2. **The quality category does not separate the groups (AUC 0.54).** The penalty for missing image alt
   text is ERROR level. 14 of 25 good READMEs have this ERROR (badges and icons in `<img>` without
   `alt`), against 1 of 25 neglected READMEs. Meanwhile a README with no images or links has nothing to lint
   and keeps full marks: oxakromax gets 20/20 and School-Library 19.8/20. The penalties measure how much there is to lint as much as how good
   the README is.
3. **Getting-started is library-centric and depends on heading names.** It gives 0 to apps, configuration
   repos and docs-site READMEs (well_app, Home-AssistantConfig, re-frame, reach). It also misses
   non-English headings (`Instalación`).
4. **Markdown parsing gaps cause false findings:**
   - Setext headings are ignored (stronghold).
   - Headings are read from text with inline code stripped, so `` ### `app = choo([opts])` `` yields a
     wrong anchor (choo).
   - Link and image markup inside a heading is not removed before slugging (shallow-backup, areg-sdk).
   - Percent-encoded anchors such as `#%EF%B8%8F-contacts` are not decoded (Oidc.Server).
   - A Markdown `![logo](…)` image does not count as a title, though an HTML `<img … logo>` does.
5. **README length alone does better than the scorer here (AUC 0.979 vs 0.914).** In this sample, the
   scorer adds no discrimination beyond "the README is long". Part of the reason is that the neglected
   group is short by construction (median 26 lines, against 209 for the good group). A harder test would compare
   READMEs of similar length.

## What this does and does not show

- **It shows** that on this sample the total score separates curated READMEs from neglected ones well
  (AUC 0.914). Identity, visuals and community separate the groups most; quality does not.
- **It does not show** agreement with human ratings. No people rated these READMEs. The labels come from
  where a repo was found, and some labels are wrong (henryosei/awc and oxakromax are decent READMEs).
- **Selection bias.** awesome-readme favours visually rich READMEs (banners, badges, GIFs). Those are the
  features the rubric rewards, so the good group partly shares the rubric's taste. The neglected group
  is mostly student projects.
- **Small sample.** With n = 25 per group the AUC is approximate. The ranking among good READMEs
  (spread 42–83) was not tested at all.

## Reproduce

```bash
# selection as run on 2026-10-19 (a rerun today gives a different list: search results move)
python bench/scorer-validation/select_repos.py WORK   # -> WORK/readmes/{good,neglected}/OWNER__REPO.md
# to rescore the exact pinned list instead, fetch each README in repos.csv at its SHA into the same layout:
#   gh api "repos/OWNER/REPO/contents/README.md?ref=SHA" -H "Accept: application/vnd.github.raw"
python bench/scorer-validation/build_stub_trees.py WORK/readmes WORK/trees      # empty-file stub trees
python bench/scorer-validation/score_all.py WORK/trees --layout tree --out results.csv
python bench/scorer-validation/score_all.py WORK/readmes --layout flat --out results-readme-only.csv
python bench/scorer-validation/analyze.py                                        # or pass a results csv
```
