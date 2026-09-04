#!/usr/bin/env python3
"""Hotfix25 runtime overlay: remove wxImage ICO dependency from main-window icon loading.

Applied after Hotfix24 on the disposable FileZilla 3.70.6 source tree.
The canonical BridgeX ICO is already copied over resources/FileZilla.ico by the
Build12 baseline patch. Hotfix25 exposes that ICO under a deterministic Windows
resource name and loads the frame icon bundle directly from Win32 resources.
"""
from __future__ import annotations

import pathlib
import sys

MARKER = "TNSUITE_BRIDGEX_BUILD12_HF25_RESOURCE_ICON"
RESOURCE_NAME = "BRIDGEX_APP_ICON"

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch_tnsuite_bridgex_hotfix25.py <filezilla-source-root>")

root = pathlib.Path(sys.argv[1]).resolve()
mainfrm = root / "src" / "interface" / "Mainfrm.cpp"
resource_rc = root / "src" / "interface" / "resources" / "filezilla.rc"

for required in (mainfrm, resource_rc):
    if not required.is_file():
        raise SystemExit(f"HF25_PATCH_FAIL: missing source file: {required}")

rc_text = resource_rc.read_text(encoding="utf-8")
resource_line = f'{RESOURCE_NAME} ICON "FileZilla.ico"'
if resource_line not in rc_text:
    if "FileZilla.ico" not in rc_text:
        raise SystemExit("HF25_PATCH_FAIL: FileZilla.ico resource anchor missing")
    if not rc_text.endswith("\n"):
        rc_text += "\n"
    rc_text += f"\n// {MARKER}\n{resource_line}\n"
    resource_rc.write_text(rc_text, encoding="utf-8", newline="\n")

text = mainfrm.read_text(encoding="utf-8")
if MARKER not in text:
    hf24_marker = "TNSUITE_BRIDGEX_BUILD12_HF24_TASKBAR_ICON"
    marker_pos = text.find(hf24_marker)
    if marker_pos < 0:
        raise SystemExit("HF25_PATCH_FAIL: Hotfix24 icon block marker missing")

    block_start = text.rfind("#ifdef __WXMSW__", 0, marker_pos)
    block_end_start = text.find("#endif", marker_pos)
    if block_start < 0 or block_end_start < 0:
        raise SystemExit("HF25_PATCH_FAIL: Hotfix24 Windows icon block bounds missing")
    block_end = block_end_start + len("#endif")

    # Use only the public Windows wrapper header. This exposes GetModuleHandleW
    # without depending on wxWidgets' private wxGetInstance declaration.
    wrapwin_header = "#ifdef __WXMSW__\n#include <wx/msw/wrapwin.h>\n#endif\n"
    if "#include <wx/msw/wrapwin.h>" not in text:
        include_anchor = "#include <wx/iconbndl.h>\n"
        if include_anchor not in text:
            raise SystemExit("HF25_PATCH_FAIL: wx/iconbndl.h include anchor missing")
        text = text.replace(include_anchor, include_anchor + wrapwin_header, 1)
        # Header insertion occurs before the constructor and therefore does not
        # invalidate the previously discovered block offsets.
        offset = len(wrapwin_header)
        block_start += offset
        block_end += offset

    replacement = r'''#ifdef __WXMSW__
	// TNSUITE_BRIDGEX_BUILD12_HF25_RESOURCE_ICON
	// Load the canonical multi-resolution BridgeX icon directly from the PE
	// RT_GROUP_ICON resource. wxIconBundle's Windows resource constructor uses
	// CreateIconFromResourceEx and therefore cannot emit the wxImage
	// "No image handler for type 3 defined." startup warning.
	auto const bridgeXModule = reinterpret_cast<WXHINSTANCE>(::GetModuleHandleW(nullptr));
	wxIconBundle bridgeXIcons(L"BRIDGEX_APP_ICON", bridgeXModule);
	if (!bridgeXIcons.IsEmpty()) {
		SetIcons(bridgeXIcons);
	}
#endif'''
    text = text[:block_start] + replacement + text[block_end:]
    mainfrm.write_text(text, encoding="utf-8", newline="\n")

patched_main = mainfrm.read_text(encoding="utf-8")
patched_rc = resource_rc.read_text(encoding="utf-8")
required_main = (
    MARKER,
    "#include <wx/msw/wrapwin.h>",
    "reinterpret_cast<WXHINSTANCE>(::GetModuleHandleW(nullptr))",
    'wxIconBundle bridgeXIcons(L"BRIDGEX_APP_ICON", bridgeXModule)',
    "SetIcons(bridgeXIcons)",
)
for required in required_main:
    if required not in patched_main:
        raise SystemExit(f"HF25_PATCH_FAIL: missing main-frame post-check marker: {required}")
if resource_line not in patched_rc:
    raise SystemExit("HF25_PATCH_FAIL: deterministic icon resource missing")
if "bridgeXIcons.AddIcon(bridgeXIconPath, wxBITMAP_TYPE_ICO)" in patched_main:
    raise SystemExit("HF25_PATCH_FAIL: file-based wxImage ICO path still present")
if "wxGetInstance()" in patched_main:
    raise SystemExit("HF25_PATCH_FAIL: private wxGetInstance dependency still present")

print("HOTFIX25_RESOURCE_ICON_PATCH=PASS")
print("HOTFIX25_WXIMAGE_ICO_DEPENDENCY=REMOVED")
print("HOTFIX25_MODULE_HANDLE=WIN32_PUBLIC_API")
