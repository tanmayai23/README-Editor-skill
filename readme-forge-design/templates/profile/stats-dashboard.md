<!-- readme-forge profile: stats dashboard. Replace {{…}}. THEME pairs: dark=tokyonight|github_dark|onedark, light=default. -->
<!-- Design pass: open with templates/design/header-profile.md (generated hero banner in the user's accent colour) and close with templates/design/footer-svg.md (--style wave). -->
<h2 align="center">Hi, I'm {{NAME}}</h2>
<p align="center"><b>{{ROLE}}</b>: {{ONE_LINE_HEADLINE}}</p>

<p align="center">
  <a href="{{LINKEDIN_URL}}"><img alt="LinkedIn: {{NAME}}" src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge"></a>
  <a href="{{SITE_URL}}"><img alt="Website: {{SITE_DOMAIN}}" src="https://img.shields.io/badge/Website-111111?style=for-the-badge&logo=googlechrome&logoColor=white"></a>
  <a href="mailto:{{EMAIL}}"><img alt="Email {{NAME}}" src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white"></a>
</p>

## About me

- 🔭 Currently building **{{CURRENT_PROJECT}}**: {{one line}}
- 🌱 Learning {{TOPIC}}
- 🤝 Open to {{collaboration / roles / mentoring}}
- ⚡ {{FUN_FACT}}

## Tech stack

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://skillicons.dev/icons?i={{SKILL_IDS}}&theme=dark&perline=10">
  <img alt="Skills: {{SKILLS_HUMAN_LIST}}" src="https://skillicons.dev/icons?i={{SKILL_IDS}}&theme=light&perline=10">
</picture>

## GitHub stats

<!-- Shared public instances can be rate-limited. For reliability, self-host github-readme-stats (fork + Vercel + PAT)
     or switch to lowlighter/metrics via workflows/metrics.yml. -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github-readme-stats.vercel.app/api?username={{USER}}&show_icons=true&hide_border=true&theme=tokyonight">
    <img height="165" alt="{{NAME}}'s GitHub stats: stars, commits, pull requests, issues" src="https://github-readme-stats.vercel.app/api?username={{USER}}&show_icons=true&hide_border=true&theme=default">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github-readme-stats.vercel.app/api/top-langs/?username={{USER}}&layout=compact&hide_border=true&theme=tokyonight">
    <img height="165" alt="{{NAME}}'s most used languages on GitHub" src="https://github-readme-stats.vercel.app/api/top-langs/?username={{USER}}&layout=compact&hide_border=true&theme=default">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://streak-stats.demolab.com?user={{USER}}&theme=tokyonight&hide_border=true">
    <img alt="{{NAME}}'s GitHub contribution streak" src="https://streak-stats.demolab.com?user={{USER}}&theme=default&hide_border=true">
  </picture>
</p>

## Featured projects

| Project | What it does | Stack |
|---|---|---|
| [{{PROJECT_1}}](https://github.com/{{USER}}/{{PROJECT_1}}) | {{one line + result}} | {{…}} |
| [{{PROJECT_2}}](https://github.com/{{USER}}/{{PROJECT_2}}) | {{…}} | {{…}} |
| [{{PROJECT_3}}](https://github.com/{{USER}}/{{PROJECT_3}}) | {{…}} | {{…}} |
