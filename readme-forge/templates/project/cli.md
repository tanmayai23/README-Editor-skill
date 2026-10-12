<!-- readme-forge template: CLI tool. Replace {{…}}; delete sections with no real content. -->
<!-- Design pass: swap the title block for templates/design/header-centered.md (generated banner) when the project wants a visual header. -->
<a id="top"></a>
# {{NAME}}

**{{ONE_SENTENCE_PITCH}}**

[![CI status]({{CI_BADGE_URL}})]({{CI_URL}})
[![Latest release]({{RELEASE_BADGE_URL}})]({{RELEASES_URL}})
[![License: {{LICENSE}}]({{LICENSE_BADGE_URL}})](LICENSE)

<!-- Terminal demo: record with vhs (charmbracelet/vhs) or asciinema + agg → docs/demo.gif -->
<img alt="{{NAME}} demo: {{what the recording shows}}" src="docs/demo.gif" width="700">

## Install

| Method | Command |
|---|---|
| {{PACKAGE_MANAGER}} | `{{INSTALL_COMMAND}}` |
| Homebrew | `brew install {{FORMULA}}` |
| Binary | download from [Releases]({{RELEASES_URL}}) |
| From source | `{{SOURCE_INSTALL}}` |

## Quickstart

```bash
{{FIRST_COMMAND}}
```

```text
{{FIRST_COMMAND_OUTPUT}}
```

## Usage

```text
{{HELP_OUTPUT_FROM_REAL_FLAGS}}
```

### Commands

| Command | Description | Example |
|---|---|---|
| `{{cmd}}` | {{…}} | `{{example}}` |

### Recipes

**{{TASK}}**

```bash
{{COMMAND}}
```

## Configuration

{{NAME}} reads `{{CONFIG_PATH}}` (overridden by flags, then env vars).

| Key / Env var | Default | Description |
|---|---|---|
| `{{KEY}}` | `{{DEFAULT}}` | {{…}} |

## Shell completion

```bash
{{COMPLETION_COMMAND}}
```

## How it works

```mermaid
flowchart LR
    {{DIAGRAM}}
```

## Development

```bash
{{DEV_SETUP}}
{{TEST_COMMAND}}
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[{{LICENSE}}](LICENSE)

---

<p align="center"><sub>Released under the <a href="{{LICENSE_FILE}}">{{LICENSE}} License</a> · Built by <a href="{{AUTHOR_URL}}">{{AUTHOR}}</a></sub></p>

<p align="right"><a href="#top">Back to top ↑</a></p>
