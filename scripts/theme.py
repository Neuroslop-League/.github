#!/usr/bin/env python3
"""Shared palette and font stacks for the org cards.

All generators (banner, member-contributions card) draw with the same colours,
so the cards look like one set — and like one family with RUdolf1517's profile.
Keys are a union of what each card needs; a card simply ignores the keys it
does not use.
"""

from __future__ import annotations

SANS = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

THEMES = {
    "dark": dict(
        bg0="#0A0E15", bg1="#0C1220", border="#1D2837",
        dot="#1A2433", dot_op="0.55",
        amber="#F0A87B", amber_op="0.20", blue="#4F8DF7", blue_op="0.18",
        text="#FFFFFF", text_soft="#C3D2E4", muted="#7C8CA1", label="#5C6B7F",
        name_from="#FFFFFF", name_to="#C3D2E4",
        eyebrow="#F0A87B", tagline="#98A8BC",
        pill_bg="#101826", pill_border="#223043", pill_text="#C9D5E3",
        term_bg="#0C131D", term_border="#223043",
        term_text="#D7E2EF", term_muted="#7C8CA1",
        term_green="#6EE7B7", term_amber="#F0A87B",
        bar="#33465F", bar_accent="#F0A87B", stub="#1B2534",
        hair="#1D2837",
        shadow="#000000", shadow_op="0.45",
        members=[
            "#F0A87B",  # amber
            "#4F8DF7",  # blue
            "#6EE7B7",  # mint
            "#A78BFA",  # violet
            "#F472B6",  # rose
            "#38BDF8",  # sky
            "#FBBF24",  # gold
            "#FB7185",  # coral
        ],
    ),
    "light": dict(
        bg0="#FFFFFF", bg1="#F5F8FC", border="#E1E8F1",
        dot="#DCE4EF", dot_op="0.8",
        amber="#F59E6B", amber_op="0.22", blue="#4F8DF7", blue_op="0.16",
        text="#0B1220", text_soft="#33445B", muted="#6B7C92", label="#8595A8",
        name_from="#0B1220", name_to="#26344A",
        eyebrow="#C2643A", tagline="#5A6B80",
        pill_bg="#FFFFFF", pill_border="#DCE4EF", pill_text="#33445B",
        term_bg="#0C131D", term_border="#D8E0EA",
        term_text="#D7E2EF", term_muted="#7C8CA1",
        term_green="#6EE7B7", term_amber="#F0A87B",
        bar="#A9BBD2", bar_accent="#D98250", stub="#E3EAF3",
        hair="#E1E8F1",
        shadow="#94A3B8", shadow_op="0.20",
        members=[
            "#D98250",  # amber
            "#3B76E1",  # blue
            "#10B981",  # emerald
            "#7C3AED",  # violet
            "#DB2777",  # pink
            "#0284C7",  # sky
            "#D97706",  # ochre
            "#E11D48",  # crimson
        ],
    ),
}
