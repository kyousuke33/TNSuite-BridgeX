#!/usr/bin/env python3
"""Hotfix15 regression gate: native FileZilla association data path, not XRC helper guesses."""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 2:
    raise SystemExit('Usage: hotfix15_native_assoc_regression_check.py <kit-root>')
root = Path(sys.argv[1]).resolve()
build = (root / 'scripts/build-filezilla-dark.sh').read_text(encoding='utf-8')
patch = (root / 'scripts/patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
checker = root / 'qa/hotfix15_extracted_upstream_check.py'
checks = []

def check(label, ok):
    ok = bool(ok); checks.append((label, ok)); print(('PASS  ' if ok else 'FAIL  ') + label)

def run_source(source):
    with tempfile.TemporaryDirectory(prefix='bridgex-hf15-upstream-') as td:
        p = Path(td) / 'src/interface/settings'
        p.mkdir(parents=True)
        (p / 'optionspage_edit_associations.cpp').write_text(source, encoding='utf-8')
        cp = subprocess.run([sys.executable, str(checker), td], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return cp.returncode, cp.stdout

native = r'''#include "optionspage_edit_associations.h"
bool COptionsPageEditAssociations::LoadPage()
{
    assocs_->ChangeValue(m_pOptions->get_string(OPTION_EDIT_CUSTOMASSOCIATIONS));
    return true;
}
bool COptionsPageEditAssociations::Validate()
{
    wxString associations = assocs_->GetValue() + _T("\n");
    if (!ProgramExists(associations)) {
        wxString error = _("Associated program not found:");
        return false;
    }
    return true;
}
bool COptionsPageEditAssociations::SavePage()
{
    m_pOptions->set(OPTION_EDIT_CUSTOMASSOCIATIONS, assocs_->GetValue().ToStdWstring());
    return true;
}
'''
rc, out = run_source(native)
check('Checker accepts observed FileZilla 3.70.6 native association data path', rc == 0 and 'HOTFIX15_EXTRACTED_ASSOC_RECEIVER=assocs_' in out and 'HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS' in out)

indirect_validate = native.replace('wxString associations = assocs_->GetValue() + _T("\\n");', 'wxString associations = GetAssociationsForValidation();')
rc, out = run_source(indirect_validate)
check('Checker does not guess how Validate reads the native editor', rc == 0 and 'HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS' in out)

mismatch = native.replace('assocs_->GetValue().ToStdWstring()', 'other_->GetValue().ToStdWstring()')
rc, out = run_source(mismatch)
check('Checker rejects mismatched Load/Save native receivers', rc != 0 and 'HOTFIX15_EXTRACTED_UPSTREAM_QA=FAIL' in out)

legacy = r'''#include "optionspage_edit_associations.h"
bool COptionsPageEditAssociations::LoadPage(){ SetTextFromOption(XRCID("ID_ASSOCIATIONS"), OPTION_EDIT_CUSTOMASSOCIATIONS); return true; }
bool COptionsPageEditAssociations::Validate(){ wxString a = GetText(XRCID("ID_ASSOCIATIONS")); return true; }
bool COptionsPageEditAssociations::SavePage(){ SetOptionFromText(XRCID("ID_ASSOCIATIONS"), OPTION_EDIT_CUSTOMASSOCIATIONS); return true; }
'''
rc, out = run_source(legacy)
check('Checker rejects obsolete XRC-helper-only source model', rc != 0 and 'HOTFIX15_EXTRACTED_UPSTREAM_QA=FAIL' in out)

check('Patcher discovers native ChangeValue/get_string receiver', 'HF15_NATIVE_ASSOC_RECEIVER_DISCOVERY' in patch and 'native_load_pattern = re.compile' in patch)
check('Patcher discovers native m_pOptions set/GetValue persistence receiver', 'native_save_pattern = re.compile' in patch and 'ToStdWstring' in patch)
check('Patcher no longer discovers association through SetTextFromOption', 'control_binding_pattern = re.compile' not in patch)
check('Patcher repairs native control at Load/Validate/Save boundaries without replacing persistence', all(x in patch for x in (
    'HF15_NATIVE_LOAD_REPAIR', 'HF15_NATIVE_VALIDATE_REPAIR', 'HF15_NATIVE_PERSIST_REPAIR',
    'upstream native association persistence was not preserved')))
check('Hotfix15 extracted gate is SHA-postcheck and pre-patch',
      build.find('sha256sum --check --strict') < build.find('Hotfix15 SHA-verified native association QA') < build.find('Apply TNSuite BridgeX UI patch'))
check('Hotfix14 extracted matcher is no longer active in build', 'Hotfix14 SHA-verified extracted upstream association QA' not in build)

if not all(ok for _, ok in checks):
    print('HOTFIX15_NATIVE_ASSOC_REGRESSION_QA=FAIL'); raise SystemExit(1)
print('HOTFIX15_NATIVE_ASSOC_REGRESSION_QA=PASS')
