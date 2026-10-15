<!-- readme-forge design: centered stack header (default for projects). Generate assets:
     python SKILL_DIR/scripts/make_banner.py --style {{STYLE}} --title "{{NAME}}" --subtitle "{{PITCH}}" --tag "{{CATEGORY}}" --out .github/assets -->
<a id="top"></a>

<a href="{{REPO_URL}}">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/header-dark.svg">
    <img alt="{{NAME}}: {{PITCH}}" src=".github/assets/header-light.svg" width="100%">
  </picture>
</a>

<p align="center"><b>{{PITCH}}</b></p>

<p align="center">
  {{BADGES_ONE_STYLE}}
</p>

<p align="center">
  <a href="{{DOCS_URL}}">Documentation</a> •
  <a href="{{DEMO_URL}}">Live demo</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="{{COMMUNITY_URL}}">Community</a>
</p>

<br>
