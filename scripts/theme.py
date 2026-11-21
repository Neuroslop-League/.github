#!/usr/bin/env python3
"""Shared monochrome (black & white) palette and font stacks for the org cards.

All generators (banner, member-contributions card) draw with the same colours,
so the cards look like one unified black-and-white set.
"""

from __future__ import annotations

SANS = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

THEMES = {
    "dark": dict(
        bg0="#050505", bg1="#0E0E0E", border="#262626",
        dot="#2B2B2B", dot_op="0.55",
        amber="#FFFFFF", amber_op="0.09", blue="#D4D4D4", blue_op="0.06",
        text="#FFFFFF", text_soft="#D4D4D4", muted="#8E8E8E", label="#666666",
        name_from="#FFFFFF", name_to="#A6A6A6",
        eyebrow="#E5E5E5", tagline="#A3A3A3",
        pill_bg="#121212", pill_border="#2A2A2A", pill_text="#D4D4D4",
        term_bg="#080808", term_border="#2A2A2A",
        term_text="#F5F5F5", term_muted="#737373",
        term_green="#D4D4D4", term_amber="#FFFFFF",
        term_dot1="#FFFFFF", term_dot2="#999999", term_dot3="#525252",
        bar="#404040", bar_accent="#FFFFFF", stub="#1A1A1A",
        hair="#242424",
        shadow="#000000", shadow_op="0.55",
        members=[
            "#FFFFFF",  # 1
            "#D4D4D4",  # 2
            "#A8A8A8",  # 3
            "#828282",  # 4
            "#616161",  # 5
            "#474747",  # 6
            "#333333",  # 7
        ],
    ),
    "light": dict(
        bg0="#FFFFFF", bg1="#F4F4F4", border="#DCDCDC",
        dot="#D4D4D4", dot_op="0.75",
        amber="#000000", amber_op="0.06", blue="#525252", blue_op="0.05",
        text="#0A0A0A", text_soft="#262626", muted="#666666", label="#808080",
        name_from="#000000", name_to="#404040",
        eyebrow="#171717", tagline="#525252",
        pill_bg="#FFFFFF", pill_border="#DCDCDC", pill_text="#262626",
        term_bg="#0A0A0A", term_border="#D4D4D4",
        term_text="#F5F5F5", term_muted="#737373",
        term_green="#D4D4D4", term_amber="#FFFFFF",
        term_dot1="#FFFFFF", term_dot2="#999999", term_dot3="#525252",
        bar="#BDBDBD", bar_accent="#111111", stub="#E5E5E5",
        hair="#E0E0E0",
        shadow="#000000", shadow_op="0.14",
        members=[
            "#0A0A0A",  # 1
            "#333333",  # 2
            "#595959",  # 3
            "#7D7D7D",  # 4
            "#9E9E9E",  # 5
            "#B8B8B8",  # 6
            "#CCCCCC",  # 7
        ],
    ),
}
