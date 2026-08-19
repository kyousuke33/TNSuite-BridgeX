#!/usr/bin/env python3
"""Fail-closed header-completeness regression QA for Build12-Hotfix8."""
from pathlib import Path
import subprocess, sys, tempfile
if len(sys.argv) != 2:
    raise SystemExit('Usage: hotfix7_staticbox_header_check.py <kit-root>')
root=Path(sys.argv[1]).resolve()
patch=(root/'scripts/patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
fixture=(root/'qa/patch_fixture_check.py').read_text(encoding='utf-8')
build=(root/'scripts/build-filezilla-dark.sh').read_text(encoding='utf-8')
checks=[]
def check(label,ok):
    ok=bool(ok); checks.append((label,ok)); print(('PASS  ' if ok else 'FAIL  ')+label)
check('Hotfix7 complete-type marker', 'TNSUITE_BRIDGEX_BUILD12_HF7_STATICBOX_COMPLETE_TYPE' in patch)
check('Patcher explicitly emits wx/statbox.h', '#include <wx/statbox.h>' in patch)
check('Patcher retains explicit wx/settings.h', '#include <wx/settings.h>' in patch)
check('Fixture models Hotfix6 omission', '#include "dialogex.h"\n#include <wx/settings.h>\nstd::tuple' in fixture and '#include "dialogex.h"\n#include <wx/statbox.h>\nstd::tuple' not in fixture)
check('Fixture asserts emitted wx/statbox.h', 'Hotfix7 did not emit explicit wx/statbox.h' in fixture)
check('Windows staticbox probe uses direct headers', 'WX_STATICBOX_PROBE=' in build and '#include <wx/sizer.h>' in build and '#include <wx/statbox.h>' in build and 'WX33_STATICBOX_DIRECT_HEADER_QA=PASS' in build)
check('Windows Hotfix4 probe uses direct headers', 'WX_HF4_PROBE=' in build and 'WX33_HF4_DIRECT_HEADER_QA=PASS' in build)
with tempfile.TemporaryDirectory(prefix='bridgex-hf7-header-') as td:
    td=Path(td); wx=td/'wx'; wx.mkdir()
    (wx/'sizer.h').write_text('#pragma once\nclass wxStaticBox;\nclass wxStaticBoxSizer { public: wxStaticBox* GetStaticBox(); };\n',encoding='utf-8')
    (wx/'settings.h').write_text('#pragma once\nstruct wxColour {};\nenum wxSystemColour { wxSYS_COLOUR_WINDOWTEXT };\nstruct wxSystemSettings { static wxColour GetColour(wxSystemColour) { return {}; } };\n',encoding='utf-8')
    (wx/'statbox.h').write_text('#pragma once\n#include <wx/settings.h>\nclass wxStaticBox { public: void SetForegroundColour(wxColour) {} };\n',encoding='utf-8')
    body='\nvoid probe(wxStaticBoxSizer* boxSizer) {\n    boxSizer->GetStaticBox()->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));\n}\n'
    neg=td/'negative.cpp'; pos=td/'positive.cpp'
    neg.write_text('#include <wx/sizer.h>\n#include <wx/settings.h>\n'+body,encoding='utf-8')
    pos.write_text('#include <wx/sizer.h>\n#include <wx/statbox.h>\n#include <wx/settings.h>\n'+body,encoding='utf-8')
    cmd=['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsyntax-only','-I',str(td)]
    n=subprocess.run(cmd+[str(neg)],text=True,capture_output=True)
    p=subprocess.run(cmd+[str(pos)],text=True,capture_output=True)
    check('Missing statbox header reproduces incomplete-type failure', n.returncode != 0 and ('incomplete type' in n.stderr or 'forward declaration' in n.stderr))
    check('Explicit statbox header resolves member access', p.returncode == 0)
    if p.returncode:
        print('POSITIVE_PROBE_STDERR:'); print(p.stderr)
    if n.returncode == 0:
        print('NEGATIVE_PROBE_UNEXPECTEDLY_COMPILED')
if not all(ok for _,ok in checks):
    print('HOTFIX7_STATICBOX_HEADER_QA=FAIL'); raise SystemExit(1)
print('HOTFIX7_STATICBOX_HEADER_QA=PASS')
