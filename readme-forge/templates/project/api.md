<!-- readme-forge template: API / backend service. Replace {{…}}; delete sections with no real content. -->
<!-- Optional design pass (readme-forge-design plugin): swap the title block for its templates/design/header-centered.md when the project wants a generated banner. -->
<a id="top"></a>
# {{NAME}}

**{{ONE_SENTENCE_PITCH}}**

[![CI status]({{CI_BADGE_URL}})]({{CI_URL}})
[![License: {{LICENSE}}]({{LICENSE_BADGE_URL}})](LICENSE)

## Quickstart

```bash
git clone {{REPO_URL}}
cd {{REPO_DIR}}
cp .env.example .env
{{RUN_COMMAND}}
```

The API listens on `http://localhost:{{PORT}}`. Interactive docs: `http://localhost:{{PORT}}{{DOCS_PATH}}`.

```bash
curl -s http://localhost:{{PORT}}{{EXAMPLE_PATH}}
```

```json
{{EXAMPLE_RESPONSE}}
```

## Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `{{PATH}}` | {{…}} | {{…}} |

Full spec: [`{{OPENAPI_FILE_OR_URL}}`]({{OPENAPI_FILE_OR_URL}})

## Authentication

{{HOW_TO_GET_AND_SEND_CREDENTIALS}}

## Errors

```json
{{ERROR_SHAPE}}
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `{{VAR}}` | ✅ | — | {{…}} |

## Architecture

```mermaid
sequenceDiagram
    autonumber
    {{SEQUENCE_OF_MAIN_REQUEST}}
```

## Development

```bash
{{INSTALL}}
{{MIGRATIONS}}
{{RUN_DEV}}
{{TEST}}
```

## Deployment

{{DEPLOY_STEPS}}

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[{{LICENSE}}](LICENSE)

---

<p align="center"><sub>Released under the <a href="{{LICENSE_FILE}}">{{LICENSE}} License</a> · Built by <a href="{{AUTHOR_URL}}">{{AUTHOR}}</a></sub></p>

<p align="right"><a href="#top">Back to top ↑</a></p>
