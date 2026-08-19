#!/usr/bin/env python3
"""Retained fail-closed checks for the Hotfix5 multiline patch-anchor repair."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: hotfix5_patch_anchor_check.py <kit-root>")
root = Path(sys.argv[1]).resolve()
patcher = (root / "scripts/patch_tnsuite_bridgex.py").read_text(encoding="utf-8")
fixture = (root / "qa/patch_fixture_check.py").read_text(encoding="utf-8")

checks = []
def check(label, ok):
    ok = bool(ok)
    checks.append((label, ok))
    print(("PASS  " if ok else "FAIL  ") + label)

check("Hotfix5 structural static-box marker", "TNSUITE_BRIDGEX_BUILD12_HF5_STATICBOX_STRUCTURAL_MATCH" in patcher)
check("Matcher scopes to createStatBox", "factory_pos = dialogex_text.find('DialogLayout::createStatBox')" in patcher)
check("Matcher no longer requires single physical line", r"new wxStaticBox\\([^\\n]+\\)" not in patcher)
check("Matcher recovers assigned variable", "assigned variable not found" in patcher and "var_match" in patcher)
check("Matcher fails closed on missing terminator", "construction terminator not found" in patcher)
check("Explicit wx settings include", "#include <wx/settings.h>" in patcher)
check("Fixture contains multiline static-box construction", "auto boxSizer = new wxStaticBoxSizer(\n" in fixture and "new wxStaticBox(\n" in fixture)
check("Fixture asserts Hotfix5 emitted marker", "Hotfix5 structural static-box marker missing from emitted dialogex.cpp" in fixture)

if not all(ok for _, ok in checks):
    print("HOTFIX5_PATCH_ANCHOR_QA=FAIL")
    raise SystemExit(1)
print("HOTFIX5_PATCH_ANCHOR_QA=PASS")
