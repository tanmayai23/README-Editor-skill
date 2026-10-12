# AI video prompts: "Before" and "After"

Use these for the **cinematic mood shots** (reel scenes 1 and 7). They work in Google Veo 3, OpenAI Sora 2, Kling 2.x, Runway Gen-4 and Higgsfield.

**Rules that make them work**
- **Never ask the AI to show readable text, code, or real logos.** Video models garble text, and fake UI would mislead viewers. Your real product shots come from the VHS and GitHub recordings.
- **Same character, same room, same lens in both prompts.** Only light, mood and the screen change, which makes the cut feel like a transformation.
- Generate 3–4 takes of each and pick the best. Use the same seed for before and after if the tool allows it.
- Settings: **16:9, 1080p, 24 fps, 5–8 s, no audio** (you add music in the editor).

---

## Prompt 1: BEFORE (cold, frustrated)

```text
Cinematic close-medium shot, 35mm lens, shallow depth of field. A young software developer in a dark grey hoodie sits at a wooden desk in a small apartment at night, lit only by the cold blue-white glow of a single monitor. Rain streaks down a window behind them, city lights blurred into bokeh. On the monitor: a plain, flat, grey document with long unbroken blocks of blurred text, no images, no color, out of focus so no letters are legible. The developer rubs their forehead and exhales, shoulders slumped, then scrolls slowly with a tired expression. Slow dolly push-in toward the developer over the whole shot. Moody, desaturated teal-and-steel color grade, soft film grain, high contrast shadows, subtle haze in the air. Photorealistic, natural motion, no camera shake.
```

**Negative prompt** (tools that support it):
```text
readable text, letters, words, code, logos, brand names, watermark, subtitles, UI screenshots, extra fingers, distorted hands, face morphing, flicker, cartoon, oversaturated
```

## Prompt 2: AFTER (warm, confident)

```text
Cinematic close-medium shot, 35mm lens, shallow depth of field, same small apartment and same wooden desk as before, now in early morning golden-hour sunlight streaming through the window, rain gone, warm light rays and floating dust particles. The same young developer in a dark grey hoodie leans back in the chair with a relaxed, satisfied smile, arms loosely crossed. On the monitor, out of focus: a clean, well-organized colorful document with neat sections, small colored pill-shaped labels in green, amber and blue, a simple flowchart of rounded boxes connected by lines, and a large green check mark glowing softly. No legible letters. Slow dolly pull-out away from the developer, revealing a coffee mug and a small plant on the desk. Warm amber-and-cream color grade, gentle film grain, soft highlights, optimistic mood. Photorealistic, natural motion, no camera shake.
```

**Negative prompt:** same as above.

---

## Optional: one-shot transformation (if your tool supports start + end frames)

Kling, Runway and Higgsfield can animate *between two images*. Generate a still from each prompt (Midjourney, Flux, Imagen or the video tool's image mode), then use:
```text
Seamless time-lapse transition from night to morning in the same room: rain fades, sunlight sweeps across the desk from left to right, the monitor's grey document dissolves into a clean colorful layout, the developer's posture shifts from slumped to relaxed and smiling. Smooth, continuous camera, no cuts.
```
Start frame = the BEFORE still, end frame = the AFTER still, 5 s. This one clip can replace scenes 1 and 7.

## Optional: thumbnail / social preview still (1280×640)

```text
Minimal tech poster, deep navy background with a soft radial glow in the center. Left half: a dull grey document card, slightly tilted, with a small red "F" badge. Right half: a bright, clean document card with colorful pill labels, a tiny flowchart and a green "A" badge, glowing amber rim light. A thin amber arrow sweeps from left to right between them. Flat vector style with subtle depth, lots of empty space at the top for a title. No other text.
```
Then add the title **readme-forge** and the subtitle *"Your README, from 43 to 95 in one command"* yourself in Canva or CapCut, because AI images can't spell reliably. Upload it under GitHub repo **Settings → Social preview**.
