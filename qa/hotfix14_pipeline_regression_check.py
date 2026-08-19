#!/usr/bin/env python3
"""Hotfix14 regression gates retained for dependency DB, clean upgrades, payload and locale metadata."""
from pathlib import Path
import sys
if len(sys.argv) != 2: raise SystemExit('Usage: hotfix14_pipeline_regression_check.py <kit-root>')
root=Path(sys.argv[1]).resolve()
build=(root/'scripts/build-filezilla-dark.sh').read_text(encoding='utf-8')
patch=(root/'scripts/patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
installer=(root/'installer/TNSuiteBridgeXInstaller.nsi').read_text(encoding='utf-8')
payload=(root/'qa/production_payload_check.py').read_text(encoding='utf-8')
po=(root/'locales/bridgex_vi_VN.po').read_text(encoding='utf-8')
checks=[]
def check(label,ok): ok=bool(ok); checks.append((label,ok)); print(('PASS  ' if ok else 'FAIL  ')+label)
check('No per-package pacman -Q dependency loop remains', 'pacman -Q "$pkg"' not in build)
check('Exactly one full package DB query exists in build script', build.count('pacman -Q >"$PACMAN_DB_SNAPSHOT"') == 1)
check('Package DB progress markers exist', all(x in build for x in ('DEPENDENCY_PACKAGE_DB_QA=START','DEPENDENCY_PACKAGE_DB_QA=PASS','DEPENDENCY_PACKAGE_DB_QA=FAIL')))
check('Package DB query has bounded timeout and clear timeout reason', 'timeout --foreground' in build and 'reason=TIMEOUT' in build)
check('Reused dependencies emit stable marker', 'echo "BUILD_DEPENDENCIES=REUSED"' in build)
check('No stale ID_EDIT_ASSOCIATIONS wx probe remains', 'FindWindow(XRCID("ID_EDIT_ASSOCIATIONS"))' not in build)
check('Hotfix14 extracted XRC matcher is not active in build', 'hotfix14_extracted_upstream_check.py' not in build)
check('Hotfix15 native extracted gate supersedes the disproven model', 'hotfix15_extracted_upstream_check.py' in build and 'HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS' in build)
check('Current extracted gate is SHA-postcheck and pre-patch', build.find('sha256sum --check --strict') < build.find('Hotfix15 SHA-verified native association QA') < build.find('Apply TNSuite BridgeX UI patch'))
check('Clean upgrade removes only marker-verified old install tree', 'IfFileExists "$INSTDIR\\${BRIDGEX_INSTALL_MARKER}" install_clean_verified 0' in installer and 'RMDir /r "$INSTDIR"' in installer)
check('Installer aborts rather than creating mixed-version tree', 'No mixed-version install was created.' in installer)
check('Payload checker explicitly forbids prior leaked development files', all(x in payload for x in ('SOURCE_PATCHES','BridgeX-CloseInstalled.ps1','BUILD_INFO.md','CHANGELOG.md','SOURCE_MANIFEST.txt')))
check('Locale metadata suppresses previous msgfmt header warnings', all(x in po for x in ('PO-Revision-Date:','Last-Translator:','Language-Team:')))
check('Native patcher does not depend on XRC SetTextFromOption discovery', 'control_binding_pattern = re.compile' not in patch and 'HF15_NATIVE_ASSOC_RECEIVER_DISCOVERY' in patch)
if not all(ok for _,ok in checks): print('HOTFIX14_PIPELINE_REGRESSION_QA=FAIL'); raise SystemExit(1)
print('HOTFIX14_PIPELINE_REGRESSION_QA=PASS')
