<!-- readme-forge profile: just an image. The whole profile is one picture (a photo, illustration or designed card).
     Bold, but a recruiter learns nothing from a picture alone, so the alt text carries the introduction and one line
     of plain text sits under it. Commit the image to assets/ (≤ 1 MB; 1280 px wide is plenty). Use your own image or one
     you have a licence for. Replace {{…}}.
     score_readme.py --profile will report missing skills/projects/contact sections: expected for this archetype, don't pad it. -->
<!-- Design pass: no banner or footer; the image is the page. A designed card can come from make_banner.py --style spotlight. -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/{{IMAGE_DARK_FILE}}">
  <img alt="{{NAME}}, {{ROLE}}. {{WHAT_THE_IMAGE_SHOWS}}" src="assets/{{IMAGE_FILE}}" width="100%">
</picture>

<p align="center"><sub>{{NAME}} · {{ROLE}} · <a href="{{SITE_URL}}">{{SITE_DOMAIN}}</a></sub></p>
