#!/usr/bin/env python3
"""Generate self-contained, animated SVG headers, footers and dividers for READMEs.

Stdlib only. No external services: the SVGs are committed to the repo, so they never
rate-limit or go down. Every file ships a dark and a light variant, honours
prefers-reduced-motion, and uses system font stacks (external fonts are blocked
inside <img>).

Usage:
  python make_banner.py --style aurora --title "orbit-api" --subtitle "Subscription billing for SaaS" --out assets/
  python make_banner.py --kind footer --style wave --title "Built with care" --out assets/
  python make_banner.py --kind divider --style aurora --out assets/
  python make_banner.py --list                       # styles and palettes
  python make_banner.py --gallery assets/gallery     # every style, dark + light, + gallery.md

Options:
  --kind header|footer|divider   (default header)
  --style NAME                   see --list
  --palette NAME                 ember | ocean | violet | mint | sunset | mono | cyber (default: style's own)
  --accent "#RRGGBB"             override the main accent colour
  --title / --subtitle / --tag   text (tag = small caps line above the title)
  --width 1280 --height 320      canvas (footer default 160, divider default 24)
  --theme dark|light|both        (default both)
  --static                       no animation
  --out DIR                      output folder (default .)
Prints the <picture> snippet to paste into the README.
"""
from __future__ import annotations

import argparse
import base64
import os
import html
import math
import random
import sys
from pathlib import Path

SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Inter, Roboto, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', 'Cascadia Code', 'JetBrains Mono', Menlo, Consolas, monospace"

# Each palette: dark + light. bg0/bg1 = background gradient, fg = title, muted = subtitle,
# a1..a3 = accents. Contrast of fg/muted on bg checked ≥ 4.5:1.
PALETTES = {
    "ember":  {"dark": dict(bg0="#0B1020", bg1="#1B2550", fg="#F5F7FF", muted="#AAB3D1", a1="#FF8A3D", a2="#FF5D8F", a3="#7C5CFF"),
               "light": dict(bg0="#FFF8F1", bg1="#FFE9D6", fg="#1A1530", muted="#5B5470", a1="#E5641A", a2="#D93A6E", a3="#6A4CF0")},
    "ocean":  {"dark": dict(bg0="#04121F", bg1="#0A2A43", fg="#EAF6FF", muted="#9CC3DD", a1="#2EC5FF", a2="#3DDC97", a3="#4F7CFF"),
               "light": dict(bg0="#F2FAFF", bg1="#DDF1FF", fg="#082036", muted="#3F607A", a1="#0089C7", a2="#119E68", a3="#2F5BE0")},
    "violet": {"dark": dict(bg0="#0E0A1F", bg1="#24164A", fg="#F6F2FF", muted="#B9AEDB", a1="#A78BFA", a2="#F472B6", a3="#60A5FA"),
               "light": dict(bg0="#FAF7FF", bg1="#EEE6FF", fg="#1E1238", muted="#5E5280", a1="#7C3AED", a2="#DB2777", a3="#2563EB")},
    "mint":   {"dark": dict(bg0="#06140F", bg1="#0D2A20", fg="#ECFFF6", muted="#9FCDB8", a1="#3DDC97", a2="#2EC5FF", a3="#C6F432"),
               "light": dict(bg0="#F3FFF9", bg1="#DDF7EA", fg="#0B2A1E", muted="#3E6656", a1="#0E9F6E", a2="#0284C7", a3="#65A30D")},
    "sunset": {"dark": dict(bg0="#1A0B1E", bg1="#3B1238", fg="#FFF3EE", muted="#E3B5BE", a1="#FF7A59", a2="#FFC857", a3="#FF4F9A"),
               "light": dict(bg0="#FFF6F2", bg1="#FFE3DA", fg="#2B0F1E", muted="#7A4A5A", a1="#E8552F", a2="#C98A00", a3="#D6336C")},
    "mono":   {"dark": dict(bg0="#0A0A0A", bg1="#1C1C1C", fg="#FAFAFA", muted="#A3A3A3", a1="#FAFAFA", a2="#737373", a3="#D4D4D4"),
               "light": dict(bg0="#FFFFFF", bg1="#F2F2F2", fg="#0A0A0A", muted="#525252", a1="#0A0A0A", a2="#A3A3A3", a3="#404040")},
    "cyber":  {"dark": dict(bg0="#05010D", bg1="#140A2E", fg="#F8F5FF", muted="#B7A6E8", a1="#00F0FF", a2="#FF2BD6", a3="#FFE600"),
               "light": dict(bg0="#F7F5FF", bg1="#E9E3FF", fg="#140A2E", muted="#4F4475", a1="#008C99", a2="#C2179F", a3="#9A8600")},
}

# Premium dark palettes (dark-design galleries: never pure black, layered surfaces, hairline borders,
# one saturated accent). Each still ships a light variant.
PALETTES.update({
    "midnight": {"dark": dict(bg0="#08090A", bg1="#111216", fg="#F7F8F8", muted="#8A8F98", a1="#7C83FF", a2="#C084FC", a3="#38BDF8", surface="#141518", line="#FFFFFF"),
                 "light": dict(bg0="#FBFBFC", bg1="#F1F2F4", fg="#0D0E10", muted="#5C616B", a1="#5E6AD2", a2="#9333EA", a3="#0284C7", surface="#FFFFFF", line="#0D0E10")},
    "carbon":   {"dark": dict(bg0="#000000", bg1="#0A0A0A", fg="#EDEDED", muted="#A1A1A1", a1="#FFFFFF", a2="#3B82F6", a3="#A855F7", surface="#111111", line="#FFFFFF"),
                 "light": dict(bg0="#FFFFFF", bg1="#FAFAFA", fg="#0A0A0A", muted="#525252", a1="#0A0A0A", a2="#2563EB", a3="#9333EA", surface="#FFFFFF", line="#0A0A0A")},
    "ghost":    {"dark": dict(bg0="#070A12", bg1="#0E1424", fg="#F2F6FF", muted="#9AA7C2", a1="#19C3EC", a2="#8B4FD1", a3="#3D7FD8", surface="#101727", line="#FFFFFF"),
                 "light": dict(bg0="#F8FAFE", bg1="#EEF2FB", fg="#0C131D", muted="#4A5568", a1="#0B7FAA", a2="#6E35A8", a3="#2F6CC0", surface="#FFFFFF", line="#0C131D")},
    "obsidian": {"dark": dict(bg0="#0E1111", bg1="#161A1A", fg="#EDEFEF", muted="#8F9A99", a1="#3ECF8E", a2="#2DD4BF", a3="#A3E635", surface="#1A1F1F", line="#FFFFFF"),
                 "light": dict(bg0="#F8FAF9", bg1="#EEF3F1", fg="#0E1111", muted="#4B5655", a1="#0F9F6A", a2="#0D9488", a3="#4D7C0F", surface="#FFFFFF", line="#0E1111")},
})

# ShaderGradient's own presets (ruucm/shadergradient presets.ts: c1/c2/c3), as banner palettes.
# Dark variant = the preset on a deep base; light variant = same hues on a soft base with darker text.
def _preset(c1, c2, c3, base_dark="#07070B", base_light="#FBF8F6"):
    return {"dark": dict(bg0=base_dark, bg1="#12121A", fg="#FFFFFF", muted="#E4E2EE", a1=c1, a2=c2, a3=c3, surface="#15151D", line="#FFFFFF"),
            "light": dict(bg0=base_light, bg1="#F1ECE8", fg="#14121A", muted="#4A4652", a1=c1, a2=c2, a3=c3, surface="#FFFFFF", line="#14121A")}


PALETTES.update({
    "halo":        _preset("#FF5005", "#DBBA95", "#D0BCE1"),
    "pensive":     _preset("#809BD6", "#910AFF", "#AF38FF"),
    "interstella": _preset("#73BFC4", "#FF810A", "#8DA0CE"),
    "universe":    _preset("#5606FF", "#FE8989", "#2A1F5C"),
    "mandarin":    _preset("#FF6A1A", "#C73C00", "#FD4912", base_dark="#0C0A09"),
    "nighty":      _preset("#606080", "#8D7DCA", "#3A3A55"),
})

STYLES = {
    # name: (default palette, description)
    "aurora":        ("violet", "drifting mesh-gradient light, modern SaaS"),
    "synthwave":     ("sunset", "3D perspective grid floor + striped sun, retro-futurism"),
    "isometric":     ("ocean",  "3D isometric cube stack that floats, infra/dev-tools"),
    "orbit":         ("ember",  "3D tilted orbits with revolving planets, platforms/ecosystems"),
    "glass":         ("violet", "frosted-glass card over moving colour blobs"),
    "terminal":      ("mint",   "code window that types the title, CLIs and libraries"),
    "neon":          ("cyber",  "glowing neon outline title, games/creative"),
    "wave":          ("ocean",  "layered animated waves (also a footer)"),
    "blueprint":     ("ocean",  "engineering grid with lines drawing themselves"),
    "constellation": ("ember",  "twinkling particle network, AI/data"),
    "minimal":       ("mono",   "clean type, one accent line drawing in"),
    "bold":          ("ember",  "oversized type with a moving gradient fill"),
    "shader":        ("halo", "grainy flowing 3D colour field (ShaderGradient look)"),
    "spotlight":     ("midnight", "dark landing-page hero: masked grid, light beam, announcement pill, gradient title"),
    "ribbon":        ("violet", "twisting silk ribbon of light strands, 3D depth"),
}


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def title_size(text: str, width: int, height: int, base: float, mono=False) -> int:
    """Estimate a font size that fits ~80% of the width (no text measuring in SVG-as-image)."""
    ch = max(len(text), 1)
    per = 0.62 if mono else 0.56
    fit = (width * 0.80) / (ch * per)
    return int(max(18, min(base, fit, height * 0.32)))


class Ctx:
    def __init__(self, a, theme):
        self.kind, self.style, self.theme = a.kind, a.style, theme
        self.W, self.H = a.width, a.height
        pal = PALETTES[a.palette or STYLES[a.style][0]][theme]
        self.c = dict(pal)
        if a.accent:
            self.c["a1"] = a.accent
        self.title, self.sub, self.tag = a.title or "", a.subtitle or "", a.tag or ""
        self.logo = getattr(a, "logo_uri", None)
        # With a side logo, keep centred text clear of it.
        self.text_w = self.W - 2 * (self.H * 0.62 + self.H * 0.2) if self.logo and a.kind == "header" and a.style != "spotlight" else self.W
        self.animate = not a.static
        self.rng = random.Random(f"{a.style}{a.title}{theme}")
        self.defs, self.css, self.body = [], [], []


# ---------------------------------------------------------------- shared pieces
def bg_rect(x: Ctx, radius=0):
    c = x.c
    x.defs.append(f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["bg0"]}"/><stop offset="1" stop-color="{c["bg1"]}"/></linearGradient>')
    x.body.append(f'<rect width="{x.W}" height="{x.H}" rx="{radius}" fill="url(#bg)"/>')


def text_block(x: Ctx, cx=None, anchor="middle", y_center=None, mono=False, size=None, glow=False, fill=None):
    """Tag + title + subtitle, vertically centred around y_center."""
    W, H, c = x.W, x.H, x.c
    cx = W / 2 if cx is None else cx
    y_center = H / 2 if y_center is None else y_center
    fam = MONO if mono else SANS
    ts = size or title_size(x.title, x.text_w if anchor == "middle" else W * 0.62, H, 72 if x.kind == "header" else 40, mono)
    ss = max(14, int(ts * 0.34))
    tg = max(11, int(ts * 0.2))
    lines_h = (tg * 1.9 if x.tag else 0) + ts + (ss * 1.7 if x.sub else 0)
    y = y_center - lines_h / 2
    out = []
    if x.tag:
        y += tg
        out.append(f'<text class="tag fade d1" x="{cx}" y="{y:.1f}" text-anchor="{anchor}" font-family="{SANS}" font-size="{tg}" font-weight="700" letter-spacing="{tg * 0.32:.1f}" fill="{c["a1"]}">{esc(x.tag.upper())}</text>')
        y += tg * 0.9
    y += ts * 0.92
    filt = ' filter="url(#glow)"' if glow else ""
    out.append(f'<text class="title fade d2" x="{cx}" y="{y:.1f}" text-anchor="{anchor}" font-family="{fam}" font-size="{ts}" font-weight="800" letter-spacing="{-ts * 0.02:.1f}" fill="{fill or c["fg"]}"{filt}>{esc(x.title)}</text>')
    if x.sub:
        y += ss * 1.7
        out.append(f'<text class="sub fade d3" x="{cx}" y="{y:.1f}" text-anchor="{anchor}" font-family="{SANS}" font-size="{ss}" font-weight="500" fill="{c["muted"]}">{esc(x.sub)}</text>')
    x.bottom = y + ss * 0.35
    x.body.extend(out)
    # Text never animates in: the first frame must be complete (link previews, thumbnails, slow loads).
    if glow:
        x.defs.append('<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    return ts


def soft_blobs(x: Ctx, n=4, blur=60, opacity=0.55, speed=14):
    W, H, c, r = x.W, x.H, x.c, x.rng
    x.defs.append(f'<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{blur}"/></filter>')
    cols = [c["a1"], c["a2"], c["a3"], c["a1"]]
    g = [f'<g filter="url(#blur)" opacity="{opacity}">']
    for i in range(n):
        cx, cy = r.uniform(0.1, 0.9) * W, r.uniform(0.1, 0.9) * H
        rad = r.uniform(0.18, 0.32) * W
        dx, dy = r.uniform(-0.12, 0.12) * W, r.uniform(-0.25, 0.25) * H
        g.append(f'<circle class="blob b{i}" cx="{cx:.0f}" cy="{cy:.0f}" r="{rad:.0f}" fill="{cols[i % 4]}"/>')
        x.css.append(f"@keyframes drift{i}{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate({dx:.0f}px,{dy:.0f}px)}}}}"
                     f".b{i}{{animation:drift{i} {speed + i * 3}s ease-in-out infinite}}")
    g.append("</g>")
    x.body.extend(g)


def logo_mark(x: Ctx, cx: float, cy: float, size: float):
    """The user's logo with a soft accent glow behind it, so dark logos stay visible on dark banners."""
    c, dark = x.c, x.theme == "dark"
    x.defs.append(f'<radialGradient id="lglow"><stop offset="0" stop-color="{c["a1"]}" stop-opacity="{.55 if dark else .22}"/>'
                  f'<stop offset=".55" stop-color="{c["a2"]}" stop-opacity="{.22 if dark else .08}"/><stop offset="1" stop-color="{c["a2"]}" stop-opacity="0"/></radialGradient>')
    x.body.append(f'<circle class="lglow" cx="{cx:.0f}" cy="{cy:.0f}" r="{size * .72:.0f}" fill="url(#lglow)"/>')
    x.css.append("@keyframes lpulse{0%,100%{opacity:1}50%{opacity:.7}}.lglow{animation:lpulse 6s ease-in-out infinite}")
    x.body.append(f'<image href="{x.logo}" x="{cx - size / 2:.0f}" y="{cy - size / 2:.0f}" width="{size:.0f}" height="{size:.0f}" preserveAspectRatio="xMidYMid meet"/>')


# ---------------------------------------------------------------- styles
def scrim(x, rx=0.36, ry=0.40, strength=0.85):
    """Soft radial wash of the background colour behind centred text (keeps 4.5:1 contrast over colour)."""
    c = x.c
    x.defs.append(f'<radialGradient id="scrim"><stop offset="0" stop-color="{c["bg0"]}" stop-opacity="{strength}"/><stop offset=".6" stop-color="{c["bg0"]}" stop-opacity="{strength * .55:.2f}"/><stop offset="1" stop-color="{c["bg0"]}" stop-opacity="0"/></radialGradient>')
    x.body.append(f'<ellipse cx="{x.W / 2}" cy="{x.H / 2}" rx="{x.W * rx:.0f}" ry="{x.H * ry:.0f}" fill="url(#scrim)"/>')


def s_aurora(x):
    bg_rect(x)
    soft_blobs(x, n=4, blur=x.H * 0.22, opacity=0.55)
    scrim(x, strength=0.7 if x.theme == "dark" else 0.8)
    # subtle grain-free noise substitute: thin horizon line
    x.body.append(f'<rect x="0" y="{x.H - 1}" width="{x.W}" height="1" fill="{x.c["fg"]}" opacity=".08"/>')
    text_block(x)


def s_glass(x):
    bg_rect(x)
    soft_blobs(x, n=4, blur=x.H * 0.14, opacity=0.9, speed=10)
    W, H, c = x.W, x.H, x.c
    pw, ph = W * 0.62, H * 0.66
    px, py = (W - pw) / 2, (H - ph) / 2
    glass_fill = x.c["bg0"] if x.theme == "dark" else "#FFFFFF"
    op = 0.62 if x.theme == "dark" else 0.66
    x.defs.append(f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".55"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".05"/><stop offset="1" stop-color="#FFFFFF" stop-opacity=".35"/></linearGradient>')
    x.body.append(f'<rect x="{px:.0f}" y="{py:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="22" fill="{glass_fill}" fill-opacity="{op}" stroke="url(#edge)" stroke-width="1.5"/>')
    # sheen sweep
    x.defs.append(f'<clipPath id="card"><rect x="{px:.0f}" y="{py:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="22"/></clipPath>'
                  '<linearGradient id="sheen" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    x.body.append(f'<g clip-path="url(#card)"><rect class="sheen" x="{px - pw * 0.4:.0f}" y="{py:.0f}" width="{pw * 0.35:.0f}" height="{ph:.0f}" fill="url(#sheen)" transform="skewX(-20)"/></g>')
    x.css.append(f"@keyframes sweep{{0%,60%{{transform:skewX(-20deg) translateX(0)}}100%{{transform:skewX(-20deg) translateX({pw * 1.9:.0f}px)}}}}.sheen{{animation:sweep 6s ease-in-out infinite}}")
    text_block(x)


def s_synthwave(x):
    W, H, c = x.W, x.H, x.c
    hz = H * 0.64  # horizon
    x.defs.append(f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["bg0"]}"/><stop offset="1" stop-color="{c["bg1"]}"/></linearGradient>'
                  f'<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["a2"]}"/><stop offset="1" stop-color="{c["a3"]}"/></linearGradient>'
                  f'<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["bg1"]}"/><stop offset="1" stop-color="{c["bg0"]}"/></linearGradient>'
                  f'<clipPath id="ground"><rect x="0" y="{hz:.1f}" width="{W}" height="{H - hz:.1f}"/></clipPath>')
    x.body.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    # striped sun behind the horizon
    sr = H * 0.20
    stripes = "".join(f'<rect x="{W / 2 - sr:.0f}" y="{hz - sr * k / 6:.1f}" width="{2 * sr:.0f}" height="{1.2 + k * 0.9:.1f}" fill="{c["bg1"]}"/>' for k in range(1, 6))
    x.defs.append(f'<clipPath id="sunclip"><circle cx="{W / 2}" cy="{hz:.1f}" r="{sr:.1f}"/></clipPath>')
    x.body.append(f'<g clip-path="url(#sunclip)" opacity=".95"><rect x="{W / 2 - sr:.0f}" y="{hz - sr:.0f}" width="{2 * sr:.0f}" height="{sr:.0f}" fill="url(#sun)"/>{stripes}</g>')
    x.body.append(f'<rect x="0" y="{hz:.1f}" width="{W}" height="{H - hz:.1f}" fill="url(#floor)"/>')
    # converging verticals (vanishing point at horizon centre)
    vlines = []
    for i in range(-14, 15):
        xb = W / 2 + i * W / 14
        vlines.append(f'<line x1="{W / 2 + i * 6:.1f}" y1="{hz:.1f}" x2="{xb:.1f}" y2="{H}" />')
    x.body.append(f'<g clip-path="url(#ground)" stroke="{c["a1"]}" stroke-width="1.2" opacity=".55">{"".join(vlines)}</g>')
    # horizontal lines rushing toward the viewer (ease-in = perspective)
    n, T = 8, 4.0
    h = [f'<g clip-path="url(#ground)" stroke="{c["a1"]}" stroke-width="1.4" opacity=".75">']
    for i in range(n):
        h.append(f'<line class="hl" style="animation-delay:{-i * T / n:.2f}s" x1="0" y1="{hz:.1f}" x2="{W}" y2="{hz:.1f}"/>')
    h.append("</g>")
    x.body.extend(h)
    x.css.append(f"@keyframes rush{{from{{transform:translateY(0);opacity:.15}}to{{transform:translateY({H - hz:.0f}px);opacity:1}}}}"
                 f".hl{{animation:rush {T}s cubic-bezier(.55,0,1,.45) infinite}}")
    x.body.append(f'<rect x="0" y="{hz - 1:.1f}" width="{W}" height="2" fill="{c["a2"]}" opacity=".8"/>')
    text_block(x, y_center=H * 0.25, glow=x.theme == "dark", size=title_size(x.title, W, H, int(H * 0.16)))


def iso_cube(cx, cy, s, top, left, right, cls=""):
    """Isometric cube centred on (cx,cy) top-vertex layout, edge s."""
    dx, dy = s * math.cos(math.radians(30)), s * math.sin(math.radians(30))
    t = f"{cx},{cy - dy} {cx + dx},{cy} {cx},{cy + dy} {cx - dx},{cy}"
    l = f"{cx - dx},{cy} {cx},{cy + dy} {cx},{cy + dy + s} {cx - dx},{cy + s}"
    r = f"{cx + dx},{cy} {cx},{cy + dy} {cx},{cy + dy + s} {cx + dx},{cy + s}"
    return (f'<g class="{cls}"><polygon points="{l}" fill="{left}"/><polygon points="{r}" fill="{right}"/>'
            f'<polygon points="{t}" fill="{top}"/></g>')


def shade(hex_, f):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if f >= 0:
        r, g, b = (int(v + (255 - v) * f) for v in (r, g, b))
    else:
        r, g, b = (int(v * (1 + f)) for v in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def s_isometric(x):
    bg_rect(x)
    W, H, c = x.W, x.H, x.c
    # faint isometric grid
    grid = []
    step = 28
    for k in range(-40, 60):
        grid.append(f'<line x1="{k * step * 1.732:.0f}" y1="0" x2="{k * step * 1.732 + H * 1.732:.0f}" y2="{H}"/>')
        grid.append(f'<line x1="{k * step * 1.732:.0f}" y1="0" x2="{k * step * 1.732 - H * 1.732:.0f}" y2="{H}"/>')
    x.body.append(f'<g stroke="{c["fg"]}" stroke-width=".6" opacity=".06">{"".join(grid)}</g>')
    s = H * 0.15
    base_x, base_y = W * 0.78, H * 0.40
    layout = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 0, 2)]
    cols = [c["a1"], c["a3"], c["a2"]]
    dx, dy = s * math.cos(math.radians(30)), s * math.sin(math.radians(30))
    cubes = []
    for i, (gx, gy, gz) in enumerate(sorted(layout, key=lambda p: (p[2], p[0] + p[1]))):
        cx = base_x + (gx - gy) * dx
        cy = base_y + (gx + gy) * dy - gz * s
        col = cols[(gx + gy + gz) % 3]
        cubes.append(iso_cube(cx, cy, s, shade(col, .25), shade(col, -.15), shade(col, -.38), f"cube c{i}"))
        x.css.append(f".c{i}{{animation:float 5s ease-in-out {-i * 0.45:.2f}s infinite}}")
    x.css.append("@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}")
    # contact shadow
    x.body.append(f'<ellipse cx="{base_x:.0f}" cy="{base_y + 2.6 * s:.0f}" rx="{2.3 * s:.0f}" ry="{0.55 * s:.0f}" fill="#000" opacity="{.35 if x.theme == "dark" else .12}"/>')
    x.body.extend(cubes)
    text_block(x, cx=W * 0.07, anchor="start")


def s_orbit(x):
    bg_rect(x)
    W, H, c = x.W, x.H, x.c
    cx, cy = W * 0.80, H * 0.52
    x.defs.append(f'<radialGradient id="core"><stop offset="0" stop-color="{shade(c["a1"], .45)}"/><stop offset="1" stop-color="{c["a1"]}"/></radialGradient>')
    rings = [(H * 0.20, 0.30, -18, 7, c["a2"]), (H * 0.33, 0.30, -18, 11, c["a3"]), (H * 0.46, 0.30, -18, 16, c["a1"])]
    back, front = [], []
    for i, (rx, k, rot, dur, col) in enumerate(rings):
        ry = rx * k
        path = f"M {cx - rx:.1f} {cy:.1f} a {rx:.1f} {ry:.1f} 0 1 0 {2 * rx:.1f} 0 a {rx:.1f} {ry:.1f} 0 1 0 {-2 * rx:.1f} 0"
        x.defs.append(f'<path id="o{i}" d="{path}"/>')
        back.append(f'<use href="#o{i}" fill="none" stroke="{c["fg"]}" stroke-opacity=".18" stroke-width="1.2" transform="rotate({rot} {cx} {cy})"/>')
        pr = 5 + i * 1.6
        anim = (f'<animateMotion dur="{dur}s" repeatCount="indefinite" rotate="0"><mpath href="#o{i}"/></animateMotion>'
                f'<animate attributeName="r" values="{pr * .7:.1f};{pr * 1.25:.1f};{pr * .7:.1f}" keyTimes="0;.5;1" dur="{dur}s" repeatCount="indefinite"/>') if x.animate else ""
        start = "" if x.animate else f' cx="{cx - rx:.1f}" cy="{cy:.1f}"'
        front.append(f'<g transform="rotate({rot} {cx} {cy})"><circle r="{pr:.1f}"{start} fill="{col}">{anim}</circle></g>')
    x.body.extend(back)
    x.body.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{H * 0.09:.0f}" fill="url(#core)"/>')
    x.body.append(f'<circle class="pulse" cx="{cx:.0f}" cy="{cy:.0f}" r="{H * 0.09:.0f}" fill="none" stroke="{c["a1"]}" stroke-width="2"/>')
    x.css.append("@keyframes pulse{from{transform:scale(1);opacity:.6}to{transform:scale(2.2);opacity:0}}"
                 ".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 3s ease-out infinite}")
    x.body.extend(front)
    text_block(x, cx=W * 0.07, anchor="start")


def s_terminal(x):
    bg_rect(x)
    W, H, c = x.W, x.H, x.c
    pw, ph = W * 0.70, H * 0.70
    px, py = (W - pw) / 2, (H - ph) / 2 + 4
    win = shade(c["bg0"], .06 if x.theme == "dark" else -.03)
    x.body.append(f'<rect x="{px + 6:.0f}" y="{py + 10:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="14" fill="#000" opacity="{.35 if x.theme == "dark" else .10}"/>'
                  f'<rect x="{px:.0f}" y="{py:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="14" fill="{win}" stroke="{c["fg"]}" stroke-opacity=".12"/>'
                  f'<circle cx="{px + 22:.0f}" cy="{py + 20:.0f}" r="6" fill="#FF5F57"/><circle cx="{px + 42:.0f}" cy="{py + 20:.0f}" r="6" fill="#FEBC2E"/><circle cx="{px + 62:.0f}" cy="{py + 20:.0f}" r="6" fill="#28C840"/>')
    ts = title_size("$ " + x.title, pw * 1.05, H, 54, mono=True)
    ty = py + ph * 0.50
    char_w = ts * 0.6
    full = (len(x.title) + 2) * char_w
    tx = px + 30
    # frame 0 shows the whole command; every 7 s it is erased and typed again
    x.defs.append(f'<clipPath id="type"><rect x="{tx:.0f}" y="{ty - ts:.0f}" width="{full:.0f}" height="{ts * 1.4:.0f}">'
                  + (f'<animate attributeName="width" values="{full:.0f};{full:.0f};0;{full:.0f};{full:.0f}" keyTimes="0;.55;.6;.85;1" dur="7s" repeatCount="indefinite"/>' if x.animate else "")
                  + "</rect></clipPath>")
    x.body.append(f'<g clip-path="url(#type)"><text x="{tx:.0f}" y="{ty:.0f}" font-family="{MONO}" font-size="{ts}" font-weight="700" fill="{c["fg"]}"><tspan fill="{c["a1"]}">$ </tspan>{esc(x.title)}</text></g>')
    x.body.append(f'<rect class="cursor" x="{tx + full + 4:.0f}" y="{ty - ts * 0.8:.0f}" width="{ts * 0.5:.0f}" height="{ts * 0.95:.0f}" fill="{c["a1"]}"/>')
    x.css.append("@keyframes blink{50%{opacity:0}}.cursor{animation:blink 1s steps(1) infinite}")
    if x.sub:
        x.body.append(f'<text x="{tx:.0f}" y="{ty + ts * 1.15:.0f}" font-family="{MONO}" font-size="{max(14, int(ts * .36))}" fill="{c["muted"]}"><tspan fill="{c["a2"]}">→ </tspan>{esc(x.sub)}</text>')
    if x.tag:
        x.body.append(f'<text x="{px + pw / 2:.0f}" y="{py + 25:.0f}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{c["muted"]}">{esc(x.tag.lower())}</text>')


def s_neon(x):
    bg_rect(x)
    W, H, c = x.W, x.H, x.c
    x.body.append(f'<g stroke="{c["a2"]}" stroke-width="1" opacity=".18">' + "".join(
        f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(0, H, 6)) + "</g>")  # scanlines
    ts = title_size(x.title, W, H, 84)
    x.defs.append('<filter id="neon" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.5" result="b1"/><feGaussianBlur stdDeviation="9" result="b2"/>'
                  '<feMerge><feMergeNode in="b2"/><feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    y = H * (0.52 if x.sub else 0.58)
    x.body.append(f'<text class="flicker" x="{W / 2}" y="{y:.0f}" text-anchor="middle" font-family="{SANS}" font-size="{ts}" font-weight="800" fill="none" stroke="{c["a1"]}" stroke-width="2.4" filter="url(#neon)">{esc(x.title)}</text>')
    if x.sub:
        x.body.append(f'<text x="{W / 2}" y="{y + ts * 0.62:.0f}" text-anchor="middle" font-family="{SANS}" font-size="{max(14, int(ts * .3))}" font-weight="600" letter-spacing="2" fill="{c["a2"]}" filter="url(#neon)">{esc(x.sub)}</text>')
    if x.tag:
        x.body.append(f'<text x="{W / 2}" y="{y - ts * 0.95:.0f}" text-anchor="middle" font-family="{MONO}" font-size="14" letter-spacing="6" fill="{c["a3"]}">{esc(x.tag.upper())}</text>')
    x.css.append("@keyframes flick{0%,19%,21%,23%,80%,100%{opacity:1}20%,22%{opacity:.35}81%{opacity:.6}}.flicker{animation:flick 5s linear infinite}")
    if x.theme == "light":  # neon reads poorly on light: fill the title too
        x.body[-1 if not x.sub else -2] = x.body[-1 if not x.sub else -2]


def wave_path(W, H, amp, base, phase, k=2):
    pts = []
    for i in range(0, 41):
        X = W * 2 * i / 40
        Y = base + amp * math.sin(phase + k * 2 * math.pi * i / 40)
        pts.append(f"{X:.1f},{Y:.1f}")
    return f"M0,{H} L" + " L".join(pts) + f" L{W * 2},{H} Z"


def s_wave(x, flip=False):
    bg_rect(x)
    W, H, c = x.W, x.H, x.c
    layers = [(c["a3"], .35, H * .08, H * .70, 0, 16), (c["a2"], .45, H * .07, H * .78, 1.4, 11), (c["a1"], .85, H * .05, H * .87, 2.6, 8)]
    if x.kind == "footer":
        layers = [(col, op, amp * .7, H * (.22 + i * .10), ph, d) for i, (col, op, amp, _, ph, d) in enumerate(layers)]
    g = [f'<g transform="{"translate(0," + str(H) + ") scale(1,-1)" if flip else ""}">']
    for i, (col, op, amp, base, ph, dur) in enumerate(layers):
        # 2 periods wide so a translateX of -W loops seamlessly
        g.append(f'<path class="w{i}" d="{wave_path(W, H, amp, base, ph)}" fill="{col}" opacity="{op}"/>')
        x.css.append(f"@keyframes slide{i}{{from{{transform:translateX(0)}}to{{transform:translateX(-{W}px)}}}}.w{i}{{animation:slide{i} {dur}s linear infinite}}")
    g.append("</g>")
    x.body.extend(g)
    if x.kind == "footer":
        if x.title:
            ts = title_size(x.title, W, H, 26)
            x.body.append(f'<text x="{W / 2}" y="{H * (0.84 if flip else 0.30):.0f}" text-anchor="middle" font-family="{SANS}" font-size="{ts}" font-weight="700" fill="{c["fg"]}">{esc(x.title)}</text>')
    else:
        text_block(x, y_center=H * 0.33)


def s_blueprint(x):
    W, H, c = x.W, x.H, x.c
    bg = "#0B2A4A" if x.theme == "dark" else "#EEF6FF"
    line = "#7FB8FF" if x.theme == "dark" else "#2F6FD6"
    x.body.append(f'<rect width="{W}" height="{H}" fill="{bg}"/>')
    grid = "".join(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{H}"/>' for gx in range(0, W + 1, 24)) + "".join(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}"/>' for gy in range(0, H + 1, 24))
    x.body.append(f'<g stroke="{line}" stroke-width=".5" opacity=".22">{grid}</g>')
    major = "".join(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{H}"/>' for gx in range(0, W + 1, 120)) + "".join(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}"/>' for gy in range(0, H + 1, 120))
    x.body.append(f'<g stroke="{line}" stroke-width="1" opacity=".3">{major}</g>')
    # technical drawing: circle + dimension lines that draw themselves
    cx, cy, r = W * 0.83, H * 0.5, H * 0.26
    shapes = [f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}"/>', f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r * .45:.0f}"/>',
              f'<line x1="{cx - r * 1.4:.0f}" y1="{cy:.0f}" x2="{cx + r * 1.4:.0f}" y2="{cy:.0f}"/>', f'<line x1="{cx:.0f}" y1="{cy - r * 1.4:.0f}" x2="{cx:.0f}" y2="{cy + r * 1.4:.0f}"/>',
              f'<rect x="{cx - r * 2.6:.0f}" y="{cy - r * .5:.0f}" width="{r:.0f}" height="{r:.0f}"/>',
              f'<path d="M{cx - r * 1.6:.0f} {cy:.0f} L{cx - r:.0f} {cy:.0f}"/>']
    x.body.append(f'<g class="draw" fill="none" stroke="{line}" stroke-width="1.6">{"".join(shapes)}</g>')
    x.css.append("@keyframes draw{0%,55%{stroke-dashoffset:0}75%{stroke-dashoffset:900}100%{stroke-dashoffset:0}}.draw *{stroke-dasharray:900;animation:draw 9s ease-in-out infinite}")
    x.c["fg"] = "#FFFFFF" if x.theme == "dark" else "#0B2A4A"
    x.c["muted"] = "#B8D6FF" if x.theme == "dark" else "#2F4E75"
    x.c["a1"] = line
    text_block(x, cx=W * 0.07, anchor="start", mono=True)
    x.body.append(f'<text x="{W - 16}" y="{H - 12}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{line}" opacity=".8">REV A · SCALE 1:1</text>')


def s_constellation(x):
    bg_rect(x)
    W, H, c, r = x.W, x.H, x.c, x.rng
    pts = [(r.uniform(0, W), r.uniform(0, H)) for _ in range(46)]
    edges = []
    for i, (ax, ay) in enumerate(pts):
        for j in range(i + 1, len(pts)):
            bx, by = pts[j]
            d = math.hypot(ax - bx, ay - by)
            if d < W * 0.11:
                edges.append(f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{bx:.0f}" y2="{by:.0f}" stroke-opacity="{max(.05, .35 - d / (W * .4)):.2f}"/>')
    x.body.append(f'<g stroke="{c["a1"]}" stroke-width="1">{"".join(edges)}</g>')
    dots = []
    for i, (px, py) in enumerate(pts):
        rr = r.uniform(1.2, 2.8)
        dots.append(f'<circle class="tw t{i % 5}" cx="{px:.0f}" cy="{py:.0f}" r="{rr:.1f}" fill="{[c["a1"], c["a2"], c["a3"], c["fg"], c["a1"]][i % 5]}"/>')
    x.body.append("".join(dots))
    x.css.append("@keyframes tw{0%,100%{opacity:.25}50%{opacity:1}}" + "".join(f".t{k}{{animation:tw {2.2 + k * .7:.1f}s ease-in-out {k * .4:.1f}s infinite}}" for k in range(5)))
    # readability scrim behind text
    x.defs.append(f'<radialGradient id="scrim"><stop offset="0" stop-color="{c["bg0"]}" stop-opacity=".92"/><stop offset="1" stop-color="{c["bg0"]}" stop-opacity="0"/></radialGradient>')
    x.body.append(f'<ellipse cx="{W / 2}" cy="{H / 2}" rx="{W * .38:.0f}" ry="{H * .42:.0f}" fill="url(#scrim)"/>')
    text_block(x)



def line_sweep(x, lx, ly, lw, lh, color, ident):
    """Static accent line (always visible) with a soft highlight travelling along it."""
    x.defs.append(f'<clipPath id="{ident}"><rect x="{lx:.0f}" y="{ly:.0f}" width="{lw:.0f}" height="{lh}" rx="{lh / 2}"/></clipPath>'
                  f'<linearGradient id="{ident}g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    x.body.append(f'<rect x="{lx:.0f}" y="{ly:.0f}" width="{lw:.0f}" height="{lh}" rx="{lh / 2}" fill="{color}"/>'
                  f'<g clip-path="url(#{ident})"><rect class="{ident}s" x="{lx - lw * .3:.0f}" y="{ly:.0f}" width="{lw * .3:.0f}" height="{lh}" fill="url(#{ident}g)" opacity=".6"/></g>')
    x.css.append(f"@keyframes {ident}k{{0%{{transform:translateX(0)}}70%,100%{{transform:translateX({lw * 1.3:.0f}px)}}}}.{ident}s{{animation:{ident}k 4s ease-in-out infinite}}")

def s_minimal(x):
    W, H, c = x.W, x.H, x.c
    x.body.append(f'<rect width="{W}" height="{H}" fill="{c["bg0"]}"/>')
    ts = text_block(x, y_center=H * 0.45)
    lw = min(W * 0.18, 220)
    line_sweep(x, W / 2 - lw / 2, getattr(x, "bottom", H * 0.45 + ts) + 18, lw, 3, c["a1"] if c["a1"] != c["fg"] else c["a2"], "ml")


def s_bold(x):
    W, H, c = x.W, x.H, x.c
    x.body.append(f'<rect width="{W}" height="{H}" fill="{c["bg0"]}"/>')
    sweep = (f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;{W} 0;0 0" dur="12s" repeatCount="indefinite"/>'
             if x.animate else "")
    x.defs.append(f'<linearGradient id="ink" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse" spreadMethod="reflect">'
                  f'<stop offset="0" stop-color="{c["a1"]}"/><stop offset=".5" stop-color="{c["a2"]}"/><stop offset="1" stop-color="{c["a3"]}"/>{sweep}</linearGradient>')
    ts = int(min(title_size(x.title, W, H, 150) * 1.15, H * 0.42))
    text_block(x, size=ts, fill="url(#ink)")


def grain(x, strength=0.14, freq=0.85):
    """Film grain overlay (feTurbulence). Static: cheap to render, gives gradients the 'shader' texture."""
    x.defs.append(f'<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="2" stitchTiles="stitch"/>'
                  f'<feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="table" tableValues="0 {strength}"/></feComponentTransfer></filter>')
    x.body.append(f'<rect width="{x.W}" height="{x.H}" filter="url(#grain)"/>')


def s_shader(x):
    """ShaderGradient look: large colour masses warped by low-frequency noise, heavy blur, film grain."""
    W, H, c = x.W, x.H, x.c
    dark = x.theme == "dark"
    x.body.append(f'<rect width="{W}" height="{H}" fill="{c["bg0"]}"/>')
    x.defs.append('<filter id="warp" x="-30%" y="-80%" width="160%" height="260%">'
                  '<feTurbulence type="fractalNoise" baseFrequency="0.0028 0.0075" numOctaves="2" seed="11" result="n"/>'
                  '<feDisplacementMap in="SourceGraphic" in2="n" scale="170" xChannelSelector="R" yChannelSelector="G" result="d"/>'
                  f'<feGaussianBlur in="d" stdDeviation="{H * 0.11:.0f}"/></filter>')
    # long diagonal "bands" read as a 3D surface once warped and blurred
    bands = [(0.22, 0.78, 0.46, 0.34, -12, c["a1"], "sa"), (0.62, 0.30, 0.50, 0.36, -8, c["a3"], "sb"),
             (0.88, 0.82, 0.30, 0.30, -16, c["a2"], "sa"), (0.42, 0.12, 0.26, 0.16, -6, shade(c["a2"], .45), "sb")]
    g = ['<g filter="url(#warp)">']
    for cx, cy, rx, ry, rot, col, cls in bands:
        g.append(f'<ellipse class="{cls}" cx="{W * cx:.0f}" cy="{H * cy:.0f}" rx="{W * rx:.0f}" ry="{H * ry:.0f}" fill="{col}" transform="rotate({rot} {W * cx:.0f} {H * cy:.0f})"/>')
    g.append("</g>")
    x.body.extend(g)
    x.css.append(f"@keyframes sa{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate({W * .09:.0f}px,{-H * .10:.0f}px)}}}}"
                 f"@keyframes sb{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate({-W * .11:.0f}px,{H * .12:.0f}px)}}}}"
                 ".sa{animation:sa 17s ease-in-out infinite}.sb{animation:sb 21s ease-in-out infinite}")
    # vignette keeps the title area calm and readable
    x.defs.append(f'<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".35" stop-color="{c["bg0"]}" stop-opacity="{.30 if dark else .10}"/><stop offset="1" stop-color="{c["bg0"]}" stop-opacity="{.75 if dark else .45}"/></radialGradient>')
    x.body.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    scrim(x, rx=0.30, ry=0.34, strength=0.55 if dark else 0.75)
    grain(x, 0.16 if dark else 0.10)
    if dark:
        x.c = dict(c, fg="#FFFFFF", muted="#E6E6EE")
    text_block(x)


def s_spotlight(x):
    """Landing-page hero (supahero-style): grid fading out radially, light beam from the top,
    announcement pill above a gradient title."""
    W, H, c = x.W, x.H, x.c
    dark = x.theme == "dark"
    line = c.get("line", c["fg"])
    x.body.append(f'<rect width="{W}" height="{H}" fill="{c["bg0"]}"/>')
    cell = 40
    x.defs.append(f'<pattern id="grid" width="{cell}" height="{cell}" patternUnits="userSpaceOnUse"><path d="M {cell} 0 L 0 0 0 {cell}" fill="none" stroke="{line}" stroke-opacity="{.09 if dark else .08}" stroke-width="1"/></pattern>'
                  f'<radialGradient id="fade" cx=".5" cy=".35" r=".62"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
                  f'<mask id="gm"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>')
    x.body.append(f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gm)"/>')
    # beam: soft accent glow + thin cone of light from the top centre
    x.defs.append(f'<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{c["a1"]}" stop-opacity="{.55 if dark else .30}"/><stop offset=".55" stop-color="{c["a2"]}" stop-opacity="{.14 if dark else .08}"/><stop offset="1" stop-color="{c["a1"]}" stop-opacity="0"/></radialGradient>'
                  f'<linearGradient id="cone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["fg"]}" stop-opacity="{.20 if dark else .10}"/><stop offset="1" stop-color="{c["fg"]}" stop-opacity="0"/></linearGradient>'
                  f'<filter id="soft"><feGaussianBlur stdDeviation="14"/></filter>')
    x.body.append(f'<ellipse class="beam" cx="{W / 2}" cy="0" rx="{W * .42:.0f}" ry="{H * .95:.0f}" fill="url(#glow)"/>')
    x.body.append(f'<polygon points="{W / 2 - 40},0 {W / 2 + 40},0 {W / 2 + W * .20:.0f},{H} {W / 2 - W * .20:.0f},{H}" fill="url(#cone)" filter="url(#soft)"/>')
    x.body.append(f'<rect x="{W * .2:.0f}" y="0" width="{W * .6:.0f}" height="1" fill="{c["a1"]}" opacity=".7"/>')
    x.css.append("@keyframes breathe{0%,100%{opacity:1}50%{opacity:.72}}.beam{animation:breathe 7s ease-in-out infinite}")
    # announcement pill (the tag) with a light sweeping across its border
    ts = title_size(x.title, W, H, 72)
    ss = max(17, int(ts * .32))
    lsize = H * .40 if x.logo else 0
    top = (lsize + 14) if x.logo else (40 + 20 if x.tag else 0)
    block = top + ts + (ss * 1.8 if x.sub else 0)
    y = H / 2 - block / 2 + 6
    if x.logo:
        logo_mark(x, W / 2, y + lsize / 2, lsize)
        y += lsize + 14
    elif x.tag:
        label = x.tag
        pw = len(label) * 9.6 + 66
        px = W / 2 - pw / 2
        surf = c.get("surface", c["bg1"])
        x.defs.append(f'<linearGradient id="pillb" x1="0" x2="1"><stop offset="0" stop-color="{line}" stop-opacity=".14"/><stop offset=".5" stop-color="{c["a1"]}" stop-opacity=".9"/><stop offset="1" stop-color="{line}" stop-opacity=".14"/>'
                      + (f'<animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0" dur="4s" repeatCount="indefinite"/>' if x.animate else "")
                      + "</linearGradient>")
        x.body.append(f'<rect x="{px:.0f}" y="{y:.0f}" width="{pw:.0f}" height="40" rx="20" fill="{surf}" fill-opacity="{.85 if dark else .95}" stroke="url(#pillb)" stroke-width="1"/>'
                      f'<circle cx="{px + 21:.0f}" cy="{y + 20:.0f}" r="4.5" fill="{c["a1"]}"/>'
                      f'<text x="{px + 34:.0f}" y="{y + 26:.0f}" font-family="{SANS}" font-size="16.5" font-weight="600" fill="{c["fg"]}">{esc(label)}</text>'
                      f'<text x="{px + pw - 26:.0f}" y="{y + 26:.0f}" font-family="{SANS}" font-size="16.5" fill="{c["muted"]}">→</text>')
        y += 40 + 20
    x.defs.append(f'<linearGradient id="tgrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["fg"]}"/><stop offset="1" stop-color="{c["fg"]}" stop-opacity="{.80 if dark else .82}"/></linearGradient>')
    y += ts * 0.86
    x.body.append(f'<text x="{W / 2}" y="{y:.0f}" text-anchor="middle" font-family="{SANS}" font-size="{ts}" font-weight="700" letter-spacing="{-ts * .035:.1f}" fill="url(#tgrad)">{esc(x.title)}</text>')
    if x.sub:
        y += ss * 1.8
        x.body.append(f'<text x="{W / 2}" y="{y:.0f}" text-anchor="middle" font-family="{SANS}" font-size="{ss}" fill="{c["muted"]}">{esc(x.sub)}</text>')
    x.body.append(f'<rect x="0" y="{H - 1}" width="{W}" height="1" fill="{line}" opacity="{.08 if dark else .10}"/>')


def s_ribbon(x):
    """Silk ribbon: many strands following a twisting sine band; per-strand phase gives 3D depth.
    SMIL morphs each strand between two phases so the ribbon flows."""
    W, H, c = x.W, x.H, x.c
    bg_rect(x)
    n = 20
    x.defs.append(f'<linearGradient id="silk" x1="0" x2="1"><stop offset="0" stop-color="{c["a3"]}" stop-opacity="0"/><stop offset=".25" stop-color="{c["a3"]}"/>'
                  f'<stop offset=".6" stop-color="{c["a1"]}"/><stop offset="1" stop-color="{c["a2"]}" stop-opacity=".2"/></linearGradient>')

    def strand(i, phase):
        t = i / (n - 1)
        pts = []
        for k in range(0, 19):
            u = k / 18
            X = -40 + (W + 80) * u
            twist = math.cos(math.pi * (u * 1.6 + phase))           # ribbon edge-on where cos≈0
            Y = H * (0.60 + 0.20 * math.sin(2 * math.pi * (u * .9 + phase * .5))) + (t - .5) * H * .42 * twist
            pts.append((X, Y))
        d = f"M{pts[0][0]:.0f},{pts[0][1]:.0f}"
        for k in range(1, len(pts)):
            mx = (pts[k - 1][0] + pts[k][0]) / 2
            my = (pts[k - 1][1] + pts[k][1]) / 2
            d += f" Q{pts[k - 1][0]:.0f},{pts[k - 1][1]:.0f} {mx:.0f},{my:.0f}"
        d += f" T{pts[-1][0]:.0f},{pts[-1][1]:.0f}"
        return d

    g = ['<g fill="none" stroke="url(#silk)" stroke-linecap="round">']
    for i in range(n):
        d0, d1 = strand(i, 0.0), strand(i, 0.55)
        op = 0.25 + 0.75 * math.sin(math.pi * i / (n - 1))          # centre strands brightest
        anim = f'<animate attributeName="d" values="{d0};{d1};{d0}" dur="14s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/>' if x.animate else ""
        g.append(f'<path d="{d0}" stroke-width="{1.1 + op * .6:.2f}" stroke-opacity="{op:.2f}">{anim}</path>')
    g.append("</g>")
    x.body.extend(g)
    scrim(x, rx=0.34, ry=0.30, strength=0.8 if x.theme == "dark" else 0.85)
    text_block(x, y_center=H * 0.42)


# ---------------------------------------------------------------- CTA buttons (Call-to-Inspiration patterns)
def button_svg(a, theme) -> str:
    """Pill CTA button. Each button is its own image wrapped in <a> in the README, so it is genuinely clickable."""
    pal = PALETTES[a.palette or "midnight"][theme]
    c = dict(pal)
    if a.accent:
        c["a1"] = a.accent
    label = a.title or "Get started"
    arrow = " →" if a.variant == "primary" else ""
    fs = 15
    w = int(len(label + arrow) * fs * 0.58 + 44)
    h = 44
    dark = theme == "dark"
    if a.variant == "primary":
        bg, fg, stroke = c["a1"], ("#0B0B0F" if _lum(c["a1"]) > 0.45 else "#FFFFFF"), "none"
    else:
        bg, fg, stroke = c.get("surface", c["bg1"]), c["fg"], c.get("line", c["fg"])
    sheen = ""
    css = ""
    if a.variant == "primary" and not a.static:
        sheen = (f'<clipPath id="bc"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{(h - 2) / 2}"/></clipPath>'
                 f'<linearGradient id="bs" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
        css = (f"@keyframes bsw{{0%,70%{{transform:translateX(0)}}100%{{transform:translateX({w * 1.6:.0f}px)}}}}.bsw{{animation:bsw 5s ease-in-out infinite}}"
               "@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    body = (f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{(h - 2) / 2}" fill="{bg}"'
            + (f' stroke="{stroke}" stroke-opacity="{.22 if dark else .18}"' if stroke != "none" else "") + "/>")
    if sheen:
        body += f'<g clip-path="url(#bc)"><rect class="bsw" x="{-w * .5:.0f}" y="0" width="{w * .4:.0f}" height="{h}" fill="url(#bs)" transform="skewX(-20)"/></g>'
    body += (f'<text x="{w / 2}" y="{h / 2 + fs * .36:.1f}" text-anchor="middle" font-family="{SANS}" font-size="{fs}" font-weight="600" fill="{fg}">'
             f'{esc(label)}' + (f'<tspan dx="4">→</tspan>' if arrow else "") + "</text>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'<style>{css}</style><defs>{sheen}</defs>{body}</svg>\n')


def _lum(hex_):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


DRAW = {"aurora": s_aurora, "glass": s_glass, "synthwave": s_synthwave, "isometric": s_isometric, "orbit": s_orbit,
        "terminal": s_terminal, "neon": s_neon, "wave": s_wave, "blueprint": s_blueprint, "constellation": s_constellation,
        "minimal": s_minimal, "bold": s_bold,
        "shader": s_shader, "spotlight": s_spotlight, "ribbon": s_ribbon}


# ---------------------------------------------------------------- footer + divider
def footer(x):
    W, H, c = x.W, x.H, x.c
    if x.style == "wave":
        return s_wave(x, flip=True)
    x.body.append(f'<rect width="{W}" height="{H}" fill="{c["bg0"]}"/>')
    x.defs.append(f'<linearGradient id="rule" x1="0" x2="1"><stop offset="0" stop-color="{c["a1"]}" stop-opacity="0"/><stop offset=".5" stop-color="{c["a1"]}"/><stop offset="1" stop-color="{c["a2"]}" stop-opacity="0"/></linearGradient>')
    line_sweep(x, W * .1, H * .32, W * .8, 2, "url(#rule)", "fl")
    if x.title:
        x.body.append(f'<text x="{W / 2}" y="{H * .62:.0f}" text-anchor="middle" font-family="{SANS}" font-size="{title_size(x.title, W, H, 24)}" font-weight="700" fill="{c["fg"]}">{esc(x.title)}</text>')
    if x.sub:
        x.body.append(f'<text x="{W / 2}" y="{H * .82:.0f}" text-anchor="middle" font-family="{SANS}" font-size="14" fill="{c["muted"]}">{esc(x.sub)}</text>')


def divider(x):
    W, H, c = x.W, x.H, x.c
    x.defs.append(f'<linearGradient id="d" x1="0" x2="1"><stop offset="0" stop-color="{c["a1"]}" stop-opacity="0"/><stop offset=".3" stop-color="{c["a1"]}"/><stop offset=".7" stop-color="{c["a2"]}"/><stop offset="1" stop-color="{c["a3"]}" stop-opacity="0"/></linearGradient>')
    x.body.append(f'<rect x="0" y="{H / 2 - 1}" width="{W}" height="2" rx="1" fill="url(#d)"/>')
    x.body.append(f'<circle class="dot" cx="0" cy="{H / 2}" r="3.5" fill="{c["a1"]}"/>')
    x.css.append(f"@keyframes run{{from{{transform:translateX(0)}}to{{transform:translateX({W}px)}}}}.dot{{animation:run 6s cubic-bezier(.5,0,.5,1) infinite alternate}}")


# ---------------------------------------------------------------- assemble
def render(a, theme) -> str:
    x = Ctx(a, theme)
    if a.kind == "header":
        DRAW[a.style](x)
        if x.logo and a.style != "spotlight":
            size = x.H * .62
            logo_mark(x, x.H * .2 + size / 2, x.H / 2, size)
    elif a.kind == "footer":
        footer(x)
    else:
        divider(x)
    css = "" if not x.animate else "".join(x.css)
    reduce = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
    label = " — ".join(t for t in (x.title, x.sub) if t) or f"{a.style} {a.kind}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{x.W}" height="{x.H}" viewBox="0 0 {x.W} {x.H}" role="img" aria-labelledby="t">'
            f'<title id="t">{esc(label)}</title>'
            f'<style>{css}{reduce}</style>'
            f'<defs>{"".join(x.defs)}</defs>{"".join(x.body)}</svg>\n')


def snippet(base: str, alt: str, width_attr="100%") -> str:
    return ("<picture>\n"
            f'  <source media="(prefers-color-scheme: dark)" srcset="{base}-dark.svg">\n'
            f'  <img alt="{esc(alt)}" src="{base}-light.svg" width="{width_attr}">\n'
            "</picture>")


def readme_path(target: Path) -> str:
    """Path for the README snippet: relative to the repo root (nearest .git), else to the cwd.
    README image paths must be relative; an absolute C:/... or /home/... path breaks on GitHub."""
    full = target.resolve()
    root = next((d for d in [full.parent, *full.parent.parents] if (d / ".git").exists()), Path.cwd().resolve())
    try:
        return os.path.relpath(full, root).replace(os.sep, "/")
    except ValueError:  # different drive on Windows
        print("warning: output is outside the repository; move the SVGs into it and fix the paths below", file=sys.stderr)
        return target.as_posix()


def write(a, out: Path, stem: str):
    out.mkdir(parents=True, exist_ok=True)
    themes = ["dark", "light"] if a.theme == "both" else [a.theme]
    for t in themes:
        svg = button_svg(a, t) if a.kind == "button" else render(a, t)
        (out / f"{stem}-{t}.svg").write_text(svg, encoding="utf-8")
    return themes


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Animated SVG headers/footers/dividers for READMEs")
    p.add_argument("--kind", choices=["header", "footer", "divider", "button"], default="header")
    p.add_argument("--variant", choices=["primary", "secondary"], default="primary", help="button style")
    p.add_argument("--href", default="#", help="button link target")
    p.add_argument("--style", default="aurora", choices=sorted(STYLES))
    p.add_argument("--palette", choices=sorted(PALETTES))
    p.add_argument("--accent")
    p.add_argument("--logo", metavar="FILE", help="PNG/SVG/WebP/JPG logo embedded in a header (transparent background works best)")
    p.add_argument("--title", default="")
    p.add_argument("--subtitle", default="")
    p.add_argument("--tag", default="")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int)
    p.add_argument("--theme", choices=["dark", "light", "both"], default="both")
    p.add_argument("--static", action="store_true")
    p.add_argument("--out", default=".")
    p.add_argument("--name", help="file stem (default: <kind>)")
    p.add_argument("--list", action="store_true")
    p.add_argument("--gallery", metavar="DIR")
    a = p.parse_args(argv)

    if a.list:
        print("Styles:")
        for k, (pal, d) in STYLES.items():
            print(f"  {k:<14} {d}  (palette: {pal})")
        print("Palettes:", ", ".join(PALETTES))
        return 0

    if a.gallery:
        out = Path(a.gallery)
        rows = ["# Banner gallery\n", "Generated by `scripts/make_banner.py`. Each style has dark + light variants; switch your GitHub theme to see both.\n"]
        for style, (pal, desc) in STYLES.items():
            a2 = argparse.Namespace(**{**vars(a), "kind": "header", "style": style, "palette": None, "height": 320,
                                       "title": a.title or "readme-forge", "subtitle": a.subtitle or "READMEs that look as good as your code",
                                       "tag": a.tag or "Claude skill"})
            write(a2, out, f"{style}")
            rows.append(f"## {style}\n\n_{desc}_ · `--style {style}`\n\n" + snippet(style, f"{style} banner: readme-forge") + "\n")
        for kind, style, h, t in (("footer", "wave", 160, "Thanks for reading"), ("footer", "minimal", 120, "Made with readme-forge"), ("divider", "aurora", 24, "")):
            a3 = argparse.Namespace(**{**vars(a), "kind": kind, "style": style, "palette": "ember" if style != "wave" else None, "height": h, "title": t, "subtitle": "", "tag": ""})
            write(a3, out, f"{kind}-{style}")
            rows.append(f"## {kind}: {style}\n\n" + snippet(f"{kind}-{style}", f"{kind} ({style})") + "\n")
        for variant, label in (("primary", "Get started"), ("secondary", "Read the docs")):
            a4 = argparse.Namespace(**{**vars(a), "kind": "button", "variant": variant, "palette": "midnight", "title": label})
            write(a4, out, f"button-{variant}")
            rows.append(f"## button: {variant}\n\n" + snippet(f"button-{variant}", label, width_attr="auto").replace(' width="auto"', ' height="44"') + "\n")
        (out / "gallery.md").write_text("\n".join(rows), encoding="utf-8")
        print(f"wrote {len(STYLES)} headers + 2 footers + 1 divider + 2 buttons (dark+light) to {out}")
        return 0

    a.logo_uri = None
    if a.logo:
        lp = Path(a.logo)
        if not lp.is_file():
            p.error(f"--logo: {lp} not found")
        mime = {".png": "image/png", ".svg": "image/svg+xml", ".webp": "image/webp", ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg", ".gif": "image/gif"}.get(lp.suffix.lower())
        if not mime:
            p.error("--logo must be .png, .svg, .webp, .jpg or .gif")
        data = lp.read_bytes()
        if len(data) > 200_000:
            print(f"warning: logo is {len(data) // 1024} KB; resize it to ~320 px so the README loads fast", file=sys.stderr)
        a.logo_uri = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")
    if a.height is None:
        a.height = {"header": 320, "footer": 160, "divider": 24, "button": 44}[a.kind]
    if a.kind == "header" and not a.title:
        p.error("--title is required for headers")
    stem = a.name or a.kind
    themes = write(a, Path(a.out), stem)
    alt = " — ".join(t for t in (a.title, a.subtitle) if t) or f"{a.kind}"
    rel = readme_path(Path(a.out) / stem)
    print(f"wrote {', '.join(f'{stem}-{t}.svg' for t in themes)} in {a.out}\n")
    if a.kind == "button":
        alt = a.title or "Get started"
        print(f'<a href="{esc(a.href)}">' + snippet(rel, alt, width_attr="auto").replace(' width="auto"', ' height="44"') + "</a>")
        return 0
    print(snippet(rel, alt) if a.theme == "both" else f'<img alt="{esc(alt)}" src="{rel}-{themes[0]}.svg" width="100%">')
    return 0


if __name__ == "__main__":
    sys.exit(main())
