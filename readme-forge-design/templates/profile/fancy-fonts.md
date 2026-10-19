<!-- readme-forge profile: fancy fonts. GitHub can't load fonts, so the styled text is Unicode generated with
     `python SKILL_DIR/scripts/fancy_text.py "TEXT" --style sans-bold` (or --all to compare). Never hand-type these characters.
     Screen readers spell styled Unicode letter by letter and GitHub search can't index it: style the headings and one tagline,
     keep the name in the badge alts and all facts in plain text. Replace {{…}}. -->
<!-- Design pass: optional header via templates/design/header-profile.md; close with templates/design/footer-quiet.md. -->
# {{FANCY: Hello, I'm NAME — e.g. --style sans-bold-italic}}

[![GitHub: {{NAME}} (@{{USER}})](https://img.shields.io/badge/@{{USER}}-181717?style=flat-square&logo=github)](https://github.com/{{USER}})
[![Website: {{SITE_DOMAIN}}](https://img.shields.io/badge/{{SITE_DOMAIN}}-{{ACCENT_HEX}}?style=flat-square&logo=googlechrome&logoColor=white)]({{SITE_URL}})
[![X: @{{X_HANDLE}}](https://img.shields.io/badge/@{{X_HANDLE}}-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/{{X_HANDLE}})

{{FANCY: one-line tagline — e.g. --style bold-italic}}

{{NAME}} is a {{ROLE}} who {{ONE_LINE_ABOUT_WHAT_YOU_BUILD}}.

## {{FANCY: Currently working on — --style sans-bold}}

[![{{PROJECT_1}}: {{PROJECT_1_PITCH}}](https://github-readme-stats.vercel.app/api/pin/?username={{USER}}&repo={{PROJECT_1}}&hide_border=true)](https://github.com/{{USER}}/{{PROJECT_1}})
[![{{PROJECT_2}}: {{PROJECT_2_PITCH}}](https://github-readme-stats.vercel.app/api/pin/?username={{USER}}&repo={{PROJECT_2}}&hide_border=true)](https://github.com/{{USER}}/{{PROJECT_2}})

## {{FANCY: My tech stack — --style sans-bold}}

<!-- one badge style per page: flat-square -->
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![{{FRAMEWORK}}](https://img.shields.io/badge/{{FRAMEWORK}}-{{FRAMEWORK_HEX}}?style=flat-square&logo={{FRAMEWORK_SLUG}}&logoColor=white)

## {{FANCY: Find me elsewhere — --style sans-bold}}

- ✍️ Blog: [{{BLOG_DOMAIN}}]({{BLOG_URL}})
- 📫 Email: {{EMAIL}}
