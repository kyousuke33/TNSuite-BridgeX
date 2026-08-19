#!/usr/bin/env python3
"""Static regression checks for the narrowly scoped Build12-Hotfix4 runtime fixes."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: hotfix4_runtime_regression_check.py <kit-root>")
root = Path(sys.argv[1]).resolve()
patcher = (root / "scripts/patch_tnsuite_bridgex.py").read_text(encoding="utf-8")
build = (root / "scripts/build-filezilla-dark.sh").read_text(encoding="utf-8")

checks = []
def check(label, ok):
    ok = bool(ok)
    checks.append((label, ok))
    print(("PASS  " if ok else "FAIL  ") + label)

# Source-scope invariants: keep the migration narrow and the original validator alive.
check("Store Notepad value-repair marker", "TNSUITE_BRIDGEX_BUILD12_HF12_STORE_NOTEPAD_VALUE_REPAIR" in patcher)
check("Store Notepad pattern is specific", "microsoft.windowsnotepad_" in patcher.lower() and r'\\notepad\\notepad.exe' in patcher)
check("Repair discovers actual native association receiver", 'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_ASSOC_RECEIVER_DISCOVERY' in patcher and 'OPTION_EDIT_CUSTOMASSOCIATIONS' in patcher)
check("Repair covers validation and persistence", 'TNSUITE_BRIDGEX_BUILD12_HF13_VALIDATE_REPAIRED_ASSOCIATIONS' in patcher and 'TNSUITE_BRIDGEX_BUILD12_HF13_PERSIST_REPAIRED_ASSOCIATIONS' in patcher)
check("Obsolete FindWindow repair is absent", 'RepairStaleStoreNotepadAssociation(wxWindow* page)' not in patcher and 'auto* editor = wxDynamicCast' not in patcher)
check("Stable system Notepad target", r'System32\\notepad.exe' in patcher)
check("Repair requires stable Notepad to exist", "stableNotepad.FileExists()" in patcher)
check("Existing association validation and native persistence preserved", 'stableNotepad.FileExists()' in patcher and 'upstream native association persistence was not preserved' in patcher and 'upstream missing-program validation was not preserved' in patcher)
check("Shared static-box caption marker", "TNSUITE_BRIDGEX_BUILD12_HF4_STATICBOX_TEXT" in patcher)
check("Static-box uses system window text", "wxSYS_COLOUR_WINDOWTEXT" in patcher)
check("Shared file-list surface marker", "TNSUITE_BRIDGEX_BUILD12_HF4_LIST_SURFACE" in patcher)
check("File-list uses system window/windowtext", "wxSYS_COLOUR_WINDOW" in patcher and "wxSYS_COLOUR_WINDOWTEXT" in patcher)
for obj in (
    "filezilla-dialogex.o",
    "filezilla-filelistctrl.o",
    "settings/filezilla-optionspage_edit_associations.o",
):
    check(f"Windows compile preflight covers {obj}", obj in build)

# Python model of the C++ line surgery, exercised against the exact runtime shape
# supplied in the Hotfix3 screenshot/evidence. This is not a C++/Windows compile.
def repair_line(line: str, stable: str = r"C:\WINDOWS\System32\notepad.exe") -> str:
    lower = line.lower()
    store_marker = r"\windowsapps\microsoft.windowsnotepad_"
    exe_suffix = r"\notepad\notepad.exe"
    marker = lower.find(store_marker)
    suffix = lower.find(exe_suffix, marker if marker >= 0 else 0)
    if marker < 0 or suffix < 0:
        return line
    quote = line.rfind('"', 0, marker + 1)
    if quote >= 0:
        path_start = quote + 1
    else:
        space = line.rfind(' ', 0, marker + 1)
        tab = line.rfind('\t', 0, marker + 1)
        path_start = max(space + 1 if space >= 0 else 0, tab + 1 if tab >= 0 else 0)
    path_end = suffix + len(exe_suffix)
    return line[:path_start] + stable + line[path_end:]

runtime_line = r'txt "C:\Program Files\WindowsApps\Microsoft.WindowsNotepad_11.2604.5.0_x64__8wekyb3d8bbwe\Notepad\Notepad.exe" %f'
expected = r'txt "C:\WINDOWS\System32\notepad.exe" %f'
check("Exact stale Store Notepad line migrates", repair_line(runtime_line) == expected)
check("Trailing %f is preserved", repair_line(runtime_line).endswith('" %f'))
valid_vscode = r'json "C:\Users\admin\AppData\Local\Programs\Microsoft VS Code\Code.exe" %f'
check("Unrelated valid editor remains unchanged", repair_line(valid_vscode) == valid_vscode)
arbitrary_missing = r'txt "C:\Missing\SomeEditor.exe" %f'
check("Arbitrary missing editor is not rewritten", repair_line(arbitrary_missing) == arbitrary_missing)

if not all(ok for _, ok in checks):
    print("HOTFIX4_RUNTIME_REGRESSION_QA=FAIL")
    raise SystemExit(1)
print("HOTFIX4_RUNTIME_REGRESSION_QA=PASS")
