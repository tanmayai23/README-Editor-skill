<!-- readme-forge profile: game mode. A community tic-tac-toe game anyone can play from your profile.
     Needs workflows/tictactoe.yml + game/tictactoe.py (setup steps at the top of the workflow). Replace {{…}}. -->
<!-- Design pass: open with templates/design/header-profile.md and close with templates/design/footer-svg.md (--style wave). -->
### Hey, I'm {{NAME}} 👋

{{ROLE}} {{at COMPANY / based in CITY}}. {{ONE_LINE_ABOUT_WHAT_YOU_BUILD}}

[![Website: {{SITE_DOMAIN}}](https://img.shields.io/badge/Website-{{ACCENT_HEX}}?style=flat-square&logo=googlechrome&logoColor=white)]({{SITE_URL}})
[![LinkedIn: {{NAME}}](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square)]({{LINKEDIN_URL}})

## 🎮 Play tic-tac-toe with everyone

Anyone can play the next move. Click a numbered square: it opens an issue, a bot plays your move within a minute, and the board below updates for the next visitor. You play for whichever team's turn it is.

<!-- TICTACTOE:START -->
_The board appears after the first workflow run (Actions → Tic-tac-toe → Run workflow)._
<!-- TICTACTOE:END -->

<sub>How it works: [the workflow](https://github.com/{{USER}}/{{USER}}/blob/main/.github/workflows/tictactoe.yml) and [the game script](https://github.com/{{USER}}/{{USER}}/blob/main/.github/scripts/tictactoe.py), about 150 lines of Python with no dependencies.</sub>

## 🔭 What I'm up to

- Working on **{{CURRENT_PROJECT}}**: {{one line}}
- Learning {{TOPIC}}
- Ask me about {{TOPICS}}

## 🛠️ Featured work

| Project | What it does |
| --- | --- |
| [{{PROJECT_1}}](https://github.com/{{USER}}/{{PROJECT_1}}) | {{one line with a result}} |
| [{{PROJECT_2}}](https://github.com/{{USER}}/{{PROJECT_2}}) | {{one line with a result}} |
