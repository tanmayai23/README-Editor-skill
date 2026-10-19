<!-- readme-forge profile: code mode. Pick the language the user actually writes most. Replace {{…}}. -->
<!-- Design pass: open with templates/design/header-profile.md (generated hero banner in the user's accent colour) and close with templates/design/footer-svg.md (--style wave). -->
### `> whoami`

```{{LANG}}
{{CODE_BLOCK}}
```

<!-- Examples for CODE_BLOCK:
TypeScript:
const {{camelName}} = {
  role: "{{ROLE}}",
  location: "{{CITY}}",
  stack: ["{{SKILL_1}}", "{{SKILL_2}}", "{{SKILL_3}}"],
  currentlyBuilding: "{{CURRENT_PROJECT}}",
  learning: ["{{TOPIC}}"],
  askMeAbout: ["{{TOPIC}}", "{{TOPIC}}"],
  reachMe: "{{EMAIL_OR_SITE}}",
};

Python:
from dataclasses import dataclass, field

@dataclass
class {{PascalName}}:
    role: str = "{{ROLE}}"
    stack: list[str] = field(default_factory=lambda: ["{{SKILL_1}}", "{{SKILL_2}}"])
    building: str = "{{CURRENT_PROJECT}}"
    learning: str = "{{TOPIC}}"
    contact: str = "{{EMAIL_OR_SITE}}"

Go / Rust: a struct literal in the same spirit. -->

### `> ls ~/projects --featured`

| Repo | Description |
|---|---|
| [`{{PROJECT_1}}`](https://github.com/{{USER}}/{{PROJECT_1}}) | {{one line}} |
| [`{{PROJECT_2}}`](https://github.com/{{USER}}/{{PROJECT_2}}) | {{one line}} |

### `> cat stack.txt`

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://skillicons.dev/icons?i={{SKILL_IDS}}&theme=dark">
  <img alt="Stack: {{SKILLS_HUMAN_LIST}}" src="https://skillicons.dev/icons?i={{SKILL_IDS}}&theme=light">
</picture>

### `> contact --list`

[Website]({{SITE_URL}}) · [LinkedIn]({{LINKEDIN_URL}}) · [Email](mailto:{{EMAIL}})
