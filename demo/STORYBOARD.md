# readme-forge: demo reel storyboard

You will make **two videos from the same footage**:

| Version | Length | Sound | Where it goes |
|---|---|---|---|
| **A. README loop** | 14–16 s | none (autoplays muted) | top of your GitHub README |
| **B. Cinematic reel** | 30 s | music + whooshes | X, LinkedIn, YouTube Shorts, Reddit, Product Hunt |

The story is the same in both: **bad README (43 F) → one command → great README (95 A).** Both numbers are real: the scorer produces them on `demo/sample-app`.

---

## Look & feel

| Element | Choice |
|---|---|
| Background (all text/end cards) | deep navy `#0B1020` with a soft radial glow `#1B2550` in the center |
| Accent | amber `#FF8A3D` (command, logo, "star" button) |
| "Bad" color | red `#FF5D5D` (the F score, error lines) |
| "Good" color | green `#3DDC97` (the A score, check marks) |
| Terminal | VHS theme *Catppuccin Mocha*, JetBrains Mono, rounded window with colored dots |
| Caption font | Inter Bold (or Poppins SemiBold), white, 64–72 px on 1080p, bottom third, max 6 words |
| Motion | slow push-ins (100% → 108% over a shot), hard cuts on beats, one whip-pan into the "after" |
| Music (reel only) | 100–120 BPM lo-fi/electronic build. Free: YouTube Audio Library, Pixabay Music (check the license) |

---

## Footage you'll record (all from the `demo/` folder)

| File | How | What it shows |
|---|---|---|
| `before.mp4` | `vhs before.tape` | the bad README, then score **43/100 F** |
| `run.mp4` | `vhs run.tape` (or record your screen) | the real Claude Code run of `/readme-forge` |
| `after.mp4` | `vhs after.tape` | score **95/100 A** |
| `github.mp4` | screen recording (Win + Shift + R in Snipping Tool) | the improved README **rendered on GitHub**: badges, endpoint table, Mermaid diagram |
| `ai-before.mp4`, `ai-after.mp4` | AI video tool, prompts in `PROMPTS.md` | cinematic mood shots (reel only) |

**For `github.mp4`:** create a throwaway public repo, push `demo/sample-app` with `README.after.md` renamed to `README.md`, and open it in Chrome in dark mode at 125% zoom. Record a slow, smooth scroll from the title down to the diagram. Hide the bookmarks bar.

---

## Scene by scene: B. Cinematic reel (30 s, 16:9, 1920×1080)

| # | Time | Visual | Source | Caption on screen | Sound |
|---|---|---|---|---|---|
| 1 | 0:00–0:03 | **Hook.** Night, rain on the window, a tired developer stares at a dull, flat document on the monitor. Slow push-in. | `ai-before.mp4` | *Your README is your first impression.* | low drone, rain |
| 2 | 0:03–0:07 | Bad README prints in the terminal, then the score card: red **43/100 grade F** and a list of ERRORs. Zoom 115% onto the score line in the last second. | `before.mp4` (speed 1.5×) | *Most READMEs fail in 10 seconds.* | beat drops on the "F" |
| 3 | 0:07–0:09 | Close-up of typing `/readme-forge improve my README`. Crop to the input line only, so the text is huge. | `run.mp4` (real time) | (none, the command is the caption) | key clicks |
| 4 | 0:09–0:15 | Claude works: reading files, running the analyzer, writing. **Speed up 8×.** Add a thin amber progress line along the bottom edge. | `run.mp4` (8×) | *Reads your actual code.* → *Draws your architecture.* | rising riser |
| 5 | 0:15–0:21 | **Whip-pan** into GitHub: rendered README with badges → endpoints table → slow push-in on the **Mermaid architecture diagram**. | `github.mp4` | *Diagram built from real imports.* | whoosh on the whip |
| 6 | 0:21–0:24 | **Split screen**: left red *43 F*, right green *95 A*. The right side slides in. Then full screen on the 95. | `before.mp4` + `after.mp4` (last frames) | *43 → 95. One command.* | impact hit |
| 7 | 0:24–0:27 | Same developer, warm morning light, leans back and smiles; the screen shows a clean, colorful document. Slow pull-out. | `ai-after.mp4` | *README like a pro.* | music opens up |
| 8 | 0:27–0:30 | **End card** on the navy background: amber `readme-forge` wordmark, then the install command in a terminal pill, then a "⭐ Star on GitHub" button that pulses once. | made in the editor | `/plugin install readme-forge` · github.com/YOU/readme-forge | soft outro |

## Scene by scene: A. README loop (15 s, 1280×720, no sound)

No AI shots. Developers trust the real product more. Burn the captions in, because there's no sound.

| # | Time | Source | Caption |
|---|---|---|---|
| 1 | 0:00–0:04 | `before.mp4` (1.5×) | *Before: 43/100* |
| 2 | 0:04–0:06 | `run.mp4` (typing, real time) | *One command* |
| 3 | 0:06–0:09 | `run.mp4` (10×) | *Reads your code* |
| 4 | 0:09–0:13 | `github.mp4` | *Diagram + docs from real facts* |
| 5 | 0:13–0:15 | `after.mp4` (last frame held) | *After: 95/100* |

Make the last frame (95 A) **hold for 1.5 s** so the loop restart feels intentional.

---

## Editing steps (CapCut desktop, free; DaVinci Resolve works the same way)

1. New project at 1920×1080, 30 fps (reel) or 1280×720, 30 fps (README loop).
2. Drop clips on the timeline in scene order. Trim to the times above.
3. Speed: select the clip → Speed → Normal → 8× (scene 4).
4. Zoom/push-in: keyframe Scale 100% at start → 108% at end on every shot.
5. Captions: Text → Inter Bold, white, a subtle black shadow (opacity 40%), bottom third. Animate in with "fade up" (6 frames).
6. Split screen (scene 6): two video tracks, each cropped to half width; keyframe the right one sliding in from the right.
7. End card: a solid `#0B1020` background, the wordmark in amber, the command in a rounded rectangle `#141A33` with monospace text.
8. Reel only: add music, cut on the beats (CapCut: Audio → "Beats" auto-markers), and whoosh SFX on cuts 4→5 and 5→6.
9. Export the master: MP4, H.264, 1080p, 30 fps, high bitrate.

## Export for the README (ffmpeg is already on your PC)

```bash
# MP4 for GitHub (small, no audio). GitHub limits upload size, so keep it under 10 MB.
ffmpeg -i loop-master.mp4 -vf "scale=1280:-2" -c:v libx264 -crf 28 -preset slow -an -movflags +faststart demo.mp4

# GIF fallback (works everywhere: PyPI, npm, Hugging Face)
ffmpeg -i loop-master.mp4 -vf "fps=15,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" -loop 0 demo.gif

# Speed a clip up 8x yourself, if your editor can't
ffmpeg -i run.mp4 -filter:v "setpts=PTS/8" -an run-8x.mp4

# Poster frame (for the social preview / thumbnail)
ffmpeg -ss 00:00:14 -i loop-master.mp4 -frames:v 1 poster.png
```

## Put it in the README

**MP4 (best quality):** on github.com, edit README.md and drag `demo.mp4` into the editor. GitHub uploads it and inserts a `https://github.com/user-attachments/assets/…` link. Keep that link on its own line and it renders as a video player.

**GIF (autoplays everywhere):**
```md
<p align="center">
  <img src="demo/demo.gif" width="800"
       alt="readme-forge demo: a README scoring 43/100 is improved by one /readme-forge command into a README with badges, an endpoint table and an architecture diagram, scoring 95/100">
</p>
```

## Recording checklist

- [ ] Install VHS: `winget install charmbracelet.vhs` (or `scoop install vhs`). It needs ffmpeg (you have it) and ttyd (VHS installs it, or `scoop install ttyd`).
- [ ] Install the JetBrains Mono font (free) so VHS can use it.
- [ ] `cd demo` → `vhs before.tape` → `vhs after.tape`. These are deterministic, so re-run them freely.
- [ ] For `run.tape`, pre-approve tool permissions in Claude Code first so the take doesn't stop on a prompt. If it still stalls, record the session with Snipping Tool instead.
- [ ] Windows: turn on Focus Assist (no notifications), hide the taskbar clock, and use a clean browser profile for `github.mp4`.
- [ ] Watch the final loop on a phone: every caption must be readable at phone width.

---

## Already rendered (Oct 2026)

| File | What |
|---|---|
| `readme-forge-demo.mp4` / `.gif` | README loop, 21 s, silent, captions burned in |
| **`readme-forge-cinematic.mp4`** | 33.8 s final film: Gemini "before" shot (hook) → tutorial footage → 43→95 → Gemini "after" shot → end card, with ambience + impact sound. Rebuild: `cd build && python cinematic.py` |
| `readme-forge-reel.mp4` | 28.5 s reel: hook card → before → live run → README → 43→95 card → end card. Add music + the AI shots from `PROMPTS.md` in CapCut |
| `poster.png` | 43 → 95 card, for the social preview / video poster |
| `sample-app/README.live.md` | the README Claude wrote **live** during `run.tape` (scored 95/100) |

Rebuild everything: `vhs before.tape && vhs run.tape && vhs after.tape`, then `cd build && bash assemble.sh`
(set `RUN_TYPE_START`, `RUN_TYPE_END`, `RUN_WORK_END` to the timestamps in your new `run.mp4`).
