#!/usr/bin/env python3
"""Regression QA preserving Hotfix13 repair intent through Hotfix15 native source discovery."""
from pathlib import Path
import sys
if len(sys.argv) != 2: raise SystemExit('Usage: hotfix13_assoc_upstream_check.py <kit-root>')
root=Path(sys.argv[1]).resolve()
patch=(root/'scripts/patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
fixture=(root/'qa/patch_fixture_check.py').read_text(encoding='utf-8')
build=(root/'scripts/build-filezilla-dark.sh').read_text(encoding='utf-8')
checks=[]
def check(label,ok): ok=bool(ok); checks.append((label,ok)); print(('PASS  ' if ok else 'FAIL  ')+label)
check('Hotfix13 repair ownership marker retained', 'TNSUITE_BRIDGEX_BUILD12_HF13_ASSOC_CONTROL_DISCOVERY' in patch)
check('Association receiver is discovered from native OPTION_EDIT_CUSTOMASSOCIATIONS data path', 'HF15_NATIVE_ASSOC_RECEIVER_DISCOVERY' in patch and 'native_load_pattern = re.compile' in patch and 'native_save_pattern = re.compile' in patch)
check('No hard-coded Hotfix12 ID_EDIT_ASSOCIATIONS control read remains', 'GetText(XRCID(\"ID_EDIT_ASSOCIATIONS\"))' not in patch and 'FindWindow(XRCID(\"ID_EDIT_ASSOCIATIONS\"))' not in patch)
check('Validate repair ownership is retained', 'TNSUITE_BRIDGEX_BUILD12_HF13_VALIDATE_REPAIRED_ASSOCIATIONS' in patch and 'HF15_NATIVE_VALIDATE_REPAIR' in patch)
check('Save repair ownership is retained on native persistence path', 'TNSUITE_BRIDGEX_BUILD12_HF13_PERSIST_REPAIRED_ASSOCIATIONS' in patch and 'HF15_NATIVE_PERSIST_REPAIR' in patch)
check('Discovered native receiver is emitted to build log', 'EDIT_ASSOC_HF15_RECEIVER=' in patch)
check('Fixture models observed native LoadPage binding', 'assocs_->ChangeValue(m_pOptions->get_string(OPTION_EDIT_CUSTOMASSOCIATIONS));' in fixture)
check('Fixture models observed native SavePage persistence', 'm_pOptions->set(OPTION_EDIT_CUSTOMASSOCIATIONS, assocs_->GetValue().ToStdWstring());' in fixture)
check('Fixture provides a Validate body for native pre-validation injection', 'bool COptionsPageEditAssociations::Validate()' in fixture)
check('Fixture rejects stale ID_EDIT_ASSOCIATIONS', "if 'ID_EDIT_ASSOCIATIONS' in emitted_assoc" in fixture)
check('Hotfix13 intent gate remains pre-download', 'hotfix13_assoc_upstream_check.py' in build and build.find('HOTFIX13_ASSOC_UPSTREAM_QA=PASS') < build.find('Download FileZilla ${FZ_VERSION} source'))
check('Hotfix15 SHA-verified native extracted gate runs before BridgeX patch', 'hotfix15_extracted_upstream_check.py' in build and build.find('HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS') > build.find('sha256sum --check --strict') and build.find('HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS') < build.find('Apply TNSuite BridgeX UI patch'))
check('Patched association TU remains in Windows compile preflight', 'settings/filezilla-optionspage_edit_associations.o' in build)
if not all(ok for _,ok in checks): print('HOTFIX13_ASSOC_UPSTREAM_QA=FAIL'); raise SystemExit(1)
print('HOTFIX13_ASSOC_UPSTREAM_QA=PASS')
