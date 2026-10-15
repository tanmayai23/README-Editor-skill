<!-- readme-forge profile: simple but innovative. A few lines of text plus ONE clever live element that says something
     about the person: now playing (Spotify), latest posts (workflows/blog-posts.yml), a game (game-mode.md), or a card the
     user's own site serves. One gimmick only; the rest stays plain. Replace {{…}}; keep the block that fits, delete the others. -->
<!-- Design pass: no banner. Close with templates/design/footer-quiet.md. -->
# Hey, I'm {{NAME}}! 👋

> **{{MOTTO_OR_MISSION_IN_ONE_LINE}}**

{{ROLE}} {{at COMPANY}}. Previously {{ONE_NOTABLE_THING_YOU_BUILT_WITH_LINK}}. {{ONE_SENTENCE_ON_WHAT_DRIVES_YOUR_WORK}}

[`[ 🩷 Sponsor me ]`](https://github.com/sponsors/{{USER}}) [`[ ✍️ Blog ]`]({{BLOG_URL}}) [`[ 📫 Say hi ]`](mailto:{{EMAIL}})

---

<!-- OPTION A: now playing. Tier B, needs the user to connect Spotify once at https://github.com/kittinan/spotify-github-profile -->
| 🎵 Now playing |
| --- |
| <a href="https://open.spotify.com/user/{{SPOTIFY_USER}}"><img alt="Song {{NAME}} is listening to on Spotify right now" src="https://spotify-github-profile.kittinanx.com/api/view?uid={{SPOTIFY_UID}}&cover_image=true&theme=default&bar_color={{ACCENT_HEX_NO_HASH}}" width="480"></a> |

<!-- OPTION B: latest writing, updated by workflows/blog-posts.yml -->
**✍️ Latest posts**
<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->
