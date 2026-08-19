#!/usr/bin/env python3
from pathlib import Path
import struct
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: branding_asset_check.py <kit-root>")
root = Path(sys.argv[1]).resolve()
assets = root / "assets" / "branding"
checks=[]

def check(label, ok):
    checks.append((label, bool(ok)))
    print(("PASS  " if ok else "FAIL  ") + label)

def png_info(path: Path):
    # PNG signature + IHDR length/type + IHDR payload (13 bytes)
    data=path.read_bytes()[:33]
    if len(data)<33 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise ValueError('invalid PNG header')
    w,h,bit_depth,color_type,compression,filter_method,interlace = struct.unpack('>IIBBBBB',data[16:29])
    return w,h,bit_depth,color_type

required = {
    "BridgeX-AppIcon.png": ((1254,1254), True),
    "BridgeX-Logo.png": ((1672,941), True),
    "BridgeX-UI-Reference.png": ((1448,1086), False),
    "BridgeX-16x16.png": ((16,16), True),
    "BridgeX-32x32.png": ((32,32), True),
    "BridgeX-48x48.png": ((48,48), True),
    "BridgeX-256x256.png": ((256,256), True),
    "BridgeX-480x480.png": ((480,480), True),
}
for name, (size, require_alpha) in required.items():
    p=assets/name
    ok=p.is_file() and p.stat().st_size>100
    color_type=None
    if ok:
        try:
            w,h,bit_depth,color_type=png_info(p)
            ok=(w,h)==size and bit_depth in (8,16)
            if require_alpha:
                ok=ok and color_type in (4,6)
        except Exception:
            ok=False
    suffix=' alpha' if require_alpha else ''
    check(f"Brand asset {name} {size[0]}x{size[1]}{suffix}",ok)

ico=assets/"BridgeX-AppIcon.ico"
ico_ok=ico.is_file() and ico.stat().st_size>1000
count=0
if ico_ok:
    data=ico.read_bytes()[:6]
    if len(data)==6:
        reserved,kind,count=struct.unpack('<HHH',data)
        ico_ok=(reserved==0 and kind==1 and count>=6)
check(f"Windows multi-resolution app icon ({count} entries)",ico_ok)

patch=(root/"scripts"/"patch_tnsuite_bridgex.py").read_text(encoding="utf-8")
for label, needle in [
    ("Brand display name patch", 'SetAppDisplayName("TNSuite BridgeX")'),
    ("Modern toolbar patch", 'TNSUITE_BRIDGEX_BUILD12_MODERN_TOOLBAR'),
    ("Quick Connect UI patch", 'TNSUITE_BRIDGEX_BUILD12_QUICK_CONNECT'),
    ("Pane header UI patch", 'TNSUITE_BRIDGEX_BUILD12_PANE_HEADER'),
    ("Automation menu patch", 'TNSUITE_BRIDGEX_BUILD12_AUTOMATION_MENU'),
    ("Windows icon replacement", 'BridgeX-AppIcon.ico'),
]:
    check(label, needle in patch)

installer=(root/"installer"/"TNSuiteBridgeXInstaller.nsi").read_text(encoding="utf-8")
check("Installer consumes branded icon", 'BRAND_ICON' in installer and 'Icon "${BRAND_ICON}"' in installer)

if not all(ok for _,ok in checks):
    print("BRANDING_ASSET_QA=FAIL")
    raise SystemExit(1)
print("BRANDING_ASSET_QA=PASS")
