#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: hotfix11_bitmap_setbitmap_check.py <kit-root>')
root = Path(sys.argv[1]).resolve()
patch = (root/'scripts/patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
build = (root/'scripts/build-filezilla-dark.sh').read_text(encoding='utf-8')
fixture = (root/'qa/patch_fixture_check.py').read_text(encoding='utf-8')
hf8qa = (root/'qa/hotfix8_runtime_product_check.py').read_text(encoding='utf-8')
checks=[]

def check(label, ok):
    ok=bool(ok); checks.append(ok); print(('PASS  ' if ok else 'FAIL  ')+label)

check('Hotfix11 safe SetBitmap marker', 'TNSUITE_BRIDGEX_BUILD12_HF11_SAFE_BITMAP_BUNDLE' in patch)
check('Old wxNullBitmap constructor blocker removed', 'PATCH_FAIL: no wxStaticBitmap constructor using wxNullBitmap' not in patch and 'staticbitmap_pattern' not in patch)
check('SetBitmap call inventory exists', 'hf11_call_pattern' in patch and 'SetBitmap' in patch and 'hf11_staticbitmap_names' in patch)
check('Known wxStaticBitmap receiver inventory exists', 'wxStaticBitmap' in patch and 'hf11_decl_patterns' in patch)
check('Statusbar fallback is narrowly scoped', 'candidate.name.lower() != "statusbar.cpp"' in patch)
check('Bundle validity guard exists', 'bundle.IsOk()' in patch and 'wxBitmapBundle::FromBitmap(wxBitmap(1, 1))' in patch)
check('Bitmap validity guard exists', 'bitmap.IsOk()' in patch and 'return wxBitmap(1, 1);' in patch)
check('Direct bitmap bundle headers emitted', '#include <wx/bitmap.h>' in patch and '#include <wx/bmpbndl.h>' in patch)
check('Zero-candidate result does not block build', 'STATUSBITMAP_HF11_PATCH_APPLIED=NONE' in patch and 'if not hf11_setbitmap_patched:' in patch)
check('Upstream inventory markers emitted', all(x in patch for x in ('HF11_UPSTREAM_STATICBITMAP_DECLS=', 'HF11_UPSTREAM_SETBITMAP_CALLS=', 'HF11_UPSTREAM_BITMAP_INVENTORY_QA=PASS')))
check('No global wx assert suppression', not any(x in patch for x in ('wxDisableAsserts','SetAssertHandler','wxSetAssertHandler')))
check('Exact wx safe-bitmap API probe wired', 'WX33_HF11_SAFE_BITMAP_API_COMPILE_QA=PASS' in build and '<wx/bmpbndl.h>' in build and 'BridgeXSafeStaticBitmap' in build)
check('Dynamic touched-TU compile gate wired', 'HF11_STATICBITMAP_PATCHED_TUS=' in build and 'HF11_STATICBITMAP_PATCHED_TU_COMPILE_QA=PASS' in build)
check('Dynamic compile allows NONE', "HF11_STATICBITMAP_PATCHED_TUS=NONE" in build and '(( ${#HF11_BITMAP_OBJECTS[@]} > 0 ))' in build)
check('Fixture models SetBitmap instead of wxNullBitmap constructor', 'm_security->SetBitmap(bundle);' in fixture and 'auto* icon = new wxStaticBitmap' not in fixture)
check('Fixture requires guarded SetBitmap', 'BridgeXSafeStaticBitmap(bundle)' in fixture and 'TNSUITE_BRIDGEX_BUILD12_HF11_SAFE_BITMAP_BUNDLE' in fixture)
check('Hotfix8 regression QA no longer asserts disproven constructor model', 'TNSUITE_BRIDGEX_BUILD12_HF8_VALID_STATIC_BITMAP' not in hf8qa and r'new\s+wxStaticBitmap' not in hf8qa)
check('Current build runs Hotfix11 gate before source download', 'hotfix11_bitmap_setbitmap_check.py' in build and build.find('Hotfix11 bitmap SetBitmap guard QA') < build.find('Download FileZilla ${FZ_VERSION} source'))
check('Hotfix11 QA report retained in external evidence', 'hotfix11-bitmap-setbitmap-report.txt' in build and 'QA_EVIDENCE="$DIST/${BUILD_NAME}-QA-Evidence"' in build)

if not all(checks):
    print('HOTFIX11_BITMAP_SETBITMAP_QA=FAIL')
    raise SystemExit(1)
print('HOTFIX11_BITMAP_SETBITMAP_QA=PASS')
