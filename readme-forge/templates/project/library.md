<!-- readme-forge template: library / SDK. Replace {{…}}; delete sections with no real content. -->
<!-- Design pass: swap the title block for templates/design/header-centered.md (generated banner) when the project wants a visual header. -->
<a id="top"></a>
<div align="center">

# {{NAME}}

**{{ONE_SENTENCE_PITCH}}**

[![CI status]({{CI_BADGE_URL}})]({{CI_URL}})
[![{{REGISTRY}} version]({{VERSION_BADGE_URL}})]({{REGISTRY_URL}})
[![License: {{LICENSE}}]({{LICENSE_BADGE_URL}})](LICENSE)

[Documentation]({{DOCS_URL}}) · [Examples](examples/) · [Changelog](CHANGELOG.md)

</div>

```{{LANG}}
{{SHORTEST_USEFUL_EXAMPLE}}
```

## Features

- **{{FEATURE_NOUN}}**: {{what it does, concretely}}
- **{{FEATURE_NOUN}}**: {{…}}
- **{{FEATURE_NOUN}}**: {{…}}

## Installation

```bash
{{INSTALL_COMMAND}}
```

Requires {{RUNTIME}} {{VERSION_RANGE}}.

## Usage

### {{MOST_COMMON_TASK}}

```{{LANG}}
{{EXAMPLE}}
```

<details>
<summary>Output</summary>

```text
{{OUTPUT}}
```

</details>

### {{SECOND_TASK}}

```{{LANG}}
{{EXAMPLE}}
```

## API overview

| Export | Description |
|---|---|
| `{{fn}}` | {{…}} |

Full reference: [{{DOCS_URL}}]({{DOCS_URL}})

## How it works

{{ONE_SENTENCE_SUMMARY_OF_DIAGRAM}}

```mermaid
flowchart LR
    {{DIAGRAM}}
```

## Compatibility

| {{RUNTIME}} | Supported |
|---|---|
| {{VERSION}} | ✅ |

## Development

```bash
git clone {{REPO_URL}}
cd {{REPO_DIR}}
{{DEV_INSTALL}}
{{TEST_COMMAND}}
```

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first, then open an issue to discuss larger changes.

## License

[{{LICENSE}}](LICENSE) © {{YEAR}} {{AUTHOR}}

---

<p align="center"><sub>Released under the <a href="{{LICENSE_FILE}}">{{LICENSE}} License</a> · Built by <a href="{{AUTHOR_URL}}">{{AUTHOR}}</a></sub></p>

<p align="right"><a href="#top">Back to top ↑</a></p>
