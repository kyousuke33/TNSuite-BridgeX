#!/usr/bin/env python3
from pathlib import Path
import struct
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: branding_contract_check.py <repo-root>")

root = Path(sys.argv[1]).resolve()
assets = root / "assets" / "branding"
checks = []


def check(label, ok):
    ok = bool(ok)
    checks.append((label, ok))
    print(("PASS  " if ok else "FAIL  ") + label)


def png_info(path: Path):
    data = path.read_bytes()[:33]
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("invalid PNG header")
    return struct.unpack(">IIBBBBB", data[16:29])


# Audit decision: these BuildKit design/reference exports are intentionally not
# canonical repository source. Reintroducing them is a governance regression.
for name in (
    "BridgeX-AppIcon.png",
    "BridgeX-Logo.png",
    "BridgeX-UI-Reference.png",
):
    check(f"Excluded non-canonical branding export absent: {name}", not (assets / name).exists())

# Canonical runtime/package branding assets pinned by the Hotfix16 manifest.
for size in (16, 20, 24, 32, 48, 64, 96, 128, 256, 480):
    name = f"BridgeX-{size}x{size}.png"
    path = assets / name
    ok = path.is_file() and path.stat().st_size > 100
    if ok:
        try:
            w, h, bit_depth, color_type, _compression, _filter, _interlace = png_info(path)
            ok = (w, h) == (size, size) and bit_depth in (8, 16) and color_type in (4, 6)
        except Exception:
            ok = False
    check(f"Canonical brand asset {name} {size}x{size} alpha", ok)

ico = assets / "BridgeX-AppIcon.ico"
ico_ok = ico.is_file() and ico.stat().st_size > 1000
count = 0
if ico_ok:
    data = ico.read_bytes()[:6]
    if len(data) == 6:
        reserved, kind, count = struct.unpack("<HHH", data)
        ico_ok = reserved == 0 and kind == 1 and count >= 6
check(f"Windows multi-resolution app icon ({count} entries)", ico_ok)

for rel in ("installer/BridgeX-Setup-Header.bmp", "installer/BridgeX-Setup-Sidebar.bmp"):
    path = root / rel
    ok = path.is_file() and path.stat().st_size > 100 and path.read_bytes()[:2] == b"BM"
    check(f"Canonical installer bitmap {rel}", ok)

patch = (root / "scripts" / "patch_tnsuite_bridgex.py").read_text(encoding="utf-8")
for label, needle in [
    ("Brand display name patch", 'SetAppDisplayName("TNSuite BridgeX")'),
    ("Modern toolbar patch", "TNSUITE_BRIDGEX_BUILD12_MODERN_TOOLBAR"),
    ("Quick Connect UI patch", "TNSUITE_BRIDGEX_BUILD12_QUICK_CONNECT"),
    ("Pane header UI patch", "TNSUITE_BRIDGEX_BUILD12_PANE_HEADER"),
    ("Automation menu patch", "TNSUITE_BRIDGEX_BUILD12_AUTOMATION_MENU"),
    ("Windows icon replacement", "BridgeX-AppIcon.ico"),
]:
    check(label, needle in patch)

installer = (root / "installer" / "TNSuiteBridgeXInstaller.nsi").read_text(encoding="utf-8")
check("Installer consumes branded icon", "BRAND_ICON" in installer and 'Icon "${BRAND_ICON}"' in installer)

if not all(ok for _, ok in checks):
    print("BRANDING_CONTRACT_QA=FAIL")
    raise SystemExit(1)

print("BRANDING_CONTRACT_QA=PASS")
