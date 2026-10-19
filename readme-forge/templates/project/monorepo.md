<!-- readme-forge template: monorepo. Replace {{…}}; delete sections with no real content. -->
<!-- Optional design pass (readme-forge-design plugin): swap the title block for its templates/design/header-centered.md when the project wants a generated banner. -->
<a id="top"></a>
# {{NAME}}

**{{ONE_SENTENCE_PITCH}}**

[![CI status]({{CI_BADGE_URL}})]({{CI_URL}})
[![License: {{LICENSE}}]({{LICENSE_BADGE_URL}})](LICENSE)

## Packages

| Package | Path | Description | Version |
|---|---|---|---|
| `{{pkg}}` | [`{{path}}`]({{path}}) | {{…}} | [![{{pkg}} version]({{BADGE}})]({{REGISTRY_URL}}) |

## How the packages fit together

```mermaid
flowchart LR
    {{PACKAGE_DEPENDENCY_DIAGRAM}}
```

## Quickstart

```bash
git clone {{REPO_URL}}
cd {{REPO_DIR}}
{{WORKSPACE_INSTALL}}
{{WORKSPACE_DEV}}
```

## Common tasks

| Task | Command |
|---|---|
| Build everything | `{{BUILD_ALL}}` |
| Test everything | `{{TEST_ALL}}` |
| Run one package | `{{FILTER_COMMAND}}` |
| Lint | `{{LINT}}` |

## Repository layout

```text
{{TRIMMED_TREE}}
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Each package has its own README with package-specific details.

## License

[{{LICENSE}}](LICENSE)

---

<p align="center"><sub>Released under the <a href="{{LICENSE_FILE}}">{{LICENSE}} License</a> · Built by <a href="{{AUTHOR_URL}}">{{AUTHOR}}</a></sub></p>

<p align="right"><a href="#top">Back to top ↑</a></p>
