# Writing style for READMEs

## Principles
1. **Show, don't claim.** Replace adjectives with evidence: a number, a code sample, a screenshot, a comparison.
   - ❌ "A blazing fast, easy-to-use JSON parser."
   - ✅ "Parses 1 GB of JSON in 0.9 s on an M2 (3× simdjson-go). One function: `parse(bytes)`."
2. **Lead with the reader's goal.** The first screen covers what it is, why it matters, and how to start.
3. **One idea per sentence; one task per section.** Short paragraphs of 1–3 sentences. Lists for parallel items. Tables for reference data.
4. **Second person, present tense, active voice.** "Run `make dev` to start the server." Not "The server can be started by running…"
5. **Concrete names.** "PostgreSQL 15", not "a database". `pnpm`, not "your package manager".
6. **Explain why only where it isn't obvious.** One sentence of rationale beats a paragraph.
7. **Consistent terms.** Pick one word for a concept ("workspace", not workspace/project/space) and keep it.
8. **Honest status.** If it's alpha, unmaintained, or has known gaps, say so in a callout near the top.

## Banned or suspect phrases (and what to do instead)
| Phrase | Do instead |
|---|---|
| blazing/lightning fast, high-performance | give a benchmark number and its setup |
| simple, easy, simply, just, straightforward | show the 3-line example and let readers judge |
| powerful, robust, flexible, seamless, cutting-edge, next-gen, revolutionary, world-class | name the capability: "retries with exponential backoff", "plugins via entry points" |
| leverage, utilize, empower, unleash, supercharge, elevate | use, let, enable, or a specific verb |
| comprehensive solution, all-in-one, one-stop | list what's included |
| "This project is a project that…" | start with the noun: "Rocket is a…" |
| "In today's fast-paced world…", "Look no further" | delete |
| "Feel free to…" | "Open an issue / PR" |
| "Obviously", "of course", "as everyone knows" | delete (it isn't obvious to the reader) |

The scorer flags the most common ones. You should also catch AI-sounding padding: rhetorical questions, "Whether you're X or Y…", triple adjectives, and closing summaries that repeat the intro.

## Emoji
- Optional, never essential. At most one per heading, and the heading must still have words (screen readers read emoji names aloud).
- Professional/library READMEs use none or very few. Profile and creative READMEs can use more.
- Don't use emoji as bullet markers in long lists.

## Callouts (GitHub)
Use `> [!NOTE]` for side info, `> [!TIP]` for shortcuts, `> [!IMPORTANT]` for required steps, `> [!WARNING]` for breaking or dangerous behavior, and `> [!CAUTION]` for data-loss risk. Use at most 1–2 per section. Port to `> **Note**` elsewhere.

## Code blocks
- Always add a language tag. Use `bash` for commands, `console` when showing a prompt with output, `powershell` for Windows, and `text` for plain output.
- Commands must be copy-paste safe: no `$` prompt in `bash` blocks, and no line continuations that break on Windows unless the block is labeled bash.
- Placeholders in angle brackets with a note: `export API_KEY=<your-key>`, followed by "Get a key at …".
- Show the expected output for the first command the user runs.

## Tone by audience
| Audience | Tone |
|---|---|
| Developers (libs, CLIs) | terse, technical, code-first |
| End users (apps) | friendly, outcome-first, screenshots, fewer internals |
| Researchers | precise, cite papers, reproducibility first |
| Recruiters/peers (profile) | personal, specific about impact and interests, brief |
| Enterprise/OSS foundations | formal, governance, security and support policy visible |

## Localization
If the user writes in another language or asks for one, write the README in that language. For multi-language READMEs, use `README.md` (English) + `README.<lang>.md`, with a language switcher line at the top: `English | [简体中文](README.zh-CN.md) | [हिन्दी](README.hi.md)`.
