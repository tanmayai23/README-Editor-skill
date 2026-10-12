<!-- readme-forge template: web app / full-stack. Replace {{…}}; delete sections with no real content. -->
<!-- Design pass: swap the title block for templates/design/header-centered.md (generated banner) when the project wants a visual header. -->
<a id="top"></a>
<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="{{LOGO_DARK}}">
    <img alt="{{NAME}} logo" src="{{LOGO_LIGHT}}" height="80">
  </picture>

  <h1>{{NAME}}</h1>
  <p><strong>{{ONE_SENTENCE_PITCH}}</strong></p>

  [![CI status]({{CI_BADGE_URL}})]({{CI_URL}})
  [![License: {{LICENSE}}]({{LICENSE_BADGE_URL}})](LICENSE)

  <a href="{{DEMO_URL}}">Live demo</a> · <a href="{{DOCS_URL}}">Docs</a> · <a href="{{ISSUES_URL}}">Report a bug</a>
</div>

<br>

<img alt="{{NAME}} screenshot: {{what the screen shows}}" src="{{SCREENSHOT}}" width="100%">

<details>
<summary><strong>Table of contents</strong></summary>

- [Features](#features)
- [Tech stack](#tech-stack)
- [Quickstart](#quickstart)
- [Manual setup](#manual-setup)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

</details>

## Features

- **{{FEATURE}}**: {{…}}
- **{{FEATURE}}**: {{…}}
- **{{FEATURE}}**: {{…}}

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | {{…}} |
| Backend | {{…}} |
| Database | {{…}} |
| Infra | {{…}} |

## Quickstart

> [!IMPORTANT]
> Requires {{PREREQUISITES}}.

```bash
git clone {{REPO_URL}}
cd {{REPO_DIR}}
cp .env.example .env
docker compose up --build
```

Open <http://localhost:{{PORT}}>.

## Manual setup

<details>
<summary>Backend</summary>

```bash
cd {{BACKEND_DIR}}
{{BACKEND_INSTALL}}
{{BACKEND_RUN}}
```

</details>

<details>
<summary>Frontend</summary>

```bash
cd {{FRONTEND_DIR}}
{{FRONTEND_INSTALL}}
{{FRONTEND_RUN}}
```

</details>

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `{{VAR}}` | ✅ | — | {{…}} |

## Architecture

{{ONE_SENTENCE_SUMMARY}}

```mermaid
flowchart LR
    accTitle: {{NAME}} architecture
    accDescr: {{ONE_SENTENCE_SUMMARY}}
    {{DIAGRAM}}
```

## Project structure

```text
{{TRIMMED_TREE}}
```

## Testing

```bash
{{TEST_COMMANDS}}
```

## Deployment

{{DEPLOY_STEPS_FROM_REAL_CONFIG}}

## Contributing

Pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev workflow and conventions.

## License

Distributed under the {{LICENSE}} License. See [LICENSE](LICENSE).

---

<p align="center"><sub>Released under the <a href="{{LICENSE_FILE}}">{{LICENSE}} License</a> · Built by <a href="{{AUTHOR_URL}}">{{AUTHOR}}</a></sub></p>

<p align="right"><a href="#top">Back to top ↑</a></p>
