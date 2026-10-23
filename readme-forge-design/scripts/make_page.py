#!/usr/bin/env python3
"""Build a whole designed README from one JSON spec: every block is an SVG card.

The "page kit" behind keynote-style profile and project READMEs: a terminal-window hero with a
dripping edge, a dock of contact tiles, numbered section headers, an about card, a tech-stack grid
with real brand icons, project cards (feature / card / link), achievement cards, themed stats
widgets and a mirrored footer. Every card ships light and dark, uses system font stacks, animates
decoration with CSS only (prefers-reduced-motion stops it) and has a complete first frame.

Stdlib only. Brand icons come from assets/icons.json (Simple Icons, CC0).

Usage:
  python make_page.py --init profile > page.json        # starter spec (profile | project)
  python make_page.py --spec page.json                  # writes the SVGs and README.md
  python make_page.py --spec page.json --readme README.md --preview preview.html
  python make_page.py --list                            # themes, visuals, block types, icons
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import math
import os
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ICONS = json.loads((HERE.parent / "assets" / "icons.json").read_text(encoding="utf-8"))["icons"]
TEMPLATES = HERE.parent / "templates" / "page"

SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Inter, Roboto, 'Helvetica Neue', Arial, sans-serif"
SERIF = "'Instrument Serif', 'New York', 'Iowan Old Style', Georgia, 'Times New Roman', serif"
MONO = "'Geist Mono', 'SF Mono', ui-monospace, 'Cascadia Code', 'JetBrains Mono', Menlo, Consolas, monospace"

# Each theme: light + dark tokens. card = card fill, surface = tiles on a card, line = hairlines,
# fg / body / muted = text at three strengths (≥ 4.5:1 on card), ink / on_ink = the solid chip,
# accents = the four sparkle colours (accent 1 also tints serif accents and rules).
_NEUTRAL_L = dict(card="#F5F5F7", card_hi="#FFFFFF", card_lo="#EDEDF2", surface="#FFFFFF", line="#E3E3E8",
                  fg="#1D1D1F", body="#424245", muted="#6E6E73", ink="#1D1D1F", on_ink="#FFFFFF", shadow=".08")
_NEUTRAL_D = dict(card="#161B22", card_hi="#1C2230", card_lo="#11151B", surface="#21262D", line="#30363D",
                  fg="#F5F5F7", body="#D0D7DE", muted="#8B949E", ink="#F5F5F7", on_ink="#161B22", shadow=".45")
THEMES = {
    "keynote": (["#4285F4", "#EA4335", "#FBBC04", "#34A853"], ["#8AB4F8", "#F28B82", "#FDD663", "#81C995"]),
    "aurora":  (["#7C3AED", "#DB2777", "#0891B2", "#65A30D"], ["#A78BFA", "#F472B6", "#22D3EE", "#A3E635"]),
    "sunset":  (["#EA580C", "#DB2777", "#CA8A04", "#7C3AED"], ["#FB923C", "#F472B6", "#FACC15", "#A78BFA"]),
    "ocean":   (["#0369A1", "#0D9488", "#2563EB", "#0891B2"], ["#38BDF8", "#2DD4BF", "#60A5FA", "#22D3EE"]),
    "forest":  (["#15803D", "#B45309", "#0F766E", "#65A30D"], ["#4ADE80", "#FBBF24", "#2DD4BF", "#A3E635"]),
    "mono":    (["#1D1D1F", "#6E6E73", "#1D1D1F", "#A1A1A6"], ["#F5F5F7", "#8B949E", "#F5F5F7", "#6E7681"]),
}
VISUALS = ["network", "wave", "chart", "grid", "chat", "orbit", "code"]
BLOCKS = ["hero", "dock", "section", "about", "stack", "projects", "achievements", "stats", "markdown", "footer"]

# 24×24 line icons for things Simple Icons doesn't cover (drawn with stroke, not fill).
LINE_ICONS = {
    "mail": "M3 6.5A1.5 1.5 0 0 1 4.5 5h15A1.5 1.5 0 0 1 21 6.5v11a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5zM3.5 6l8.5 7 8.5-7",
    "globe": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18zM3 12h18M12 3c2.6 2.7 3.8 5.7 3.8 9s-1.2 6.3-3.8 9c-2.6-2.7-3.8-5.7-3.8-9S9.4 5.7 12 3z",
    "link": "M10 14a4.5 4.5 0 0 0 6.4 0l3-3a4.5 4.5 0 0 0-6.4-6.4l-1.2 1.2M14 10a4.5 4.5 0 0 0-6.4 0l-3 3a4.5 4.5 0 0 0 6.4 6.4l1.2-1.2",
    "file": "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M9 13h6M9 17h6",
    "phone": "M5 4h3.5l1.5 4-2 1.5a11 11 0 0 0 6.5 6.5L16 14l4 1.5V19a1.5 1.5 0 0 1-1.6 1.5A16.5 16.5 0 0 1 3.5 5.6 1.5 1.5 0 0 1 5 4z",
    "pin": "M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11zM12 7.5a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5z",
    "rss": "M5 5a14 14 0 0 1 14 14M5 11a8 8 0 0 1 8 8M5.5 18.5h.01",
    "code": "M8.5 7 3.5 12l5 5M15.5 7l5 5-5 5M13.5 4.5l-3 15",
    "terminal": "M4 6l6 6-6 6M12 18h8",
    "star": "M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z",
}
ALIASES = {
    "js": "javascript", "ts": "typescript", "py": "python", "c++": "cplusplus", "cpp": "cplusplus", "golang": "go",
    "aws": "amazonwebservices", "amazon web services": "amazonwebservices", "gcp": "googlecloud", "google cloud": "googlecloud",
    "node": "nodedotjs", "nodejs": "nodedotjs", "next": "nextdotjs", "nextjs": "nextdotjs", "vue": "vuedotjs", "nuxt": "nuxtdotjs",
    "k8s": "kubernetes", "postgres": "postgresql", "mongo": "mongodb", "gemini": "googlegemini", "hf": "huggingface",
    "hugging face": "huggingface", "sklearn": "scikitlearn", "scikit-learn": "scikitlearn", "tailwind": "tailwindcss",
    "github actions": "githubactions", "gh actions": "githubactions", "rails": "rubyonrails", ".net": "dotnet",
    "twitter": "x", "dev.to": "devdotto", "email": "mail", "e-mail": "mail", "website": "globe", "portfolio": "globe",
    "web": "globe", "site": "globe", "blog": "rss", "resume": "file", "cv": "file", "location": "pin",
}


# Shorter labels for icon titles that don't fit under a 68 px tile.
SHORT = {"Amazon Web Services": "AWS", "Google Gemini": "Gemini", "Hugging Face": "Hugging Face", "GitHub Actions": "Actions",
         "Ruby on Rails": "Rails", "scikit-learn": "scikit-learn", "Visual Studio Code": "VS Code"}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def die(msg):
    sys.exit(f"make_page.py: {msg}")


# ---------------------------------------------------------------- colour

def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(v))):02X}" for v in rgb)


def lum(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in _rgb(h))
    return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


def mix(a, b, t):
    return _hex([x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))])


def readable(color, bg, need=3.0):
    """Nudge color toward black or white until it reaches `need`:1 on bg (keeps the hue)."""
    target = "#000000" if lum(bg) > .4 else "#FFFFFF"
    c, t = color, 0.0
    while contrast(c, bg) < need and t < 1:
        t += .05
        c = mix(color, target, t)
    return c


class T:
    """Tokens for one theme + mode, plus helpers the cards share."""

    def __init__(self, theme, mode, accents=None):
        if theme not in THEMES:
            die(f"unknown theme {theme!r}; choose from {', '.join(THEMES)}")
        self.mode = mode
        self.__dict__.update(_NEUTRAL_L if mode == "light" else _NEUTRAL_D)
        acc = THEMES[theme][0 if mode == "light" else 1]
        if accents:
            acc = [a if mode == "light" else readable(a, self.card, 4.5) for a in (accents * 4)[:4]]
        self.acc = acc

    def a(self, i):
        return self.acc[i % 4]

    def text_accent(self, i, bg=None, need=4.5):
        return readable(self.a(i), bg or self.card, need)


# ---------------------------------------------------------------- text metrics (approximate)

# Advance widths (per 100 px) of ASCII 32–126, measured in the browser for the stacks above
# (Segoe UI regular / bold, Georgia italic); ×1.04 leaves room for SF Pro and Roboto.
_ADV = {
    "S4": [27, 28, 39, 59, 54, 82, 80, 23, 30, 30, 42, 68, 22, 40, 22, 39, 54, 54, 54, 54, 54, 54, 54, 54, 54, 54, 22, 22, 68, 68, 68, 45, 96, 65, 57, 62, 70, 51, 49, 69, 71, 27, 36, 58, 47, 90, 75, 75, 56, 75, 60, 53, 52, 69, 62, 93, 59, 55, 57, 30, 38, 30, 68, 42, 27, 51, 59, 46, 59, 52, 31, 59, 57, 24, 24, 50, 24, 86, 57, 59, 59, 59, 35, 42, 34, 57, 48, 72, 46, 48, 45, 30, 24, 30, 68],
    "S7": [28, 33, 49, 59, 58, 87, 85, 29, 37, 37, 46, 71, 27, 40, 27, 44, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 27, 27, 71, 71, 71, 44, 95, 70, 64, 62, 74, 53, 52, 71, 77, 32, 45, 65, 51, 96, 79, 76, 61, 76, 65, 56, 59, 72, 67, 100, 66, 61, 61, 37, 44, 37, 71, 42, 31, 54, 62, 48, 62, 54, 38, 62, 60, 28, 28, 56, 28, 92, 60, 61, 62, 62, 40, 44, 39, 60, 54, 80, 55, 54, 48, 37, 33, 37, 71],
    "I4": [24, 33, 41, 64, 61, 82, 71, 22, 38, 38, 47, 64, 27, 37, 27, 47, 61, 43, 56, 55, 56, 53, 57, 50, 60, 57, 38, 38, 64, 64, 64, 48, 93, 67, 65, 64, 75, 65, 60, 73, 81, 39, 52, 69, 60, 93, 77, 73, 61, 73, 70, 56, 62, 76, 67, 98, 71, 62, 60, 38, 47, 38, 64, 64, 50, 57, 55, 45, 58, 47, 33, 57, 56, 30, 29, 53, 29, 88, 59, 54, 58, 56, 46, 43, 35, 58, 54, 82, 50, 56, 44, 43, 38, 43, 64],
}
_OTHER = {"—": 100, "–": 50, "·": 30, "’": 25, "‘": 25, "“": 42, "”": 42, "−": 68, "…": 90, "↗": 70, "→": 70, "×": 60}


def _adv(ch, table):
    o = ord(ch)
    return _ADV[table][o - 32] if 32 <= o <= 126 else _OTHER.get(ch, 62)


def text_w(s, size, weight=400, kind="sans", spacing=0.0):
    if kind == "mono":
        return len(s) * size * .6 + spacing * max(len(s) - 1, 0)
    if kind == "serif":
        units = sum(_adv(ch, "I4") for ch in s)
    else:
        bold = {400: 0, 500: .25, 600: .55, 700: 1}.get(weight, 0)
        units = sum(_adv(ch, "S4") * (1 - bold) + _adv(ch, "S7") * bold for ch in s)
    return units / 100 * size * 1.04 + spacing * max(len(s) - 1, 0)


def fit(s, size, max_w, weight=400, kind="sans", spacing=0.0, floor=.6):
    """Largest font size ≤ size (down to floor×size) at which s fits max_w."""
    sz = size
    while sz > size * floor and text_w(s, sz, weight, kind, spacing * sz / size) > max_w:
        sz -= .5
    return round(sz, 1)


def wrap(s, size, max_w, weight=400, kind="sans", spacing=0.0):
    lines, cur = [], ""
    for word in str(s).split():
        trial = f"{cur} {word}".strip()
        if cur and text_w(trial, size, weight, kind, spacing) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


def rich_tokens(s):
    """'I build *useful* things' → [(word, is_accent)]. *…* = serif accent, **…** = bold."""
    out = []
    for i, part in enumerate(re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", str(s))):
        if not part:
            continue
        style = "bold" if part.startswith("**") else "accent" if part.startswith("*") else ""
        for w in part.strip("*").split():
            out.append((w, style))
    return out


def wrap_rich(s, size, max_w, weight, accent_scale=1.15):
    lines, cur, cur_w = [], [], 0.0
    for word, style in rich_tokens(s):
        ww = text_w(word, size * accent_scale, 400, "serif") if style == "accent" else text_w(word, size, weight)
        sp = size * .27
        if cur and cur_w + sp + ww > max_w:
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur.append((word, style))
        cur_w += (sp if len(cur) > 1 else 0) + ww
    if cur:
        lines.append(cur)
    return lines


def rich_line(tokens, x, y, size, weight, fill, t: T, spacing=0.0, accent_i=0, accent_scale=1.15, extra=""):
    parts, prev = [], None
    for word, style in tokens:
        gap = " " if prev is not None else ""
        if style == "accent":
            parts.append(f'{gap}<tspan class="serif" fill="{t.text_accent(accent_i, need=3)}" font-size="{size * accent_scale:.0f}" letter-spacing="0">{esc(word)}</tspan>')
        elif style == "bold":
            parts.append(f'{gap}<tspan font-weight="700" fill="{t.fg}">{esc(word)}</tspan>')
        else:
            parts.append(gap + esc(word))
        prev = style
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'letter-spacing="{spacing}"{extra} xml:space="preserve">{"".join(parts)}</text>')


def txt(x, y, s, size, fill, weight=400, cls="", anchor="", spacing=0, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    c = f' class="{cls}"' if cls else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}"{a}{ls}{c}{extra}>{esc(s)}</text>'


# ---------------------------------------------------------------- shared shapes

def star(x, y, r, color, cls="twinkle", delay=0.0):
    return (f'<g transform="translate({x:.1f},{y:.1f})"><path d="M0,{-r:.1f} Q0,0 {r:.1f},0 Q0,0 0,{r:.1f} '
            f'Q0,0 {-r:.1f},0 Q0,0 0,{-r:.1f}Z" fill="{color}" class="{cls}" style="animation-delay:{delay:.2f}s"/></g>')


def scatter(t: T, spots, seed):
    """Sparkles at the given (x, y, r) spots, colours and timings varied but deterministic."""
    rnd = random.Random(seed)
    out = []
    for i, (x, y, r) in enumerate(spots):
        cls = "twinkle" if r >= 9 else "glint"
        out.append(star(x, y, r, t.a(i + rnd.randrange(4)), cls, rnd.uniform(0, 2.8)))
    return "".join(out)


def pill(x, y, label, color, t: T, size=11.5, h=28):
    w = text_w(label, size, 600, "mono", 1.2) + 30
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{t.surface}" stroke="{t.line}"/>'
            + txt(x + w / 2, y + h / 2 + size * .36, label, size, readable(color, t.surface, 4.5), 600, "mono", "middle", 1.2)), w


def chip(x, y, label, t: T, size=13.5, h=32):
    w = text_w(label, size, 600) + 34
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{t.ink}"/>'
            + txt(x + w / 2, y + h / 2 + size * .36, label, size, t.on_ink, 600, anchor="middle")), w


def arrow_btn(cx, cy, r, t: T):
    s = r * .35
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t.surface}" stroke="{t.line}"/>'
            f'<path d="M{cx - s:.1f},{cy + s:.1f} L{cx + s:.1f},{cy - s:.1f} M{cx - s * .7:.1f},{cy - s:.1f} H{cx + s:.1f} V{cy + s * .7:.1f}" '
            f'fill="none" stroke="{t.fg}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')


def resolve_icon(name):
    """slug | alias | title → ('brand', meta) | ('line', path) | (None, None)."""
    if not name:
        return None, None
    key = str(name).strip().lower()
    key = ALIASES.get(key, key)
    if key in LINE_ICONS:
        return "line", LINE_ICONS[key]
    slug = re.sub(r"[^a-z0-9]", "", key.replace("+", "plus").replace(".", "dot"))
    if slug in ICONS:
        return "brand", ICONS[slug]
    for meta in ICONS.values():
        if meta["title"].lower() == key:
            return "brand", meta
    return None, None


def icon(name, x, y, size, t: T, bg, fallback="", color=None):
    """Draw an icon in a size×size box at (x, y). Unknown names become a monogram."""
    kind, data = resolve_icon(name)
    sc = size / 24
    if kind == "brand":
        c = color or "#" + data["hex"]
        if contrast(c, bg) < 1.6:
            c = t.fg
        return f'<path transform="translate({x:.1f},{y:.1f}) scale({sc:.4f})" d="{data["path"]}" fill="{c}"/>'
    if kind == "line":
        c = color or t.text_accent(0, bg, 3)
        return (f'<path transform="translate({x:.1f},{y:.1f}) scale({sc:.4f})" d="{data}" fill="none" stroke="{c}" '
                f'stroke-width="{1.8:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    mono = re.sub(r"[^A-Za-z0-9#+]", "", str(fallback or name))[:2].capitalize() or "•"
    fs = size * (.62 if len(mono) == 1 else .5)
    return txt(x + size / 2, y + size / 2 + fs * .36, mono, round(fs, 1), color or t.text_accent(0, bg), 700, "mono", "middle")


def embed(path, base: Path):
    p = (base / path) if not Path(path).is_absolute() else Path(path)
    if not p.exists():
        die(f"image not found: {p}")
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
            ".gif": "image/gif", ".svg": "image/svg+xml"}.get(p.suffix.lower())
    if not mime:
        die(f"unsupported image type: {p.name} (use png, jpg, webp, gif or svg)")
    data = p.read_bytes()
    if len(data) > 250_000:
        print(f"warning: {p.name} is {len(data) // 1024} KB; resize it to ~600 px wide so the card stays light", file=sys.stderr)
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


# ---------------------------------------------------------------- SVG document

CSS_DECOR = """
.twinkle{animation:twinkle 3.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.glint{animation:glint 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.spin{animation:spin 14s linear infinite;transform-box:fill-box;transform-origin:center}
.blink{animation:blink 1.1s steps(1) infinite}
.ripple{animation:ripple 3.6s ease-out infinite;transform-box:fill-box;transform-origin:center}
.breathe{animation:breathe 3.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.drop{animation:drop 3.6s cubic-bezier(.55,0,.9,.5) infinite;transform-box:fill-box;transform-origin:center top}
.zoom{animation:zoom 18s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
.dash{animation:dash 6s linear infinite}
@keyframes twinkle{0%,100%{opacity:.35;transform:scale(.55) rotate(0)}50%{opacity:1;transform:scale(1) rotate(45deg)}}
@keyframes glint{0%,100%{opacity:.15;transform:scale(.3)}50%{opacity:1;transform:scale(1)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes blink{50%{opacity:0}}
@keyframes ripple{0%{opacity:.6;transform:scale(.3)}100%{opacity:0;transform:scale(1.7)}}
@keyframes breathe{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.55)}}
@keyframes drop{0%,30%{opacity:0;transform:translateY(0) scale(.4)}40%{opacity:1;transform:translateY(0) scale(1)}85%{opacity:1;transform:translateY(70px) scale(1,1.15)}100%{opacity:0;transform:translateY(84px) scale(1.2,.6)}}
@keyframes zoom{from{transform:scale(1)}to{transform:scale(1.07)}}
@keyframes dash{to{stroke-dashoffset:-84}}
"""
CSS_ENTRANCE = """
.up{animation:up .9s cubic-bezier(.2,.8,.2,1) both}
@keyframes up{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
"""


def doc(w, h, label, body, motion, defs="", fonts=""):
    css = (f"{fonts}text{{font-family:{SANS};font-kerning:normal}}"
           f".mono{{font-family:{MONO}}}.serif{{font-family:{SERIF};font-style:italic;font-weight:400}}")
    if motion != "static":
        css += CSS_DECOR + (CSS_ENTRANCE if motion == "entrance" else "")
        css += "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{esc(label)}"><title>{esc(label)}</title><style>{css}</style><defs>{defs}</defs>{body}</svg>\n')


# ---------------------------------------------------------------- cards

def drip_card(t: T, top, bottom, drips, flip, H, gid):
    """Window card whose bottom edge melts into drips (flip=True mirrors it for the footer)."""
    d = f"M70,{top} H1130 Q1160,{top} 1160,{top + 30} V{bottom - 30} Q1160,{bottom} 1130,{bottom}"
    for c, r, end in sorted(drips, reverse=True):
        mid = bottom + (end - bottom) * .3
        d += (f" H{c + r + 20:.1f} C{c + r + .5:.1f},{bottom} {c + r:.1f},{mid:.1f} {c + r:.1f},{end:.1f}"
              f" A{r},{r} 0 0 1 {c - r:.1f},{end:.1f} C{c - r:.1f},{mid:.1f} {c - r - .5:.1f},{bottom} {c - r - 20:.1f},{bottom}")
    d += f" H70 Q40,{bottom} 40,{bottom - 30} V{top + 30} Q40,{top} 70,{top} Z"
    tf = f' transform="translate(0,{H}) scale(1,-1)"' if flip else ""
    y1, y2 = ("1", "0") if flip else ("0", "1")
    defs = (f'<linearGradient id="{gid}" x1="0" y1="{y1}" x2="0" y2="{y2}"><stop offset="0" stop-color="{t.card_hi}"/>'
            f'<stop offset=".55" stop-color="{t.card}"/><stop offset="1" stop-color="{t.card_lo}"/></linearGradient>'
            f'<filter id="soft" x="-10%" y="-10%" width="120%" height="140%"><feDropShadow dx="0" dy="18" stdDeviation="22" '
            f'flood-color="#000" flood-opacity="{t.shadow}"/></filter>'
            f'<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".16"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    return defs, f'<g filter="url(#soft)"><path d="{d}" fill="url(#{gid})" stroke="{t.line}" stroke-width="1.5"{tf}/></g>'


def make_drips(seed, n=5):
    rnd = random.Random(seed)
    xs = sorted(rnd.sample(range(1, 10), n))
    return [(130 + x * 105 + rnd.randint(-25, 25), rnd.choice([10, 11, 13, 14, 15]), 420 + rnd.randint(38, 120)) for x in xs]


def window(t: T, spec, y0, base: Path, prompt_default):
    """Traffic lights, title bar and the hero/footer content block, starting at y0."""
    o = [f'<g transform="translate(0,{y0})">',
         f'<circle cx="78" cy="76" r="6.5" fill="#FF5F57"/><circle cx="100" cy="76" r="6.5" fill="#FEBC2E"/><circle cx="122" cy="76" r="6.5" fill="#28C840"/>',
         txt(600, 81, spec.get("window", ""), 13, t.muted, 500, "mono", "middle"),
         f'<line x1="40" y1="108" x2="1160" y2="108" stroke="{t.line}"/>',
         '<g class="up">']
    tile_bg = t.ink
    o.append(f'<rect x="96" y="168" width="156" height="156" rx="38" fill="{tile_bg}" stroke="{t.line}"/>'
             f'<rect x="96" y="168" width="156" height="156" rx="38" fill="url(#sheen)"/>')
    if spec.get("logo"):
        o.append(f'<clipPath id="tile"><rect x="96" y="168" width="156" height="156" rx="38"/></clipPath>'
                 f'<image href="{embed(spec["logo"], base)}" x="116" y="188" width="116" height="116" preserveAspectRatio="xMidYMid meet" clip-path="url(#tile)"/>')
    elif spec.get("initials"):
        ini = str(spec["initials"])[:3]
        o.append(txt(174, 246 + 22, ini, fit(ini, 64, 120, 700), t.on_ink, 700, anchor="middle", spacing=-2))
    else:
        o.append(f'<path d="M134,216 L163,242 L134,268" fill="none" stroke="{t.on_ink}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<rect x="176" y="258" width="42" height="10" rx="5" fill="{t.a(3)}" class="blink"/>')
    o.append("</g>")
    o.append(txt(296, 172, spec.get("prompt", prompt_default), 15, t.muted, 400, "mono up"))
    status_w = 0
    if spec.get("status"):
        s = spec["status"]
        status_w = text_w(s, 13.5, 500) + 52
        x = 1116 - status_w
        o.append(f'<g class="up"><rect x="{x:.1f}" y="140" width="{status_w:.1f}" height="34" rx="17" fill="{t.surface}" stroke="{t.line}"/>'
                 f'<circle cx="{x + 20:.1f}" cy="157" r="5" fill="{t.a(3)}"/><circle cx="{x + 20:.1f}" cy="157" r="5" fill="{t.a(3)}" class="ripple"/>'
                 + txt(x + 34, 161.5, s, 13.5, t.body, 500) + "</g>")
    greet = spec.get("greeting", "")
    if greet:
        o.append(txt(292, 246, greet, fit(greet, 84, 820, 400, "serif"), t.body, 400, "serif up", spacing=-1))
    title = spec.get("title", "")
    o.append(txt(290, 330, title, fit(title, 88, 830, 700, spacing=-4.2), t.fg, 700, "up", spacing=-4.2))
    meta = [m for m in spec.get("meta", []) if m]
    if meta:
        size = 19
        def total(sz):
            return sum(text_w(re.sub(r"\*", "", m), sz) for m in meta) + (len(meta) - 1) * sz * 2.1
        while size > 14 and total(size) > 840:
            size -= .5
        x, parts = 296.0, []
        for i, m in enumerate(meta):
            if i:
                parts.append(star(x + size * .75, 375, size * .47, t.a(i), "twinkle", .7 * i))
                x += size * 2.1
            parts.append(rich_line(rich_tokens(m), x, 382, size, 400, t.muted, t))
            x += text_w(re.sub(r"\*", "", m), size)
        o.append('<g class="up">' + "".join(parts) + "</g>")
    o.append("</g>")
    return "".join(o)


def card_hero(spec, t, ctx, footer=False):
    drips = spec.get("drips", True)
    H = 600 if drips else 460
    seed = (spec.get("title", "") + ("f" if footer else "h"))
    dr = make_drips(seed) if drips else []
    defs, shell = drip_card(t, 40, 420, dr, footer, H, "card")
    y0 = 140 if (footer and drips) else 0
    body = [shell, window(t, spec, y0, ctx["base"], "~ $ ./say-hello --to you" if footer else '~ $ echo "$GREETING"')]
    rnd = random.Random(seed)
    if drips:
        for i, (c, r, end) in enumerate(dr[:4]):
            y = (H - end - 12) if footer else end + 12
            cls = "" if footer else "drop"
            body.append(f'<circle cx="{c}" cy="{y}" r="{r * .55:.1f}" fill="{t.a(i)}" class="{cls}" style="animation-delay:{i * .9:.1f}s"/>')
        band = (20, 130) if footer else (470, 580)
        body.append(scatter(t, [(x, rnd.randint(*band), rnd.choice([6.4, 8, 11.2, 14.4, 17.6])) for x in range(120, 1160, 170)], seed))
    # outside the text column (x 290–1120) so long titles never run into a sparkle
    edge = [(22, 250 + y0, 14.4), (1180, 150 + y0, 16), (1180, 345 + y0, 9.6), (60, 20 if not footer else 580, 11.2),
            (1140, 236 + y0, 12.8), (1130, 300 + y0, 8)]
    body.append(scatter(t, edge, seed + "e"))
    label = spec.get("alt") or " — ".join(x for x in (f'{spec.get("greeting", "")} {spec.get("title", "")}'.strip(),
                                                     ", ".join(re.sub(r"\*", "", m) for m in spec.get("meta", []))) if x)
    return doc(1200, H, label, "".join(body), ctx["motion"], defs), label


def card_dock(item, t, ctx):
    label, handle = item.get("label", ""), item.get("handle", "")
    body = [f'<defs><linearGradient id="dsheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t.surface}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{t.card}"/></linearGradient></defs>',
            f'<rect x="24" y="12" width="96" height="96" rx="26" fill="{t.surface}" stroke="{t.line}" stroke-width="1.5"/>',
            f'<rect x="24" y="12" width="96" height="96" rx="26" fill="url(#dsheen)"/>',
            icon(item.get("icon", label), 52, 40, 40, t, t.surface, label),
            txt(72, 140, label, fit(label, 17, 136, 600), t.fg, 600, anchor="middle", spacing=-.3)]
    if handle:
        body.append(txt(72, 162, handle, fit(handle, 15, 138, 400, "serif"), t.muted, 400, "serif", "middle"))
    body.append(scatter(t, [(116, 16, 14.4), (20, 100, 6.4)], label))
    alt = item.get("alt") or " — ".join(x for x in (label, handle) if x)
    return doc(144, 176, alt, "".join(body), ctx["motion"]), alt


def card_section(spec, t, ctx):
    n, total = ctx["section_no"], ctx["section_total"]
    title, sub = spec.get("title", ""), spec.get("subtitle", "")
    ts = fit(title, 44, 760, 600, spacing=-1.6)
    tw = text_w(title, ts, 600, spacing=-1.6 * ts / 44)
    i = n - 1
    body = ['<g class="up">', f'<g transform="translate(30,58)"><path d="M0,-20 Q0,0 20,0 Q0,0 0,20 Q0,0 -20,0 Q0,0 0,-20Z" fill="{t.a(i)}" class="spin"/></g>',
            txt(62, 74, title, ts, t.fg, 600, spacing=-1.6)]
    if sub:
        body.append(txt(62 + tw + 18, 74, sub, fit(sub, 27, 1040 - tw - 80, 400, "serif"), t.muted, 400, "serif"))
    body += [txt(1184, 70, f"{n:02d} / {total:02d}", 13, t.muted, 500, "mono", "end", 1),
             f'<line x1="16" y1="102" x2="1184" y2="102" stroke="{t.line}" stroke-width="1.5"/>',
             f'<line x1="16" y1="102" x2="96" y2="102" stroke="{t.a(i)}" stroke-width="3" stroke-linecap="round"/>', "</g>",
             scatter(t, [(1084, 40, 11.2), (1050, 70, 6.4), (1112, 82, 8), (960, 36, 6.4)], title)]
    alt = f"{n:02d} — {title}" + (f", {sub}" if sub else "")
    return doc(1200, 112, alt, "".join(body), ctx["motion"]), alt


def card_about(spec, t, ctx):
    items = spec.get("items", [])
    col_w = 512 if items else 1000
    hs = 54
    head = wrap_rich(spec.get("headline", ""), hs, col_w, 600)
    while len(head) > 3 and hs > 40:
        hs -= 2
        head = wrap_rich(spec.get("headline", ""), hs, col_w, 600)
    o = ['<g class="up">', txt(88, 86, spec.get("eyebrow", "ABOUT").upper(), 12.5, t.muted, 500, "mono", spacing=3)]
    y = 86 + hs * 1.38
    for ln in head:
        o.append(rich_line(ln, 85, y, hs, 600, t.fg, t, -hs * .044))
        y += hs * 1.15
    o.append("</g><g class=\"up\">")
    y += 6
    for ln in wrap(spec.get("body", ""), 18, col_w) if spec.get("body") else []:
        o.append(txt(88, y, ln, 18, t.body))
        y += 26
    if spec.get("quote"):
        y += 30
        for ln in wrap(spec["quote"], 24, col_w, kind="serif"):
            o.append(txt(88, y, ln, 24, t.muted, cls="serif"))
            y += 30
    o.append("</g>")
    left_h = y
    ry = 86
    if items:
        o.append(f'<line x1="640" y1="70" x2="640" y2="__H__" stroke="{t.line}" stroke-width="1.5"/>')
        o.append(txt(676, 86, spec.get("eyebrow_right", "RIGHT NOW").upper(), 12.5, t.muted, 500, "mono up", spacing=3))
        ry = 124
        for i, it in enumerate(items[:5]):
            o.append('<g class="up">' + star(680, ry - 6, 10, t.a(i), "twinkle", .6 * i)
                     + txt(700, ry, it.get("label", ""), 18, t.fg, 600, spacing=-.2))
            lines = wrap(it.get("text", ""), 16, 440)
            for k, ln in enumerate(lines[:2]):
                o.append(txt(700, ry + 25 + k * 21, ln, 16, t.muted))
            o.append("</g>")
            ry += 66 + 21 * (min(len(lines), 2) - 1)
    H = int(max(left_h, ry) + 50)
    o = [s.replace("__H__", str(H - 70)) for s in o]
    body = f'<rect x="16" y="10" width="1168" height="{H - 20}" rx="32" fill="{t.card}"/>' + "".join(o)
    body += scatter(t, [(1140, 52, 17.6), (1110, 80, 8), (600, H - 50, 12.8), (560, 64, 8), (1150, H - 40, 9.6)], "about")
    plain = re.sub(r"\*", "", spec.get("headline", ""))
    alt = spec.get("alt") or f"About: {plain} " + " ".join(f'{it.get("label", "")} {it.get("text", "")};' for it in items).strip()
    return doc(1200, H, alt.strip(" ;"), body, ctx["motion"]), alt.strip(" ;")


def card_stack(spec, t, ctx):
    groups = spec.get("groups", [])
    if not groups:
        die("stack block needs groups: [{label, items: [...]}]")
    per_row, o, y, names, k = 7, [], 54, [], 0
    for gi, g in enumerate(groups):
        items = [it if isinstance(it, dict) else {"icon": it} for it in g.get("items", [])]
        rows = [items[i:i + per_row] for i in range(0, len(items), per_row)] or [[]]
        o.append('<g class="up">' + star(86, y + 41, 10, t.a(gi), "twinkle", .5 * gi)
                 + txt(106, y + 47, g.get("label", ""), fit(g.get("label", ""), 18, 176, 600), t.fg, 600, spacing=-.2) + "</g>")
        for row in rows:
            for c, it in enumerate(row):
                x = 290 + c * 122
                kind, meta = resolve_icon(it.get("icon") or it.get("name"))
                name = it.get("name") or (SHORT.get(meta["title"], meta["title"]) if kind == "brand" else str(it.get("icon", "")).title())
                names.append(name)
                o.append(f'<g class="up"><rect x="{x}" y="{y}" width="68" height="68" rx="19" fill="{t.surface}" stroke="{t.line}"/>'
                         + icon(it.get("icon") or name, x + 19, y + 19, 30, t, t.surface, name, it.get("color"))
                         + txt(x + 34, y + 92, name, fit(name, 13.5, 116, 500), t.body, 500, anchor="middle") + "</g>")
                k += 1
            y += 128
        if gi < len(groups) - 1:
            o.append(f'<line x1="80" y1="{y - 18}" x2="1120" y2="{y - 18}" stroke="{t.line}"/>')
    H = y + 30
    body = f'<rect x="16" y="10" width="1168" height="{H - 20}" rx="32" fill="{t.card}"/>' + "".join(o)
    body += scatter(t, [(1150, 44, 12.8), (1120, 74, 6.4), (1160, H - 40, 9.6)], "stack")
    alt = spec.get("alt") or "Tech stack — " + ", ".join(names)
    return doc(1200, H, alt, body, ctx["motion"]), alt


def visual(kind, x, y, w, h, t: T, seed):
    """Small animated illustration inside (x, y, w, h)."""
    rnd = random.Random(seed)
    cx, cy = x + w / 2, y + h / 2
    o = []
    if kind == "network":
        pts = [(x + w * fx, y + h * fy) for fx, fy in ((.12, .25), (.36, .62), (.6, .32), (.86, .7), (.25, .9), (.68, .95))]
        o.append(f'<path d="M{" L".join(f"{a:.0f},{b:.0f}" for a, b in pts[:4])}" fill="none" stroke="{t.a(0)}" stroke-width="3" stroke-dasharray="6 8" stroke-linecap="round" class="dash"/>')
        for i, (a, b) in enumerate(pts):
            r = 6 if i % 2 == 0 else 9
            o.append(f'<circle cx="{a:.0f}" cy="{b:.0f}" r="{r}" fill="{t.a(i)}"/><circle cx="{a:.0f}" cy="{b:.0f}" r="14" fill="{t.a(i)}" class="ripple" style="animation-delay:{i * .5:.1f}s"/>')
    elif kind == "wave":
        n = 11
        step = w / n
        for i in range(n):
            bh = h * (.2 + .8 * abs(((i * 7 + 3) % 11) / 10 - .1))
            o.append(f'<rect x="{x + i * step:.0f}" y="{cy - bh / 2:.0f}" width="{step * .5:.0f}" height="{bh:.0f}" rx="{step * .25:.1f}" fill="{t.a(i)}" class="breathe" style="animation-delay:{i * .15:.2f}s"/>')
    elif kind == "chart":
        vals = [.2, .35, .3, .5, .45, .7, .62, .9]
        pts = [(x + w * i / (len(vals) - 1), y + h * (1 - v)) for i, v in enumerate(vals)]
        line = " L".join(f"{a:.0f},{b:.0f}" for a, b in pts)
        o.append(f'<linearGradient id="area{seed[:3]}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t.a(0)}" stop-opacity=".25"/><stop offset="1" stop-color="{t.a(0)}" stop-opacity="0"/></linearGradient>')
        o.append(f'<path d="M{line} L{x + w:.0f},{y + h:.0f} L{x:.0f},{y + h:.0f}Z" fill="url(#area{seed[:3]})"/>')
        o.append(f'<path d="M{line}" fill="none" stroke="{t.a(0)}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
        ex, ey = pts[-1]
        o.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="6" fill="{t.a(3)}"/><circle cx="{ex:.0f}" cy="{ey:.0f}" r="14" fill="{t.a(3)}" class="ripple"/>')
    elif kind == "grid":
        cols, rows = 7, 4
        s = min(w / cols, h / rows) * .78
        for r in range(rows):
            for c in range(cols):
                op = .15 + .85 * rnd.random()
                cls = ' class="glint"' if rnd.random() < .18 else ""
                o.append(f'<rect x="{x + c * w / cols:.0f}" y="{y + r * h / rows:.0f}" width="{s:.0f}" height="{s:.0f}" rx="{s * .25:.1f}" fill="{t.a(r + c)}" fill-opacity="{op:.2f}"{cls} style="animation-delay:{rnd.uniform(0, 2.4):.1f}s"/>')
    elif kind == "chat":
        bw = w * .62
        for i, (fx, by) in enumerate(((0, .05), (w - bw, .38), (0, .71))):
            c = t.surface if i % 2 == 0 else t.a(0)
            o.append(f'<rect x="{x + fx:.0f}" y="{y + h * by:.0f}" width="{bw:.0f}" height="{h * .24:.0f}" rx="{h * .12:.0f}" fill="{c}" stroke="{t.line}"/>')
            for d in range(3):
                dc = t.muted if i % 2 == 0 else t.surface
                o.append(f'<circle cx="{x + fx + 26 + d * 16:.0f}" cy="{y + h * (by + .12):.0f}" r="4" fill="{dc}" class="blink" style="animation-delay:{d * .25 + i * .3:.2f}s"/>')
    elif kind == "orbit":
        r1, r2 = min(w, h) * .26, min(w, h) * .45
        o.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r1:.0f}" fill="none" stroke="{t.line}" stroke-width="1.5"/>'
                 f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r2:.0f}" fill="none" stroke="{t.line}" stroke-width="1.5" stroke-dasharray="4 6"/>'
                 f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r1 * .42:.0f}" fill="{t.a(0)}"/>')
        for i, (rr, dur) in enumerate(((r1, 9), (r2, 16), (r2, 16))):
            ang = i * 2.1
            px, py = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
            o.append(f'<g class="spin" style="animation-duration:{dur}s"><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rr:.0f}" fill="none"/>'
                     f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{7 + i * 2}" fill="{t.a(i + 1)}"/></g>')
    elif kind == "code":
        for i in range(6):
            lw = w * (.3 + .6 * rnd.random())
            ind = (i % 3) * 22
            o.append(f'<rect x="{x + ind:.0f}" y="{y + i * h / 6:.0f}" width="{lw - ind:.0f}" height="{h / 6 * .45:.0f}" rx="5" fill="{t.a(i)}" fill-opacity="{.35 + .5 * rnd.random():.2f}"/>')
        o.append(f'<rect x="{x + w * .55:.0f}" y="{y + 5 * h / 6:.0f}" width="12" height="{h / 6 * .45:.0f}" rx="2" fill="{t.fg}" class="blink"/>')
    else:
        die(f"unknown visual {kind!r}; choose from {', '.join(VISUALS)}")
    return "".join(o)


def cta_label(item):
    if item.get("cta"):
        return item["cta"]
    href = item.get("href", "")
    return "View code ↗" if "github.com" in href else "Open live ↗" if href.startswith("http") else "Open ↗"


def card_feature(item, t, ctx, i):
    o, y = [], 52
    if item.get("tag"):
        p, _ = pill(88, y, item["tag"].upper(), t.a(item.get("color", 3)), t)
        o.append(f'<g class="up">{p}</g>')
    title = item.get("title", "")
    o.append('<g class="up">' + txt(84, 136, title, fit(title, 66, 600, 700, spacing=-3), t.fg, 700, spacing=-3))
    if item.get("subtitle"):
        o.append(txt(88, 174, item["subtitle"], fit(item["subtitle"], 28, 600, 400, "serif"), t.muted, cls="serif"))
    o.append("</g>")
    y = 212
    metrics = item.get("metrics", [])[:3]
    desc = wrap(item.get("description", ""), 17, 600) if item.get("description") else []
    o.append('<g class="up">' + "".join(txt(88, y + k * 25, ln, 17, t.body) for k, ln in enumerate(desc)) + "</g>")
    y += 25 * len(desc)
    if metrics:
        my = max(292, y + 55)
        for k, m in enumerate(metrics):
            v, lab = str(m.get("value", "")), m.get("label", "")
            o.append('<g class="up">' + txt(88 + k * 196, my, v, fit(v, 40, 180, 600, spacing=-1.6), t.fg, 600, spacing=-1.6)
                     + txt(90 + k * 196, my + 26, lab, fit(lab, 14.5, 180), t.muted) + "</g>")
        y = my + 26
    H = int(max(360, y + 42))
    ph = H - 80
    o.append(f'<rect x="730" y="40" width="414" height="{ph}" rx="26" fill="{t.surface}" stroke="{t.line}"/>')
    o.append(visual(item.get("visual", VISUALS[i % len(VISUALS)]), 790, 80, 300, ph - 110, t, title))
    if item.get("tech"):
        o.append(txt(756, 40 + ph - 20, " · ".join(item["tech"]), fit(" · ".join(item["tech"]), 12, 230, kind="mono"), t.muted, cls="mono"))
    if item.get("href"):
        o.append(txt(1120, 40 + ph - 20, cta_label(item), 13.5, t.text_accent(0, t.surface), 600, anchor="end"))
    body = f'<rect x="16" y="10" width="1168" height="{H - 20}" rx="32" fill="{t.card}"/>' + "".join(o)
    body += scatter(t, [(690, 40, 14.4), (700, H - 30, 8), (40, H - 30, 9.6), (1160, 30, 11.2)], title)
    alt = item.get("alt") or " — ".join(x for x in (title, item.get("subtitle"), ", ".join(f'{m.get("value")} {m.get("label")}' for m in metrics)) if x)
    return doc(1200, H, alt, body, ctx["motion"]), alt


def card_project(item, t, ctx, i, min_h=350):
    o = []
    if item.get("tag"):
        p, _ = pill(36, 40, item["tag"].upper(), t.a(item.get("color", i)), t, 11, 26)
        o.append(f'<g class="up">{p}</g>')
    title, sub = item.get("title", ""), item.get("subtitle", "")
    o.append('<g class="up">' + txt(34, 118, title, fit(title, 40, 330, 700, spacing=-1.6), t.fg, 700, spacing=-1.6))
    if sub:
        o.append(txt(36, 148, sub, fit(sub, 21, 330, 400, "serif"), t.muted, cls="serif"))
    o.append("</g>")
    desc = wrap(item.get("description", ""), 15, 500)[:4] if item.get("description") else []
    o.append('<g class="up">' + "".join(txt(36, 188 + k * 23, ln, 15, t.body) for k, ln in enumerate(desc)) + "</g>")
    y = 188 + 23 * len(desc) + 10
    if item.get("highlight"):
        c, _ = chip(36, y, item["highlight"], t)
        o.append(f'<g class="up">{c}</g>')
        y += 32
    H = int(max(min_h, y + 74))
    if item.get("tech"):
        o.append(txt(36, H - 42, " · ".join(item["tech"]), fit(" · ".join(item["tech"]), 11.5, 440, kind="mono"), t.muted, cls="mono"))
    o.append(visual(item.get("visual", VISUALS[(i + 1) % len(VISUALS)]), 392, 60, 160, 108, t, title))
    if item.get("href"):
        o.append(arrow_btn(540, H - 50, 18, t))
    body = f'<rect x="10" y="10" width="570" height="{H - 20}" rx="30" fill="{t.card}"/>' + "".join(o)
    body += scatter(t, [(548, 230, 11.2), (360, 44, 8), (510, H - 80, 6.4)], title)
    alt = item.get("alt") or " — ".join(x for x in (title, sub, item.get("highlight")) if x)
    return doc(590, H, alt, body, ctx["motion"]), alt


def card_link(item, t, ctx, i):
    title, sub = item.get("title", ""), item.get("subtitle", "")
    o = [f'<rect x="4" y="4" width="376" height="88" rx="26" fill="{t.card}"/>',
         f'<circle cx="50" cy="48" r="22" fill="{t.surface}" stroke="{t.line}"/>']
    if item.get("icon"):
        o.append(icon(item["icon"], 39, 37, 22, t, t.surface, title))
    else:
        o.append(f'<g transform="translate(50,48)"><path d="M0,-11 Q0,0 11,0 Q0,0 0,11 Q0,0 -11,0 Q0,0 0,-11Z" fill="{t.a(i)}" class="spin"/></g>')
    o.append(txt(88, 45 if sub else 54, title, fit(title, 19, 220, 600, spacing=-.4), t.fg, 600, spacing=-.4))
    if sub:
        o.append(txt(88, 69, sub, fit(sub, 17, 220, 400, "serif"), t.muted, cls="serif"))
    o.append(arrow_btn(340, 48, 17, t))
    o.append(star(302, 22, 6.4, t.a(i + 1), "glint", 1.2))
    alt = item.get("alt") or " — ".join(x for x in (title, sub) if x)
    return doc(384, 96, alt, "".join(o), ctx["motion"]), alt


def card_achievement(item, t, ctx, i, n, min_h=430):
    title, sub = item.get("title", ""), item.get("subtitle", "")
    o = ['<g class="up">']
    if item.get("eyebrow"):
        o.append(star(316, 64, 9, t.a(i)) + txt(334, 69, item["eyebrow"].upper(), 11.5, t.muted, 600, "mono", spacing=1.6))
    ts = 34
    tl = wrap(title, ts, 262, 700)
    while len(tl) > 2 and ts > 26:
        ts -= 2
        tl = wrap(title, ts, 262, 700)
    y = 126
    for ln in tl[:3]:
        o.append(txt(309, y, ln, ts, t.fg, 700, spacing=-1.4))
        y += ts * 1.15
    if sub:
        ss = fit(sub, 38, 252, 400, "serif", floor=.55)
        o.append(txt(310, y + ss * .12, sub, ss, t.text_accent(i, need=3), cls="serif"))
        y += ss * 1.2
    o.append("</g>")
    desc = wrap(item.get("description", ""), 15.5, 252) if item.get("description") else []
    y += 10
    o.append('<g class="up">' + "".join(txt(312, y + k * 25, ln, 15.5, t.body) for k, ln in enumerate(desc)) + "</g>")
    y += 25 * len(desc)
    H = int(max(min_h, y + 100))
    if item.get("chip"):
        c, _ = chip(312, H - 92, item["chip"], t, 13, 30)
        o.append(f'<g class="up">{c}</g>')

    ph = H - 44  # photo / emblem panel on the left, full card height
    if item.get("image"):
        defs = (f'<clipPath id="ph"><rect x="22" y="22" width="260" height="{ph}" rx="22"/></clipPath>'
                f'<linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/>'
                f'<stop offset="1" stop-color="#000" stop-opacity=".55"/></linearGradient>')
        panel = (f'<g clip-path="url(#ph)"><image href="{embed(item["image"], ctx["base"])}" x="22" y="22" width="260" height="{ph}" '
                 f'preserveAspectRatio="xMidYMid slice" class="zoom"/><rect x="22" y="{22 + ph - 96}" width="260" height="96" fill="url(#shade)"/></g>')
    else:
        a = t.a(i)
        defs = (f'<linearGradient id="emb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/>'
                f'<stop offset="1" stop-color="{mix(a, "#000000", .45)}"/></linearGradient>')
        panel = f'<rect x="22" y="22" width="260" height="{ph}" rx="22" fill="url(#emb)"/>'
        cy = 22 + ph / 2 - 10
        if item.get("icon") and resolve_icon(item["icon"])[0]:
            panel += icon(item["icon"], 112, cy - 40, 80, t, "#000000", color="#FFFFFF")
        else:
            panel += f'<g transform="translate(152,{cy:.0f})"><path d="M0,-58 Q0,0 58,0 Q0,0 0,58 Q0,0 -58,0 Q0,0 0,-58Z" fill="#FFFFFF" fill-opacity=".92" class="spin"/></g>'
    panel += (f'<rect x="22" y="22" width="260" height="{ph}" rx="22" fill="none" stroke="#000" stroke-opacity=".06"/>'
              + txt(40, 22 + ph - 20, f"{i + 1:02d} / {n:02d}", 12.5, "#FFFFFF", 600, "mono", spacing=1)
              + star(260, 48, 19.2, "#FFFFFF", "twinkle", .2) + star(236, 72, 8, "#FFFFFF", "glint", 1.3))
    body = f'<rect x="2" y="2" width="586" height="{H - 4}" rx="32" fill="{t.card}"/>' + panel + "".join(o)
    body += scatter(t, [(552, 52, 16), (530, H - 34, 9.6), (566, H - 130, 6.4)], title)
    alt = item.get("alt") or " — ".join(x for x in (title, sub, item.get("description")) if x)
    return doc(590, H, alt, body, ctx["motion"], defs), alt


# ---------------------------------------------------------------- page assembly

def picture(rel, alt, width, href=None, height=None):
    size = f' height="{height}"' if height else f' width="{width}"'
    pic = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{rel}-dark.svg">'
           f'<img src="{rel}-light.svg" alt="{esc(alt)}"{size}></picture>')
    # one line: GitHub keeps <a><picture>…</picture></a> intact only when it doesn't span lines
    return f'<a href="{esc(href)}">{pic}</a>' if href else pic


def stats_block(spec, page, light: T, dark: T):
    user = spec.get("user") or page.get("github")
    if not user:
        die("stats block needs \"user\" (or a top-level \"github\")")
    out = []
    def hx(c):
        return c.lstrip("#")
    if spec.get("snake", True):
        repo = spec.get("snake_repo", f"{user}/{user}")
        base = f"https://raw.githubusercontent.com/{repo}/output"
        lf, df = spec.get("snake_files", ["github-snake.svg", "github-snake-dark.svg"])
        out.append("<!-- Snake: add templates/profile/workflows/snake.yml to this repo and run it once. -->\n"
                   f'<picture><source media="(prefers-color-scheme: dark)" srcset="{base}/{df}">'
                   f'<img src="{base}/{lf}" alt="{esc(user)}\'s contribution grid, eaten by a snake" width="100%"></picture>')
    cards = []
    if spec.get("stats", True):
        title = spec.get("title", "GitHub stats").replace(" ", "%20")

        def u(t):
            return (f"https://github-readme-stats.vercel.app/api?username={user}&show_icons=true&include_all_commits=true"
                    f"&bg_color={hx(t.card)}&title_color={hx(t.fg)}&text_color={hx(t.body)}&icon_color={hx(t.a(0))}"
                    f"&ring_color={hx(t.a(0))}&hide_border=true&border_radius=24&custom_title={title}")
        cards.append(f'<picture><source media="(prefers-color-scheme: dark)" srcset="{esc(u(dark))}"><img src="{esc(u(light))}" alt="{esc(user)}\'s GitHub stats" height="190"></picture>')
    if spec.get("streak", True):
        def s(t):
            return (f"https://streak-stats.demolab.com?user={user}&background={hx(t.card)}&border={hx(t.line)}&stroke={hx(t.line)}"
                    f"&ring={hx(t.a(0))}&fire={hx(t.a(1))}&currStreakNum={hx(t.fg)}&sideNums={hx(t.fg)}"
                    f"&currStreakLabel={hx(t.text_accent(0))}&sideLabels={hx(t.muted)}&dates={hx(t.muted)}&hide_border=true&border_radius=24")
        cards.append(f'<picture><source media="(prefers-color-scheme: dark)" srcset="{esc(s(dark))}"><img src="{esc(s(light))}" alt="{esc(user)}\'s contribution streak" height="190"></picture>')
    if cards:
        out.append("<!-- Shared public instances can be rate-limited. For reliability, self-host them or commit the SVGs from an Action (workflows/metrics.yml). -->\n"
                   + "\n".join(cards))
    return "\n\n".join(out)


def row_heights(svgs):
    """Height for each half-width card: the taller of it and its neighbour in the same row."""
    hs = [int(re.search(r'height="(\d+)"', s).group(1)) for s in svgs]
    return [max(hs[k - k % 2:k - k % 2 + 2]) for k in range(len(hs))]


def build(spec_path: Path, readme: Path | None, preview: Path | None):
    raw = spec_path.read_text(encoding="utf-8")
    left = sorted(set(re.findall(r"\{\{[^}]*\}\}", raw)))
    if left:
        die(f"{len(left)} placeholder(s) left in {spec_path.name}, e.g. {', '.join(left[:3])}. "
            "Fill them from the user's data or delete those fields/blocks.")
    page = json.loads(raw)
    base = spec_path.parent
    readme = readme or (base / page.get("readme", "README.md"))
    assets = (readme.parent / page.get("assets", "assets/page")).resolve()
    assets.mkdir(parents=True, exist_ok=True)
    theme, motion = page.get("theme", "keynote"), page.get("motion", "ambient")
    if motion not in ("ambient", "entrance", "static"):
        die("motion must be ambient, entrance or static")
    accents = page.get("accents")
    light, dark = T(theme, "light", accents), T(theme, "dark", accents)
    blocks = page.get("blocks", [])
    for b in blocks:
        if b.get("type") not in BLOCKS:
            die(f"unknown block type {b.get('type')!r}; choose from {', '.join(BLOCKS)}")
    ctx = {"base": base, "motion": motion, "section_total": sum(b["type"] == "section" for b in blocks), "section_no": 0}
    rel_dir = os.path.relpath(assets, readme.parent.resolve()).replace(os.sep, "/")
    rel_dir = rel_dir if rel_dir.startswith(".") else "./" + rel_dir
    written, md, preview_items = [], ["<!-- Generated by readme-forge-design make_page.py. Edit the spec and re-run instead of editing the SVGs. -->", "",
                                      '<div align="center">', ""], []

    def emit(stem, fn):
        alt = ""
        for t in (light, dark):
            svg, alt = fn(t)
            (assets / f"{stem}-{t.mode}.svg").write_text(svg, encoding="utf-8")
        written.append(stem)
        return f"{rel_dir}/{stem}", alt

    def gap():
        if md[-1] != "":
            md.append("")
        md.extend(["<br><br>", ""])

    seen = {}
    def stem_for(name):
        seen[name] = seen.get(name, 0) + 1
        return name if seen[name] == 1 else f"{name}-{seen[name]}"

    for b in blocks:
        kind = b["type"]
        if kind in ("hero", "footer"):
            if kind == "footer":
                gap()
            rel, alt = emit(stem_for(kind), lambda t: card_hero(b, t, ctx, kind == "footer"))
            md.append(picture(rel, alt, "100%", b.get("href")))
            preview_items.append((rel, "100%"))
            md.append("")
        elif kind == "dock":
            items = b.get("items", [])
            w = f"{min(13, 96 // max(len(items), 1))}%"
            for it in items:
                slug = re.sub(r"[^a-z0-9]+", "-", str(it.get("label", "link")).lower()).strip("-")
                rel, alt = emit(stem_for(f"dock-{slug}"), lambda t, it=it: card_dock(it, t, ctx))
                md.append(picture(rel, alt, w, it.get("href")))
                preview_items.append((rel, w))
            md.append("")
        elif kind == "section":
            gap()
            ctx["section_no"] += 1
            rel, alt = emit(stem_for(f"section-{ctx['section_no']:02d}"), lambda t: card_section(b, t, ctx))
            md.append(picture(rel, alt, "100%"))
            preview_items.append((rel, "100%"))
        elif kind == "about":
            rel, alt = emit(stem_for("about"), lambda t: card_about(b, t, ctx))
            md.append(picture(rel, alt, "100%"))
            preview_items.append((rel, "100%"))
        elif kind == "stack":
            rel, alt = emit(stem_for("stack"), lambda t: card_stack(b, t, ctx))
            md.append(picture(rel, alt, "100%"))
            preview_items.append((rel, "100%"))
        elif kind == "projects":
            items = b.get("items", [])
            sizes = {"feature": ("100%", card_feature), "card": ("49%", card_project), "link": ("32%", card_link)}
            cards = [(i, it) for i, it in enumerate(items) if it.get("size", "card") == "card"]
            heights = row_heights([card_project(it, light, ctx, i)[0] for i, it in cards])
            prev, cards_seen = None, 0
            for i, it in enumerate(items):
                size = it.get("size", "card")
                if size not in sizes:
                    die(f"project size must be feature, card or link (got {size!r})")
                if prev == "card" and size == "link":
                    md.append("")
                w, fn = sizes[size]
                slug = re.sub(r"[^a-z0-9]+", "-", str(it.get("title", "project")).lower()).strip("-")
                pre = "more" if size == "link" else "project"
                if size == "card":
                    h = heights[cards_seen]
                    cards_seen += 1
                    rel, alt = emit(stem_for(f"{pre}-{slug}"), lambda t, it=it, i=i, h=h: card_project(it, t, ctx, i, h))
                else:
                    rel, alt = emit(stem_for(f"{pre}-{slug}"), lambda t, it=it, fn=fn, i=i: fn(it, t, ctx, i))
                md.append(picture(rel, alt, w, it.get("href")))
                preview_items.append((rel, w))
                prev = size
        elif kind == "achievements":
            items = b.get("items", [])
            heights = row_heights([card_achievement(it, light, ctx, i, len(items))[0] for i, it in enumerate(items)])
            for i, it in enumerate(items):
                rel, alt = emit(stem_for(f"achievement-{i + 1:02d}"),
                                lambda t, it=it, i=i: card_achievement(it, t, ctx, i, len(items), heights[i]))
                md.append(picture(rel, alt, "49%", it.get("href")))
                preview_items.append((rel, "49%"))
        elif kind == "stats":
            block = stats_block(b, page, light, dark)
            md.extend(["", block])
            for dk, lt, attr in re.findall(r'srcset="([^"]+)"><img src="([^"]+)"[^>]*?((?:width|height)="[^"]+")', block):
                preview_items.append((html.unescape(lt), html.unescape(dk), attr))
        elif kind == "markdown":
            md.extend(["", "</div>", "", b.get("text", "").strip(), "", '<div align="center">', ""])
    md.extend(["", "</div>", ""])
    text = "\n".join(md)
    text = re.sub(r'<div align="center">\n\n</div>\n', "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    readme.write_text(text, encoding="utf-8")
    print(f"wrote {len(written) * 2} SVGs to {assets} and {readme}")
    if preview:
        write_preview(preview, assets, preview_items, readme)
        print(f"preview: {preview}")
    return written


def write_preview(path: Path, assets: Path, items, readme: Path):
    """Both themes side by side, on GitHub's own page colours."""
    def col(mode, bg):
        imgs = []
        for it in items:
            if len(it) == 3:  # remote widget: (light url, dark url, size attr)
                src, size = it[0] if mode == "light" else it[1], it[2]
                imgs.append(f'<img src="{esc(src)}" {size} style="vertical-align:top;margin:4px">')
                continue
            rel, w = it
            src = os.path.relpath((readme.parent / rel).resolve(), path.parent.resolve()).replace(os.sep, "/") + f"-{mode}.svg"
            imgs.append(f'<img src="{esc(src)}" style="width:{w};vertical-align:top">')
        return f'<section style="background:{bg};padding:24px;flex:1;text-align:center">{"".join(imgs)}</section>'
    path.write_text("<!doctype html><meta charset=utf-8><title>Page kit preview</title>"
                    "<body style='margin:0;display:flex;gap:0'>" + col("light", "#FFFFFF") + col("dark", "#0D1117") + "</body>",
                    encoding="utf-8")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Build a designed README of SVG cards from a JSON spec")
    p.add_argument("--spec", type=Path, help="page spec (JSON)")
    p.add_argument("--readme", type=Path, help="README to write (default: spec's \"readme\", else README.md next to the spec)")
    p.add_argument("--preview", type=Path, help="also write an HTML page showing both themes")
    p.add_argument("--init", choices=["profile", "project"], help="print a starter spec")
    p.add_argument("--list", action="store_true", help="themes, visuals, block types and icon names")
    a = p.parse_args(argv)
    if a.list:
        print("themes:  " + ", ".join(THEMES))
        print("visuals: " + ", ".join(VISUALS))
        print("blocks:  " + ", ".join(BLOCKS))
        print("line icons: " + ", ".join(LINE_ICONS))
        print(f"brand icons ({len(ICONS)}): " + ", ".join(sorted(ICONS)))
        return 0
    if a.init:
        sys.stdout.write((TEMPLATES / f"{a.init}.json").read_text(encoding="utf-8"))
        return 0
    if not a.spec:
        p.error("--spec is required (or use --init / --list)")
    build(a.spec, a.readme, a.preview)
    return 0


if __name__ == "__main__":
    sys.exit(main())
