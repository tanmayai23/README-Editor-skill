<!-- readme-forge profile: organization. Path: ORG/.github repo → profile/README.md (public), or ORG/.github-private → profile/README.md (members only). Replace {{…}}. -->
<!-- Design pass: open with templates/design/header-profile.md (generated hero banner in the user's accent colour) and close with templates/design/footer-svg.md (--style wave). -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{{BANNER_DARK_URL}}">
  <img alt="{{ORG_NAME}}: {{TAGLINE}}" src="{{BANNER_LIGHT_URL}}" width="100%">
</picture>

**{{ORG_NAME}}** {{MISSION_ONE_SENTENCE}}

### Projects

| Project | Description | |
|---|---|---|
| [{{PROJECT}}](https://github.com/{{ORG}}/{{PROJECT}}) | {{one line}} | [![Stars of {{PROJECT}}](https://img.shields.io/github/stars/{{ORG}}/{{PROJECT}}?style=flat-square&label=⭐)](https://github.com/{{ORG}}/{{PROJECT}}) |

### Get involved

- 🐛 Start with [good first issues](https://github.com/search?q=org%3A{{ORG}}+label%3A%22good+first+issue%22+state%3Aopen&type=issues)
- 💬 Ask questions in [Discussions]({{DISCUSSIONS_URL}}) or on [{{CHAT}}]({{CHAT_URL}})
- 📖 Read our [contributing guide]({{CONTRIBUTING_URL}}) and [code of conduct]({{COC_URL}})
- 🔐 Report security issues privately: {{SECURITY_CONTACT}}

### Links

[Website]({{SITE_URL}}) · [Docs]({{DOCS_URL}}) · [Blog]({{BLOG_URL}}) · [Careers]({{CAREERS_URL}})
