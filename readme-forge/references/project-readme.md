# Project README blueprints

A README has three readers, in this order. Serve them in this order:
1. **Evaluator** (10 seconds): what is this, is it for me, is it alive? → title, pitch, badges, demo, features.
2. **User** (5 minutes): how do I install and get a result? → quickstart, install, usage, config.
3. **Contributor** (later): how is it built, how do I change it? → architecture, structure, development, contributing.

## Universal skeleton

```md
<div align="center">                              ← optional; centered hero for apps/brands
  <picture>…logo dark/light…</picture>
  <h1>Name</h1>
  <p><b>One sentence: what it does, for whom, how it's different.</b></p>
  badges (3–6)
  <p><a href="demo">Live demo</a> · <a href="docs">Docs</a> · <a href="issues">Report bug</a></p>
</div>

Demo GIF / screenshot (alt text!)  — or a 5-line code example for libraries

## Features            3–7 bullets, each a concrete capability ("Exports to PNG, SVG and PDF") not adjectives
## Quickstart          ≤ 5 commands from zero to a visible result
## Installation        every supported method (package manager, binary, Docker, source); prerequisites first
## Usage               real examples with real output; most common task first
## Configuration       table: Variable | Required | Default | Description  (from env_vars facts)
## Architecture        Mermaid diagram + 3–6 sentences on how the pieces talk
## Project structure   trimmed tree (≤ 25 lines) with one-line comments on key dirs
## Development         clone → install → run → test → lint; from real scripts/make targets
## Deployment          only if the repo has deploy config (deploy_hints, docker)
## Roadmap / FAQ       only if real content exists (link issues/milestones)
## Contributing        3 lines + link to CONTRIBUTING.md
## License             "Distributed under the MIT License. See LICENSE." (from license facts)
## Acknowledgments     libraries/papers/people actually credited
```
Add `## Table of contents` after the hero when > 6 H2 sections (or a `<details>` TOC). GitHub also has an automatic outline button, so keep the TOC short.

## Blueprints by type (deltas from the skeleton)

### Library / SDK (`templates/project/library.md`)
- Show a **5–15 line code sample right under the pitch**. This beats a screenshot.
- Install one-liner for each registry (`npm i x`, `pip install x`, `cargo add x`, `go get x`).
- Usage: the 2–4 most common tasks, each a heading with a snippet and its output.
- API: a brief table of main exports, then link to full docs (docs site, docs.rs, pkg.go.dev, typedoc).
- Compatibility: runtime versions, browser/ESM/CJS support, platform notes.
- Comparison with alternatives only if fair and factual.

### CLI tool (`templates/project/cli.md`)
- A terminal recording (asciinema/vhs GIF) or a code block showing a command and its output.
- Install via package managers, `go install`, `cargo install`, brew, prebuilt binaries, Docker.
- Usage: `tool --help` output (real output from the code's flag definitions), then common recipes.
- Commands table: Command | Description | Example.
- Config file location and format, plus env vars. Shell completion if supported.

### Web app / full-stack (`templates/project/webapp.md`)
- Screenshot or GIF and a live-demo link at the top.
- Tech stack line or table (Frontend / Backend / DB / Infra) from `frameworks` and `packages_detail`.
- Quickstart with Docker Compose if there is a compose file (`docker compose up` → open `http://localhost:PORT`).
- Manual setup per package (backend, frontend), with `.env` setup copied from `.env.example`.
- Architecture: a client → API → DB flowchart, plus a sequence diagram for auth or the main flow.
- Deployment section from `vercel.json`, `fly.toml`, `render.yaml` or k8s.

### API / backend service (`templates/project/api.md`)
- Endpoint summary table from `http_routes` (Method | Path | Description). Link OpenAPI/Swagger at `/docs` if FastAPI, or a swagger file.
- An example request and response with curl.
- Auth explanation, rate limits, error format.
- Run locally, run tests, migrations (alembic, prisma migrate, etc. from the scripts).

### ML / data science (`templates/project/ml-project.md`)
- Results table first (real numbers with dataset and metric), with a link to the HF model or dataset.
- Reproducibility: environment (Python, CUDA), data download, train command, eval command, expected runtime and hardware.
- Pretrained weights table: Model | Params | Metric | Download.
- Inference snippet.
- Pipeline diagram: data → preprocess → train → evaluate → serve.
- Citation (BibTeX) and a `CITATION.cff`.
- Pair with an HF model card (Mode C) when weights are published.

### Monorepo (`templates/project/monorepo.md`)
- A packages table: Package | Path | Description | Version badge (from `monorepo_packages` / `packages_detail`).
- Workspace commands (`pnpm -r build`, `turbo run test`, `nx affected`), plus how to run one package.
- Dependency diagram between packages, built with `import_graph.py --depth 1`.
- Each package keeps its own short README. The root one routes readers to them.

### Research / paper code
- Paper title, authors, venue, and arXiv/DOI badges. Optionally a teaser figure.
- "Reproduce Table N" commands, data, checkpoints. BibTeX citation near the top or bottom.

### Template / starter / boilerplate
- "Use this template" button link: `https://github.com/OWNER/REPO/generate`.
- What's included (stack checklist), rename steps, and what to delete.

### Infra / DevOps
- What it provisions (diagram), prerequisites (cloud CLI, credentials), inputs/outputs tables (Terraform variables), cost warning, teardown command.

### Mobile / game
- Store badges and links, screenshots grid (a table of 3 images), supported OS versions, build instructions for each platform. For games, also the controls.

## Section-writing rules
- **Pitch formula:** `<Name> is a <category> that <does X> for <audience>[, unlike/without <pain>].` Under 25 words.
- **Features:** start each with a verb or noun phrase. Put **specific nouns** in bold. No "fast, simple, powerful".
- **Quickstart:** must actually work in a fresh clone. Prerequisites go in a callout first. Show expected output or URL.
- **Commands:** one command per line in `bash` blocks. Don't prefix with `$` (it breaks copy-paste) unless output is interleaved, in which case use `console`. Use `powershell` blocks for Windows-specific steps.
- **Config table:** list every variable in `.env.example`. Mark secrets. Never paste real secret values.
- **Project structure:** trim generated or vendor dirs. Comment only non-obvious dirs.
- **Links:** use relative links for files in the repo on GitHub, and absolute links when porting (see platforms.md).
- **Length:** a good target is 150–400 lines. Move deep docs into `docs/` and link to them.
