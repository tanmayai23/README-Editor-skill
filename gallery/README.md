# readme-forge gallery

The data behind the readme-forge gallery website: every banner style, full README design, profile style and before/after example, plus READMEs that people made with the skill.

The website reads [`gallery.json`](gallery.json), so a merged pull request shows up on the site without a redeploy.

## Add your README

Made a README or profile with readme-forge? Add it.

1. Take a screenshot of your README on GitHub, about 1280 px wide (PNG or WebP, under 1 MB). If you have both themes, take one in dark mode and one in light mode.
2. Save it as `gallery/screenshots/<your-github-username>-dark.png` (and `-light.png`). With one screenshot, use the same file for both.
3. Add an entry to the end of `items` in `gallery.json`:

   ```json
   {
     "id": "community-<your-github-username>",
     "category": "community",
     "title": "Your name or project name",
     "description": "One sentence about what the README shows.",
     "image": {
       "dark": "gallery/screenshots/<your-github-username>-dark.png",
       "light": "gallery/screenshots/<your-github-username>-light.png"
     },
     "animated": false,
     "style": "minimal",
     "link": "https://github.com/<you>/<repo>",
     "author": { "name": "Your name", "github": "<your-github-username>" },
     "source": "community"
   }
   ```

   `style` is the profile style you used (the part after `profile-` in a `profiles` entry, such as `minimal` or `stats-dashboard`), or `project` for a project README. Set `animated` to `true` if the README moves.

4. Open a pull request. CI checks the entry, and the gallery shows it once it's merged.

Not sure how to do the JSON? Post your README in [Show and tell](https://github.com/tanmayai23/README-Editor-skill/discussions/categories/show-and-tell) and a maintainer will add it.

### Rules

- Only your own README, and only one entry per person or project.
- The README must be public and must have been made or improved with readme-forge.
- No personal data you don't want shared, and nothing offensive.

## Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique. Community entries start with `community-`. |
| `category` | yes | One of the `id`s in `categories`. |
| `title`, `description` | yes | Shown on the card. |
| `image` | yes for community | `dark` and `light` paths inside this repo, or `null` for text-only cards. |
| `animated` | yes | Shows a "GIF" badge on the card. |
| `link` | yes | Path inside this repo, or an `https://` URL for community entries. |
| `command` | official entries | The command that makes it, shown with a Copy button. |
| `style`, `author` | community entries | Profile style used, and who made it. |
| `source` | yes | `official` or `community`. |

Image paths are served through jsDelivr from `assetBase`.
