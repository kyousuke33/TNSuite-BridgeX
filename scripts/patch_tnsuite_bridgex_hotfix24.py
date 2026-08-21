#!/usr/bin/env python3
"""Hotfix24: assign the original BridgeX multi-resolution icon to the main wxFrame.

This is intentionally separate from the Build12 base patch so the withdrawn
Hotfix16 baseline remains auditable. The build adapter applies this patch after
scripts/patch_tnsuite_bridgex.py on a disposable FileZilla 3.70.6 source tree.
"""
from __future__ import annotations

import pathlib
import re
import sys

MARKER = "TNSUITE_BRIDGEX_BUILD12_HF24_TASKBAR_ICON"

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch_tnsuite_bridgex_hotfix24.py <filezilla-source-root>")

root = pathlib.Path(sys.argv[1]).resolve()
mainfrm = root / "src" / "interface" / "Mainfrm.cpp"
if not mainfrm.is_file():
    raise SystemExit(f"HF24_PATCH_FAIL: missing Mainfrm.cpp: {mainfrm}")

text = mainfrm.read_text(encoding="utf-8")
if MARKER in text:
    print("HOTFIX24_TASKBAR_ICON_PATCH=ALREADY_APPLIED")
    raise SystemExit(0)

# wxTopLevelWindow::SetIcons consumes a wxIconBundle, preserving all useful ICO
# sizes instead of forcing Windows to stretch one extracted 32x32 representation.
headers = (
    "#include <wx/filename.h>\n",
    "#include <wx/iconbndl.h>\n",
    "#include <wx/stdpaths.h>\n",
)
for header in headers:
    if header.strip() in text:
        continue
    first_include = re.search(r"(?m)^#include[^\n]*\n", text)
    if not first_include:
        raise SystemExit("HF24_PATCH_FAIL: Mainfrm.cpp include anchor not found")
    pos = first_include.end()
    text = text[:pos] + header + text[pos:]

# Find the constructor body without depending on its initializer-list contents.
constructor = re.search(r"\bCMainFrame::CMainFrame\s*\(", text)
if not constructor:
    raise SystemExit("HF24_PATCH_FAIL: CMainFrame constructor not found")

# Skip C++ comments/strings while looking for the first constructor body brace.
def first_code_brace(source: str, start: int) -> int:
    i = start
    state = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if ch == "/" and nxt == "/":
                state = "line"; i += 2; continue
            if ch == "/" and nxt == "*":
                state = "block"; i += 2; continue
            if ch == '"':
                state = "string"; i += 1; continue
            if ch == "'":
                state = "char"; i += 1; continue
            if ch == "{":
                return i
            i += 1; continue
        if state == "line":
            if ch == "\n": state = "code"
            i += 1; continue
        if state == "block":
            if ch == "*" and nxt == "/": state = "code"; i += 2; continue
            i += 1; continue
        if ch == "\\":
            i += 2; continue
        if state == "string" and ch == '"': state = "code"
        elif state == "char" and ch == "'": state = "code"
        i += 1
    return -1

brace = first_code_brace(text, constructor.end())
if brace < 0:
    raise SystemExit("HF24_PATCH_FAIL: CMainFrame constructor body not found")

icon_code = r'''

#ifdef __WXMSW__
	// TNSUITE_BRIDGEX_BUILD12_HF24_TASKBAR_ICON
	// BridgeX-AppIcon.ico is copied next to BridgeX.exe by the Hotfix24 runtime
	// adapter. AddIcon imports every size stored in the original ICO and SetIcons
	// applies the bundle to the top-level window used by the Windows taskbar.
	wxFileName const bridgeXExecutable(wxStandardPaths::Get().GetExecutablePath());
	wxString const bridgeXIconPath = bridgeXExecutable.GetPathWithSep() + L"BridgeX-AppIcon.ico";
	wxIconBundle bridgeXIcons;
	bridgeXIcons.AddIcon(bridgeXIconPath, wxBITMAP_TYPE_ICO);
	if (!bridgeXIcons.IsEmpty()) {
		SetIcons(bridgeXIcons);
	}
#endif
'''
text = text[: brace + 1] + icon_code + text[brace + 1 :]
mainfrm.write_text(text, encoding="utf-8", newline="\n")

check = mainfrm.read_text(encoding="utf-8")
for required in (MARKER, "SetIcons(bridgeXIcons)", "BridgeX-AppIcon.ico"):
    if required not in check:
        raise SystemExit(f"HF24_PATCH_FAIL: missing post-patch marker: {required}")

print("HOTFIX24_TASKBAR_ICON_PATCH=PASS")
