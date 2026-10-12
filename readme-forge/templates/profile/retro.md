<!-- readme-forge profile: retro / terminal. Generate ASCII art for the name (e.g. figlet "standard" font) — keep ≤ 60 cols so it fits phones. Replace {{…}}. -->
<!-- Design pass: open with templates/design/header-profile.md (generated hero banner in the user's accent colour) and close with templates/design/footer-svg.md (--style wave). -->
```text
{{ASCII_ART_NAME}}
```

```text
┌──────────────────────────────────────────────┐
│ USER      {{USER}}                            │
│ ROLE      {{ROLE}}                            │
│ LOCATION  {{CITY}}                            │
│ STATUS    building {{CURRENT_PROJECT}}        │
│ LEARNING  {{TOPIC}}                           │
└──────────────────────────────────────────────┘
```

**C:\\> dir /projects**

- [`{{PROJECT_1}}`](https://github.com/{{USER}}/{{PROJECT_1}}): {{one line}}
- [`{{PROJECT_2}}`](https://github.com/{{USER}}/{{PROJECT_2}}): {{one line}}

**C:\\> type stack.txt**

`{{SKILL_1}}` `{{SKILL_2}}` `{{SKILL_3}}` `{{SKILL_4}}` `{{SKILL_5}}`

**C:\\> ping {{NAME}}**

[{{SITE_DOMAIN}}]({{SITE_URL}}) · [mail](mailto:{{EMAIL}})

<!-- Note for screen readers: ASCII art is read character by character. Keep it short, and put the real name as plain text right after it. -->
**{{NAME}}**, {{ROLE}}
