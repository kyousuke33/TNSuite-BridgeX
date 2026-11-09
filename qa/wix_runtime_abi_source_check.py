#!/usr/bin/env python3
"""Regression guard for reviewed WiX payload ABI pairs and exact-legacy flow."""
from pathlib import Path
path = Path(__file__).resolve().parents[1] / ".release/build-wix-installer.ps1"
text = path.read_text(encoding="utf-8")
required = (
    "libfilezilla-58.dll", "libfzssh-13.0.0.dll",
    "libfilezilla-60.dll", "libfzssh-16.0.0.dll",
    "RUNTIME_ABI_DLL_PAIR_UNREVIEWED", "RUNTIME_ABI_DLL_COUNT_FAIL",
    "RUNTIME_ABI_DLL_PAIR=PASS", "$libfz.Count -ne 1",
    "$libssh.Count -ne 1", "Get-ChildItem -LiteralPath $bin -File"
)
for marker in required:
    if marker not in text:
        raise SystemExit(f"WIX_RUNTIME_ABI_SOURCE_QA=FAIL marker={marker}")
print("WIX_RUNTIME_ABI_SOURCE_QA=PASS")
