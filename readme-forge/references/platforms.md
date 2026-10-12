# Platform rendering rules

Write for where the README will be **read**. When one README must serve several platforms, write it for GitHub first and port it to the others (Mode E). Keep the facts identical across versions.

## Feature support matrix

| Feature | GitHub | GitLab | Hugging Face | PyPI | npm | crates.io / docs.rs | VS Code Marketplace |
|---|---|---|---|---|---|---|---|
| GFM tables, task lists, strikethrough | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mermaid code blocks | ✅ | ✅ | ⚠️ unreliable → image | ❌ | ❌ | ❌ | ❌ |
| Alerts `> [!NOTE]` | ✅ | ❌ (plain quote) | ❌ | ❌ | ❌ | ❌ | ❌ |
| `<picture>` dark/light | ✅ | ⚠️ | ❌ use `#hf-dark-mode-only` | ❌ (sanitized) | ⚠️ | ❌ | ❌ |
| `#gh-dark-mode-only` suffix | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Math `$…$` / `$$…$$` | ✅ | ✅ | ✅ KaTeX | ❌ | ❌ | ❌ | ❌ |
| `<details><summary>` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| `<div align="center">` | ✅ | ✅ | ✅ | ⚠️ align stripped | ✅ | ⚠️ | ✅ |
| Relative links/images | ✅ | ✅ | ✅ (within repo) | ❌ break | ⚠️ needs `repository` field; prefer absolute | ⚠️ | ⚠️ needs `repository` |
| YAML frontmatter | shown as table | hidden/table | **required metadata** | shown as text ❌ | shown as text ❌ | ❌ | ❌ |
| Footnotes `[^1]` | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ |
| SVG images | ✅ (via camo proxy) | ✅ | ✅ | ✅ (absolute) | ✅ | ✅ | ⚠️ only from trusted HTTPS hosts |
| Emoji shortcodes `:rocket:` | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ | ⚠️ |

## GitHub specifics
- Alerts (only these five): `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`. Don't nest them, and use at most one or two per section.
- Profile README: repo `USER/USER`, public, with `README.md` at its root. Org profile: `ORG/.github` → `profile/README.md` (public), or `ORG/.github-private` → `profile/README.md` for members only.
- Where GitHub looks for the README: `.github/README.md` > root `README.md` > `docs/README.md`.
- The automatic TOC button exists, so a manual TOC is optional for READMEs of 6 or fewer sections.
- Images are proxied through camo, so a widget can take minutes to refresh. Dynamic SVG widgets must send the right cache headers.
- `<picture>` must contain an `<img>` fallback with alt text.
- Allowed HTML is a sanitized subset. No `<style>`, `<script>` or `style=` attributes. `align`, `width` and `height` work.
- Social preview: set it in the repo settings with a 1280×640 image (not part of the README).

## Hugging Face
- Model, dataset and Space repos read YAML frontmatter from `README.md`. See `huggingface.md`.
- Dark/light images: add `#hf-dark-mode-only` / `#hf-light-mode-only` to the image URL.
- Relative links resolve inside the repo (`resolve/main/...` for files).
- The Space README frontmatter is the Space's configuration. If it's wrong, the build breaks.
- GitHub → HF port: add frontmatter, replace Mermaid with an image, convert alerts to `> **Note:**`, and keep the "how to use" code near the top.

## PyPI (`long_description`)
- pyproject: `readme = "README.md"`, which sets the content type automatically. For setup.py, use `long_description=open("README.md").read()` and `long_description_content_type="text/markdown"`.
- The renderer is `readme_renderer` (cmark-gfm, then bleach sanitize). Validate with `twine check dist/*`.
- **Relative links and images break.** Rewrite them as absolute URLs:
  - images → `https://raw.githubusercontent.com/OWNER/REPO/main/path.png` (or `https://cdn.jsdelivr.net/gh/OWNER/REPO@TAG/path.png` to pin a version);
  - files → `https://github.com/OWNER/REPO/blob/main/path`.
- No Mermaid, alerts, `<picture>` or math. Frontmatter appears as raw text.
- Keep it shorter: pitch, install, quickstart and a docs link work well.

## npm
- npm renders the README in the published tarball (whatever existed at publish time). Updating GitHub doesn't update npm until the next publish.
- Relative image links get rewritten only if `repository` is set in package.json, and even then branch guessing can fail. **Use absolute URLs.**
- No Mermaid and no alerts. Basic HTML works.

## GitLab
- Mermaid ✅, math ✅, alerts ❌ (GitLab uses `> **Note**`; newer versions support `> [!note]` alerts but they aren't portable).
- Relative links resolve against the default branch.

## VS Code Marketplace / Open VSX
- README is shown on the extension page. Images must be HTTPS. SVGs are allowed only from trusted badge providers, so use PNG for screenshots.
- `vsce package` rewrites relative links if `repository` is set. Use `--baseImagesUrl` otherwise.

## docs.rs / crates.io
- `readme = "README.md"` in Cargo.toml. crates.io renders it with a sanitizer. You can also include it in crate docs with `#![doc = include_str!("../README.md")]`, in which case code blocks become doctests, so mark non-Rust blocks with their language or with `ignore`/`text`.

## Port checklist (GitHub → X)
1. Change relative URLs to absolute (pinned to a tag when possible).
2. Replace Mermaid blocks with a pre-rendered image plus a one-sentence text summary.
3. Change `> [!NOTE]` to `> **Note**` + newline + text.
4. Change `<picture>` to the light-mode `<img>`, or use the platform's dark/light suffix.
5. Remove GitHub-only widgets (stats cards) and the TOC if the result is short.
6. Add or remove frontmatter as needed (HF requires it; PyPI and npm show it as text).
7. Check rendering: `twine check`, `npm pack --dry-run` plus a preview, or the HF "Preview" tab.
