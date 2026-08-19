#!/usr/bin/env python3
"""Fail-closed regression QA for the Hotfix5 wxStaticBoxSizer type error.

This intentionally compiles both a positive and a negative C++ probe. The
negative probe reproduces the exact Hotfix5 failure class: calling
SetForegroundColour directly on wxStaticBoxSizer. The positive probe requires
colouring the owned wxStaticBox through GetStaticBox().
"""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 2:
    raise SystemExit("Usage: hotfix6_staticbox_compile_check.py <kit-root>")
root = Path(sys.argv[1]).resolve()
patcher = (root / "scripts/patch_tnsuite_bridgex.py").read_text(encoding="utf-8")
fixture = (root / "qa/patch_fixture_check.py").read_text(encoding="utf-8")
build = (root / "scripts/build-filezilla-dark.sh").read_text(encoding="utf-8")

checks = []
def check(label, ok):
    ok = bool(ok)
    checks.append((label, ok))
    print(("PASS  " if ok else "FAIL  ") + label)

check("Hotfix6 target marker", "TNSUITE_BRIDGEX_BUILD12_HF6_STATICBOX_TARGET" in patcher)
check("Matcher targets wxStaticBoxSizer token exactly", r"new\s+wxStaticBoxSizer" in patcher)
check("Colour call uses owned wxStaticBox", "GetStaticBox()->SetForegroundColour" in patcher)
check("Patcher does not directly colour static-box sizer", "staticbox_sizer_var}->SetForegroundColour" not in patcher)
check("Realistic fixture models nested wxStaticBoxSizer/wxStaticBox", "auto boxSizer = new wxStaticBoxSizer(" in fixture and "new wxStaticBox(" in fixture)
check("Fixture rejects direct sizer colour call", "still calls SetForegroundColour on wxStaticBoxSizer" in fixture)
check("Windows exact-wx API probe includes GetStaticBox", "bridgex_wx33_staticbox_probe" in build and "GetStaticBox()" in build)
check("Windows exact-wx probe covers Hotfix4 controls", "bridgex_wx33_hf4_controls_probe" in build and "WX33_HF4_CONTROL_API_COMPILE_QA=PASS" in build)

compiler = "g++"
base = r'''
struct wxColour {};
enum wxSystemColour { wxSYS_COLOUR_WINDOWTEXT };
struct wxSystemSettings { static wxColour GetColour(wxSystemColour) { return {}; } };
struct wxStaticBox { void SetForegroundColour(wxColour) {} };
struct wxStaticBoxSizer {
    wxStaticBox box;
    wxStaticBox* GetStaticBox() { return &box; }
};
'''
positive = base + r'''
void probe(wxStaticBoxSizer* boxSizer) {
    boxSizer->GetStaticBox()->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));
}
int main() { wxStaticBoxSizer s; probe(&s); }
'''
negative = base + r'''
void probe(wxStaticBoxSizer* boxSizer) {
    boxSizer->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));
}
int main() { wxStaticBoxSizer s; probe(&s); }
'''
with tempfile.TemporaryDirectory(prefix="bridgex-hf6-staticbox-") as td:
    td = Path(td)
    pos = td / "positive.cpp"
    neg = td / "negative.cpp"
    pos.write_text(positive, encoding="utf-8")
    neg.write_text(negative, encoding="utf-8")
    p = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-fsyntax-only", str(pos)], text=True, capture_output=True)
    n = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-fsyntax-only", str(neg)], text=True, capture_output=True)
    check("Positive C++ type probe compiles", p.returncode == 0)
    check("Hotfix5 direct-sizer regression probe is rejected", n.returncode != 0 and "SetForegroundColour" in n.stderr)
    if p.returncode != 0:
        print("POSITIVE_PROBE_STDERR:")
        print(p.stderr)
    if n.returncode == 0:
        print("NEGATIVE_PROBE_UNEXPECTEDLY_COMPILED")

if not all(ok for _, ok in checks):
    print("HOTFIX6_STATICBOX_COMPILE_QA=FAIL")
    raise SystemExit(1)
print("HOTFIX6_STATICBOX_COMPILE_QA=PASS")
