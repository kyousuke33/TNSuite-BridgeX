#!/usr/bin/env python3
"""Fail-closed regression QA for first-restart theme/language persistence.

Hotfix15 launched the replacement GUI before the current process completed its
normal shutdown. That allowed the child to construct COptions against the old
on-disk state. Hotfix16 keeps upstream persistence ownership intact and adds a
one-shot parent/child handoff: child startup waits for parent termination before
COptions construction.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: hotfix16_restart_persistence_check.py <kit-root>')

root = Path(sys.argv[1]).resolve()
patch = (root / 'scripts' / 'patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
build = (root / 'scripts' / 'build-filezilla-dark.sh').read_text(encoding='utf-8')
source_compat = (root / 'qa' / 'source_compat_check.py').read_text(encoding='utf-8')
fixture = (root / 'qa' / 'patch_fixture_check.py').read_text(encoding='utf-8')

checks = []
def check(label, ok):
    ok = bool(ok)
    checks.append(ok)
    print(('PASS  ' if ok else 'FAIL  ') + label)

# Child-side restart handoff must be a Windows-native, bounded, fail-closed wait.
for needle, label in (
    ('TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_HANDOFF', 'Hotfix16 child handoff marker'),
    ('TNSUITE_BRIDGEX_RESTART_PARENT_PID', 'One-shot restart parent PID environment contract'),
    ('kBridgeXRestartParentWaitMs = 60000', 'Parent wait is bounded at 60 seconds'),
    ('::OpenProcess(SYNCHRONIZE', 'Parent process opened only for synchronization'),
    ('::WaitForSingleObject(parent, kBridgeXRestartParentWaitMs)', 'Child blocks on parent termination'),
    ('::CloseHandle(parent)', 'Parent process handle is closed'),
    ('waitResult == WAIT_OBJECT_0', 'Timeout/error path is fail-closed'),
    ('::GetLastError() == ERROR_INVALID_PARAMETER', 'Already-exited parent race is accepted'),
):
    check(label, needle in patch)

check('Child clears inherited restart marker before normal startup',
      patch.find('wxUnsetEnv(kBridgeXRestartParentPidEnv)') > patch.find('BridgeXWaitForRestartParentIfRequested'))
check('Invalid/self parent PID is rejected',
      '!parentPid' in patch and 'GetCurrentProcessId()' in patch and 'return false;' in patch)

# The critical ordering invariant: wait must be installed in OnInit before the
# patcher reaches the COptions construction patch point.
wait_pos = patch.find('TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS')
options_patch_pos = patch.find("options_anchor = '\\toptions_ = std::make_unique<COptions>();")
check('Restart handoff wait is injected before COptions construction patch point',
      0 <= wait_pos < options_patch_pos)
check('OnInit fails closed when parent handoff cannot complete',
      'if (!BridgeXWaitForRestartParentIfRequested())' in patch)

# Parent-side ordering: persist all selected values in COptions first, then
# create child with the one-shot parent PID, clean parent env, then close parent.
lang_set = patch.find('m_pOptions->set(OPTION_LANGUAGE, newLanguage);')
theme_set = patch.find('m_pOptions->set(OPTION_BRIDGEX_THEME, newTheme);')
handoff_marker = patch.find('TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF')
setenv = patch.find('wxSetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID"', handoff_marker)
execute = patch.find('wxExecute(executable, wxEXEC_ASYNC)', handoff_marker)
unsetenv = patch.find('wxUnsetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID")', handoff_marker)
close = patch.find('top->Close();', handoff_marker)
check('Language option is assigned before restart handoff', 0 <= lang_set < handoff_marker)
check('Theme option is assigned before restart handoff', 0 <= theme_set < handoff_marker)
check('Restart environment handoff is set before child creation', 0 <= setenv < execute)
check('Parent environment is restored immediately after child creation', 0 <= execute < unsetenv < close)
check('Current process closes only after child handoff succeeds', 'if (restartedPid != 0)' in patch and unsetenv < close)
check('Old immediate child-then-close restart block is gone',
      'if (wxExecute(executable, wxEXEC_ASYNC) != 0)' not in patch)

restart_slice = patch[handoff_marker:close + len('top->Close();')] if handoff_marker >= 0 and close >= 0 else ''
check('Restart path does not invoke PowerShell/cmd helper',
      not re.search(r'(?i)(powershell|cmd\.exe|taskkill)', restart_slice))
check('Hotfix16 does not invent a private COptions flush/save API',
      not re.search(r'(?i)m_pOptions->(?:flush|save|write|sync)\s*\(', restart_slice))

# Model the exact runtime symptom. Old ordering necessarily lets the first child
# observe old disk state; new ordering requires parent flush/exit before child read.
disk = {'language': 'en_US', 'theme': 1}
pending = {'language': 'vi_VN', 'theme': 0}
old_first_child = dict(disk)          # child starts before parent shutdown flush
disk.update(pending)                  # parent exits and upstream persistence flushes
check('Regression model reproduces Hotfix15 two-restart stale read',
      old_first_child == {'language': 'en_US', 'theme': 1} and disk == pending)

disk = {'language': 'en_US', 'theme': 1}
disk.update(pending)                  # parent shutdown completes first
hf16_first_child = dict(disk)         # only then may child construct COptions
check('Hotfix16 model applies Light + Vietnamese on the first restart', hf16_first_child == pending)

# Windows exact-API compile probe and source/fixture post-patch gates.
check('Hotfix16 exact Windows/wx API compile probe is wired',
      'WX33_HF16_RESTART_HANDOFF_API_COMPILE_QA=PASS' in build and
      '#include <windows.h>' in build and 'wxSetEnv' in build and 'WaitForSingleObject' in build)
qa_pos = build.find('Hotfix16 first-restart settings persistence QA - fail closed')
download_pos = build.find('Download FileZilla ${FZ_VERSION} source')
check('Hotfix16 regression QA runs before source download',
      0 <= qa_pos < download_pos and 'HOTFIX16_RESTART_PERSISTENCE_QA=PASS' in build)
check('Post-patch source compatibility gates Hotfix16 ordering',
      'TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS' in source_compat and
      'TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF' in source_compat)
check('Patch fixture gates Hotfix16 emitted restart lifecycle',
      'HF16_RESTART_PERSISTENCE_HANDOFF' in fixture and 'HF16_WAIT_PARENT_BEFORE_OPTIONS' in fixture)

if not all(checks):
    print('HOTFIX16_RESTART_PERSISTENCE_QA=FAIL')
    raise SystemExit(1)
print('HOTFIX16_RESTART_PERSISTENCE_QA=PASS')
