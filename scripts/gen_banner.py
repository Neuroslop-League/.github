#!/usr/bin/env python3
"""Generate the Neuroslop League banner (light + dark) as static SVG.

Same geometry and visual language as RUdolf1517's personal profile banner:
1000px wide, two theme-matched files under assets/.

    python3 scripts/gen_banner.py

Writes assets/banner-dark.svg and assets/banner-light.svg.
"""

from __future__ import annotations

from pathlib import Path

W, H = 1000, 330

from theme import MONO, SANS, THEMES  # noqa: E402

PX = 56
TX, TY, TW, TH = 588, 54, 356, 222
EYEBROW_Y = 66
NAME1_Y, NAME2_Y = 132, 224
MONO_Y, TAG_Y = 250, 292

TAGLINE = "An independent collective of vibe coders & slop enthusiasts."
MONO_LINE = "NEUROSLOP LEAGUE — EST. 2026"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def banner(name: str) -> str:
    t = THEMES[name]

    lines = [
        (f'<tspan fill="{t["term_amber"]}">$</tspan> <tspan fill="{t["term_text"]}">neuroslop gen "cat in space"</tspan>', 54),
        (f'<tspan fill="{t["term_green"]}">&#10003; cat_space_final_v27.png</tspan>', 75),
        (f'<tspan fill="{t["term_amber"]}">$</tspan> <tspan fill="{t["term_text"]}">grep quality /dev/null</tspan>', 104),
        (f'<tspan fill="{t["term_muted"]}">grep: quality: not found</tspan>', 125),
        (f'<tspan fill="{t["term_amber"]}">$</tspan> <tspan fill="{t["term_text"]}">ls</tspan>', 154),
        (f'<tspan fill="{t["term_green"]}">ideas/</tspan>  <tspan fill="{t["term_green"]}">slop/</tspan>  <tspan fill="{t["term_green"]}">final/</tspan>', 175),
        (f'<tspan fill="{t["term_amber"]}">$</tspan>', 203),
    ]
    term_lines = "\n".join(
        f'      <text x="{TX + 24}" y="{TY + dy}" font-family="{MONO}" font-size="12.5" xml:space="preserve" '
        f'direction="ltr">{line}</text>'
        for line, dy in lines
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Neuroslop League</title>
  <desc id="d">Banner of the Neuroslop League GitHub organization: organization name and a terminal running the mythical neuroslop CLI.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['bg0']}"/><stop offset="1" stop-color="{t['bg1']}"/>
    </linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['name_from']}"/><stop offset="1" stop-color="{t['name_to']}"/>
    </linearGradient>
    <radialGradient id="glowA" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['amber']}" stop-opacity="{t['amber_op']}"/>
      <stop offset="1" stop-color="{t['amber']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowB" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['blue']}" stop-opacity="{t['blue_op']}"/>
      <stop offset="1" stop-color="{t['blue']}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="21" height="21" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1.05" fill="{t['dot']}" fill-opacity="{t['dot_op']}"/>
    </pattern>
    <clipPath id="frame"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22"/></clipPath>
    <filter id="lift" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="9" stdDeviation="13" flood-color="{t['shadow']}" flood-opacity="{t['shadow_op']}"/>
    </filter>
    <style>
      .caret {{ animation: blink 1.15s steps(1, end) infinite; }}
      .pulse {{ animation: pulse 3.6s ease-in-out infinite; }}
      @keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
      @keyframes pulse {{ 0%, 100% {{ opacity: 0.35; }} 50% {{ opacity: 0.9; }} }}
      @media (prefers-reduced-motion: reduce) {{ .caret, .pulse {{ animation: none; }} }}
    </style>
  </defs>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <rect width="{W}" height="{H}" fill="url(#dots)"/>
    <ellipse cx="110" cy="-10" rx="380" ry="250" fill="url(#glowA)"/>
    <ellipse cx="930" cy="{H + 10}" rx="340" ry="230" fill="url(#glowB)"/>
    <rect width="{W}" height="2.4" fill="url(#name)" opacity="0.85"/>

    <circle class="pulse" cx="{PX + 3}" cy="{EYEBROW_Y - 4}" r="4.2" fill="{t['amber']}"/>
    <text x="{PX + 17}" y="{EYEBROW_Y}" font-family="{MONO}" font-size="11" letter-spacing="3.4" fill="{t['eyebrow']}">GITHUB ORGANIZATION</text>

    <text x="{PX - 2}" y="{NAME1_Y}" font-family="{SANS}" font-size="62" font-weight="700" letter-spacing="-1.2" fill="url(#name)">NEUROSLOP</text>
    <text x="{PX - 2}" y="{NAME2_Y}" font-family="{SANS}" font-size="62" font-weight="700" letter-spacing="-1.2" fill="url(#name)">LEAGUE</text>
    <text x="{PX}" y="{MONO_Y}" font-family="{MONO}" font-size="10.5" letter-spacing="2.2" fill="{t['eyebrow']}">{esc(MONO_LINE)}</text>
    <text x="{PX}" y="{TAG_Y}" font-family="{SANS}" font-size="14.5" fill="{t['tagline']}">{esc(TAGLINE)}</text>

    <g filter="url(#lift)">
      <rect x="{TX}" y="{TY}" width="{TW}" height="{TH}" rx="14" fill="{t['term_bg']}" stroke="{t['term_border']}" stroke-width="1"/>
    </g>
    <path d="M{TX} {TY + 33} h{TW}" stroke="{t['term_border']}" stroke-width="1"/>
    <circle cx="{TX + 21}" cy="{TY + 16.5}" r="4" fill="{t['term_dot1']}" opacity="0.88"/>
    <circle cx="{TX + 38}" cy="{TY + 16.5}" r="4" fill="{t['term_dot2']}" opacity="0.78"/>
    <circle cx="{TX + 55}" cy="{TY + 16.5}" r="4" fill="{t['term_dot3']}" opacity="0.78"/>
    <text x="{TX + TW - 18}" y="{TY + 20}" text-anchor="end" font-family="{MONO}" font-size="10.5" fill="{t['term_muted']}">zsh</text>
{term_lines}
    <rect class="caret" x="{TX + 38}" y="{TY + 192}" width="7" height="13.5" fill="{t['term_amber']}" opacity="0.9"/>
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22" fill="none" stroke="{t['border']}" stroke-width="1"/>
</svg>
"""


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        path = out / f"banner-{theme}.svg"
        path.write_text(banner(theme), encoding="utf-8")
        print(f"wrote {path} ({path.stat().st_size} B)")


if __name__ == "__main__":
    main()
