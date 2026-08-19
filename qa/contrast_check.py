#!/usr/bin/env python3
"""Fail-closed WCAG contrast check for the TNSuite BridgeX Build12-Hotfix16 palette."""
from __future__ import annotations

PAIRS = [
    ("Primary / main background", "#F3F7FB", "#0F1724", 4.5),
    ("Primary / control background", "#F3F7FB", "#162235", 4.5),
    ("Secondary / main background", "#A9B6C6", "#0F1724", 4.5),
    ("Disabled / control background", "#A9B6C6", "#162235", 4.5),
    ("Selected row text / selection", "#F3F7FB", "#0E5EA8", 4.5),
    ("Menu hover text / hover", "#F3F7FB", "#173B5A", 4.5),
    ("Link/hot text / main background", "#45C7FF", "#0F1724", 4.5),
    ("UI border / control background", "#5B6F86", "#111B2A", 3.0),
]

def channel(v: int) -> float:
    x = v / 255.0
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

def ratio(fg: str, bg: str) -> float:
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)

failed = False
print("TNSuite BridgeX Build12-Hotfix16 - contrast QA")
print("=" * 72)
for name, fg, bg, minimum in PAIRS:
    value = ratio(fg, bg)
    status = "PASS" if value >= minimum else "FAIL"
    print(f"{status:4}  {name:42} {value:5.2f}:1  >= {minimum:.1f}:1")
    failed |= value < minimum

if failed:
    raise SystemExit(1)
print("CONTRAST_QA=PASS")
