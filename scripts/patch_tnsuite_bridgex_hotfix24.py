#!/usr/bin/env python3
"""Hotfix24 runtime overlay for the disposable FileZilla 3.70.6 source tree.

This is intentionally separate from the pinned Build12-Hotfix16 baseline so
Hotfix24 runtime corrections do not rewrite historical source authority.
"""
from __future__ import annotations

import pathlib
import re
import sys

ICON_MARKER = "TNSUITE_BRIDGEX_BUILD12_HF24_TASKBAR_ICON"

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch_tnsuite_bridgex_hotfix24.py <filezilla-source-root>")

root = pathlib.Path(sys.argv[1]).resolve()
mainfrm = root / "src" / "interface" / "Mainfrm.cpp"
vi_locale = root / "locales" / "vi_VN.po"
for required_path in (mainfrm, vi_locale):
    if not required_path.is_file():
        raise SystemExit(f"HF24_PATCH_FAIL: missing source file: {required_path}")

text = mainfrm.read_text(encoding="utf-8")
if ICON_MARKER not in text:
    # wxTopLevelWindow::SetIcons consumes a wxIconBundle, preserving all useful
    # ICO sizes instead of forcing Windows to stretch one extracted image.
    headers = (
        "#include <wx/filename.h>\n",
        "#include <wx/iconbndl.h>\n",
        "#include <wx/image.h>\n",
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

    constructor = re.search(r"\bCMainFrame::CMainFrame\s*\(", text)
    if not constructor:
        raise SystemExit("HF24_PATCH_FAIL: CMainFrame constructor not found")

    # Skip C++ comments/strings while looking for the constructor body brace.
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
	// adapter. wxIconBundle loads ICO through wxImage. The BMP handler is always
	// registered, but the ICO handler is not guaranteed to be present. Register
	// it before AddIcon so startup never shows "No image handler for type 3
	// defined." (wxBITMAP_TYPE_ICO is bitmap type 3).
	if (!wxImage::FindHandler(wxBITMAP_TYPE_ICO)) {
		wxImage::AddHandler(new wxICOHandler);
	}

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
for required in (
    ICON_MARKER,
    "wxImage::FindHandler(wxBITMAP_TYPE_ICO)",
    "wxImage::AddHandler(new wxICOHandler)",
    "SetIcons(bridgeXIcons)",
    "BridgeX-AppIcon.ico",
):
    if required not in check:
        raise SystemExit(f"HF24_PATCH_FAIL: missing icon post-patch marker: {required}")
print("HOTFIX24_TASKBAR_ICON_PATCH=PASS")
print("HOTFIX24_ICO_IMAGE_HANDLER=PASS")

# FileZilla 3.70.6's shipped Vietnamese catalog currently renders the three
# password-storage radio choices with the same label. Patch only the extracted
# disposable upstream catalog. The pinned BridgeX Build12-Hotfix16 locale and
# source manifest remain byte-for-byte unchanged.
password_translations = {
    "Sav&e passwords": "&Lưu mật khẩu",
    "D&o not save passwords": "&Không lưu mật khẩu",
    "Sa&ve passwords protected by a master password": "Lưu mật khẩu, &bảo vệ bằng mật khẩu chính",
}

po_lines = vi_locale.read_text(encoding="utf-8").splitlines(keepends=True)
for msgid, msgstr in password_translations.items():
    needle = f'msgid "{msgid}"'
    matches = [i for i, line in enumerate(po_lines) if line.rstrip("\r\n") == needle]
    if len(matches) != 1:
        raise SystemExit(f"HF24_PATCH_FAIL: password msgid anchor count={len(matches)} msgid={msgid!r}")
    i = matches[0] + 1
    while i < len(po_lines) and not po_lines[i].startswith("msgstr "):
        if po_lines[i].startswith("msgid ") or (po_lines[i].startswith("#") and i > matches[0] + 1):
            raise SystemExit(f"HF24_PATCH_FAIL: msgstr missing for {msgid!r}")
        i += 1
    if i >= len(po_lines):
        raise SystemExit(f"HF24_PATCH_FAIL: msgstr missing for {msgid!r}")
    end = i + 1
    while end < len(po_lines) and po_lines[end].startswith('"'):
        end += 1
    po_lines[i:end] = [f'msgstr "{msgstr}"\n']

vi_locale.write_text("".join(po_lines), encoding="utf-8", newline="\n")
patched_locale = vi_locale.read_text(encoding="utf-8")
for msgid, msgstr in password_translations.items():
    block = f'msgid "{msgid}"\nmsgstr "{msgstr}"'
    if block not in patched_locale:
        raise SystemExit(f"HF24_PATCH_FAIL: password translation post-check failed: {msgid!r}")
if len(set(password_translations.values())) != 3:
    raise SystemExit("HF24_PATCH_FAIL: password translations must be distinct")

print("HOTFIX24_PASSWORD_TRANSLATIONS=PASS")
