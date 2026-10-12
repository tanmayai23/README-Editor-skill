<!-- readme-forge profile: creative / animated. ≤ 2 animations. Needs workflows/snake.yml for the snake. Replace {{…}}. -->
<!-- Design pass: open with templates/design/header-profile.md (generated hero banner in the user's accent colour) and close with templates/design/footer-svg.md (--style wave). -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{{BANNER_DARK_URL}}">
  <img alt="{{NAME}}: {{ROLE}}. {{BANNER_TEXT}}" src="{{BANNER_LIGHT_URL}}" width="100%">
</picture>

<h1 align="center">Hey there, I'm {{NAME}} ✨</h1>

<p align="center">
  <a href="https://github.com/DenverCoder1/readme-typing-svg">
    <img alt="Typing: {{LINE_1}}; {{LINE_2}}; {{LINE_3}}" src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=500&size=22&pause=1000&color={{ACCENT_HEX}}&center=true&vCenter=true&width=600&lines={{LINE_1_URLENC}};{{LINE_2_URLENC}};{{LINE_3_URLENC}}">
  </a>
</p>

<table>
<tr>
<td width="55%" valign="top">

### About me

- 🎨 {{WHAT_YOU_CREATE}}
- 🔭 Working on **{{CURRENT_PROJECT}}**
- 🌱 Learning {{TOPIC}}
- 💬 Ask me about {{TOPICS}}
- ⚡ {{FUN_FACT}}

</td>
<td width="45%" valign="top">

### Find me

[![Website: {{SITE_DOMAIN}}](https://img.shields.io/badge/Website-{{ACCENT_HEX}}?style=flat-square&logo=googlechrome&logoColor=white)]({{SITE_URL}})
[![X: @{{X_HANDLE}}](https://img.shields.io/badge/@{{X_HANDLE}}-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/{{X_HANDLE}})
[![Dribbble or Behance: {{NAME}}](https://img.shields.io/badge/Portfolio-ea4c89?style=flat-square&logo=dribbble&logoColor=white)]({{PORTFOLIO_URL}})

</td>
</tr>
</table>

### Things I build with

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://skillicons.dev/icons?i={{SKILL_IDS}}&theme=dark">
  <img alt="Tools: {{SKILLS_HUMAN_LIST}}" src="https://skillicons.dev/icons?i={{SKILL_IDS}}&theme=light">
</picture>

### Recent work

| | |
|---|---|
| <img alt="{{PROJECT_1}} screenshot: {{what it shows}}" src="{{PROJECT_1_IMG}}" width="320"> | **[{{PROJECT_1}}]({{PROJECT_1_URL}})**<br>{{one line}} |
| <img alt="{{PROJECT_2}} screenshot: {{what it shows}}" src="{{PROJECT_2_IMG}}" width="320"> | **[{{PROJECT_2}}]({{PROJECT_2_URL}})**<br>{{one line}} |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/{{USER}}/{{USER}}/output/github-snake-dark.svg">
  <img alt="Animated snake eating {{NAME}}'s GitHub contribution graph" src="https://raw.githubusercontent.com/{{USER}}/{{USER}}/output/github-snake.svg">
</picture>
