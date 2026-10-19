#!/usr/bin/env python3
"""Convert text to Unicode "fancy font" styles for profile READMEs (Fancy Fonts archetype).

GitHub can't change fonts, so profiles use Unicode Mathematical Alphanumeric Symbols
(𝗯𝗼𝗹𝗱, 𝙞𝙩𝙖𝙡𝙞𝙘, 𝚖𝚘𝚗𝚘, …). This maps letters and digits correctly, including the
letters that live outside the block (ℎ, ℂ, ℝ, …), and leaves everything else as is.

Screen readers spell these characters out one by one ("mathematical bold capital H")
and GitHub search can't find them, so use them for short decorative lines only and
keep your name and key facts in plain text somewhere on the page.

  python fancy_text.py "Hello, I'm Ada" --style sans-bold
  python fancy_text.py "Hello" --all
"""
from __future__ import annotations

import argparse
import sys

# style: (A, a, 0) start code points; None = no digits in that style
STYLES = {
    "bold":             (0x1D400, 0x1D41A, 0x1D7CE),
    "italic":           (0x1D434, 0x1D44E, None),
    "bold-italic":      (0x1D468, 0x1D482, None),
    "sans-bold":        (0x1D5D4, 0x1D5EE, 0x1D7EC),
    "sans-italic":      (0x1D608, 0x1D622, None),
    "sans-bold-italic": (0x1D63C, 0x1D656, None),
    "mono":             (0x1D670, 0x1D68A, 0x1D7F6),
    "double-struck":    (0x1D538, 0x1D552, 0x1D7D8),
}
# Letters already encoded in Letterlike Symbols; their slots in the math block are unassigned.
HOLES = {
    "italic": {"h": "ℎ"},
    "double-struck": {"C": "ℂ", "H": "ℍ", "N": "ℕ", "P": "ℙ",
                      "Q": "ℚ", "R": "ℝ", "Z": "ℤ"},
}


def convert(text: str, style: str) -> str:
    upper, lower, digit = STYLES[style]
    holes = HOLES.get(style, {})
    out = []
    for ch in text:
        if ch in holes:
            out.append(holes[ch])
        elif "A" <= ch <= "Z":
            out.append(chr(upper + ord(ch) - 65))
        elif "a" <= ch <= "z":
            out.append(chr(lower + ord(ch) - 97))
        elif "0" <= ch <= "9" and digit:
            out.append(chr(digit + ord(ch) - 48))
        else:
            out.append(ch)
    return "".join(out)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("text")
    p.add_argument("--style", choices=sorted(STYLES), default="sans-bold")
    p.add_argument("--all", action="store_true", help="print the text in every style")
    a = p.parse_args(argv)
    if a.all:
        for s in STYLES:
            print(f"{s:<17} {convert(a.text, s)}")
    else:
        print(convert(a.text, a.style))
    return 0


if __name__ == "__main__":
    sys.exit(main())
