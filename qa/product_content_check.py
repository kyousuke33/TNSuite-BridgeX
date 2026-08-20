#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: product_content_check.py <kit-root>')
root=Path(sys.argv[1]).resolve()
checks=[]

def check(label, ok):
    ok=bool(ok); checks.append((label,ok)); print(('PASS  ' if ok else 'FAIL  ')+label)

patch=(root/'scripts/patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
po=(root/'locales/bridgex_vi_VN.po').read_text(encoding='utf-8')
help_html=(root/'docs/BridgeX-Help.html').read_text(encoding='utf-8')
bug_html=(root/'docs/BridgeX-Report-Bug.html').read_text(encoding='utf-8')
installer=(root/'installer/TNSuiteBridgeXInstaller.nsi').read_text(encoding='utf-8')
readme=(root/'README.md').read_text(encoding='utf-8')
wrapper=(root/'Build-TNSuiteBridgeX.ps1').read_text(encoding='utf-8')
build_cmd=(root/'Build.cmd').read_text(encoding='utf-8')
build_sh=(root/'scripts/build-filezilla-dark.sh').read_text(encoding='utf-8')

check('Explicit RGB palette fix', 'wxColour(15, 23, 36)' in patch and 'wxColour(14, 94, 168)' in patch)
# Old strings may appear as exact replacement anchors in the patcher, but actual
# emitted dark-code must not contain the old one-argument web-style constructors.
dark_section=patch.split('dark_code = r\'\'\'',1)[1].split("'''",1)[0] if "dark_code = r'''" in patch else ''
check('No web-hex wxColour in emitted dark palette', re.search(r'wxColour\(0x[0-9A-Fa-f]{6}\)', dark_section) is None)
check('Light and Dark appearance modes', 'DarkMode_Always' in patch and 'SetAppearance(wxApp::Appearance::Light)' in patch and 'DarkMode_Never' not in patch and 'OPTION_BRIDGEX_THEME' in patch)
check('Language moved into Interface', 'TNSUITE_BRIDGEX_BUILD12_LANGUAGE_IN_INTERFACE' in patch and 'English' in patch and 'Vietnamese' in patch)
check('Welcome is BridgeX-owned', 'Welcome to TNSuite BridgeX' in patch and 'TNSUITE_BRIDGEX_BUILD12_WELCOME' in patch)
check('About uses TNSuite homepage', 'https://tnsuite.com/' in patch)
check('Local Help actions', 'BridgeX-Help.html' in patch and 'BridgeX-Report-Bug.html' in patch)
check('Local Help has no upstream support URL', 'filezilla-project.org' not in help_html.lower() and 'filezilla-project.org' not in bug_html.lower())
po_header='\n'.join(po.splitlines()[:16])
check('Vietnamese catalog identity', r'"Language: vi_VN\n"' in po_header and r'"Project-Id-Version: TNSuite BridgeX 0.5 Build12-Hotfix16\n"' in po_header)
check('Vietnamese PO header newline escaping', r'\\n' not in po_header and r'"Content-Type: text/plain; charset=UTF-8\n"' in po_header and r'"Content-Transfer-Encoding: 8bit\n"' in po_header)
check('Early BridgeX locale fail-closed gates', 'bridgex_locale_source_check.py' in build_sh and 'BRIDGEX_VI_LOCALE_EARLY_MSGFMT_QA=PASS' in build_sh and build_sh.find('BridgeX Vietnamese locale early msgfmt probe') < build_sh.find('Download FileZilla ${FZ_VERSION} source'))
for msgid in ('Appearance','&Language:','Vietnamese','&Theme:','Light','Dark','Secure Transfer & Automation','Welcome to TNSuite BridgeX','&Getting help...','&Report a bug...'):
    check(f'Vietnamese translation entry: {msgid}', f'msgid "{msgid}"' in po)
check('Installer Build12-Hotfix16 identity', '!define PRODUCT_VERSION "0.5-Build12-Hotfix16"' in installer and 'VIProductVersion "0.5.12.16"' in installer)
check('README Build12-Hotfix16 identity', 'v0.5 Build12-Hotfix16' in readme and 'Build11-Hotfix2' not in readme)
check('PowerShell wrapper Build12-Hotfix16 identity', "TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full" in wrapper)
check('Runner path is internally consistent', wrapper.count('tnsuite-bridgex-build12-hotfix16-runner.sh') == 2 and 'tnsuite-bridgex-build12-runner.sh' not in wrapper)
check('Build.cmd failure log identity', 'TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full-compile.log' in build_cmd)
check('Hotfix12 stale Store Notepad value repair', 'TNSUITE_BRIDGEX_BUILD12_HF12_STORE_NOTEPAD_VALUE_REPAIR' in patch and 'microsoft.windowsnotepad_' in patch.lower() and r'System32\\notepad.exe' in patch)
check('Hotfix15 discovers and repairs native association data path', all(x in patch for x in ('TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_ASSOC_RECEIVER_DISCOVERY','native_load_pattern = re.compile','native_save_pattern = re.compile','HF15_NATIVE_LOAD_REPAIR','HF15_NATIVE_VALIDATE_REPAIR','HF15_NATIVE_PERSIST_REPAIR')) and 'control_binding_pattern = re.compile' not in patch)
check('Hotfix12/15 keeps association validation fail-closed', 'stableNotepad.FileExists()' in patch and 'upstream missing-program validation was not preserved' in patch)
check('Hotfix4 shared static-box text fix', 'TNSUITE_BRIDGEX_BUILD12_HF4_STATICBOX_TEXT' in patch and 'wxSYS_COLOUR_WINDOWTEXT' in patch)
check('Hotfix5 structural static-box anchor retained', 'TNSUITE_BRIDGEX_BUILD12_HF5_STATICBOX_STRUCTURAL_MATCH' in patch and 'construction terminator not found' in patch)
check('Hotfix6 static-box type correction', 'TNSUITE_BRIDGEX_BUILD12_HF6_STATICBOX_TARGET' in patch and r'new\s+wxStaticBoxSizer' in patch and 'GetStaticBox()->SetForegroundColour' in patch and 'staticbox_sizer_var}->SetForegroundColour' not in patch)
check('Hotfix6 compile regression gate wired', 'hotfix6_staticbox_compile_check.py' in build_sh and 'HOTFIX6_STATICBOX_COMPILE_QA=PASS' in build_sh and 'WX33_STATICBOX_API_COMPILE_QA=PASS' in build_sh and 'WX33_HF4_CONTROL_API_COMPILE_QA=PASS' in build_sh)
check('Hotfix7 explicit static-box complete-type header', 'TNSUITE_BRIDGEX_BUILD12_HF7_STATICBOX_COMPLETE_TYPE' in patch and '#include <wx/statbox.h>' in patch)
check('Hotfix7 header-completeness gate wired', 'hotfix7_staticbox_header_check.py' in build_sh and 'HOTFIX7_STATICBOX_HEADER_QA=PASS' in build_sh and 'WX33_STATICBOX_DIRECT_HEADER_QA=PASS' in build_sh and 'WX33_HF4_DIRECT_HEADER_QA=PASS' in build_sh)
check('Hotfix7 file-list direct settings header', 'first_include = re.search' in patch and "'#include <wx/settings.h>\\n' + filelist_text" in patch)
check('Hotfix4 shared file-list surface fix', 'TNSUITE_BRIDGEX_BUILD12_HF4_LIST_SURFACE' in patch and 'wxSYS_COLOUR_WINDOW' in patch and 'wxSYS_COLOUR_WINDOWTEXT' in patch)
check('Hotfix4 patched TU compile preflight', all(x in build_sh for x in ('filezilla-dialogex.o','filezilla-filelistctrl.o','settings/filezilla-optionspage_edit_associations.o')))
check('Hotfix8 restart CTA', 'TNSUITE_BRIDGEX_BUILD12_HF8_RESTART_CTA' in patch and 'SetYesNoLabels(_("Restart now"), _("Later"))' in patch)
check('Hotfix8 restart translations', all(x in po for x in ('msgid "Restart now"','msgstr "Khởi động ngay"','msgid "Later"','msgstr "Để sau"')))
check('Hotfix11 SetBitmap validity guard without assert suppression', 'TNSUITE_BRIDGEX_BUILD12_HF11_SAFE_BITMAP_BUNDLE' in patch and 'bundle.IsOk()' in patch and 'bitmap.IsOk()' in patch and not any(x in patch for x in ('wxDisableAsserts','SetAssertHandler','wxSetAssertHandler')))
check('Hotfix8 verified uninstall cleanup', 'BRIDGEX_INSTALL_MARKER' in installer and 'RMDir /r /REBOOTOK "$INSTDIR"' in installer and 'BridgeX-CloseInstalled.ps1' not in installer)
check('Hotfix8 branded setup/uninstall assets', all((root/'installer'/x).is_file() for x in ('BridgeX-Setup-Sidebar.bmp','BridgeX-Setup-Header.bmp')) and 'MUI_UNWELCOMEFINISHPAGE_BITMAP' in installer)
check('Hotfix8 runtime QA retained with Hotfix11 bitmap probes', 'hotfix8_runtime_product_check.py' in build_sh and 'HOTFIX8_RUNTIME_PRODUCT_QA=PASS' in build_sh and 'WX33_HF11_SAFE_BITMAP_API_COMPILE_QA=PASS' in build_sh and 'WX33_HF8_RESTART_CTA_API_COMPILE_QA=PASS' in build_sh and 'HF11_STATICBITMAP_PATCHED_TU_COMPILE_QA=PASS' in build_sh)
check('Hotfix9-16 build-time Python is stdlib-only', 'hotfix9_qa_dependency_check.py' in build_sh and 'HOTFIX9_QA_DEPENDENCY_QA=PASS' in build_sh and 'from PIL import' not in (root/'qa/hotfix8_runtime_product_check.py').read_text(encoding='utf-8'))
check('Hotfix10 structural restart statement gate', 'TNSUITE_BRIDGEX_BUILD12_HF10_RESTART_STRUCTURAL_STATEMENT' in patch and 'hotfix10_restart_statement_check.py' in build_sh and 'HOTFIX10_RESTART_STATEMENT_QA=PASS' in build_sh and 'rfind(\"wxMessageBox(\"' not in patch)

check('Hotfix11 bitmap SetBitmap gate', 'hotfix11_bitmap_setbitmap_check.py' in build_sh and 'HOTFIX11_BITMAP_SETBITMAP_QA=PASS' in build_sh and 'staticbitmap_pattern' not in patch and 'STATUSBITMAP_HF11_PATCH_APPLIED=NONE' in patch)
check('Hotfix12 clean production payload gate', 'hotfix12_settings_payload_check.py' in build_sh and 'HOTFIX12_SETTINGS_PAYLOAD_QA=PASS' in build_sh and 'production_payload_check.py' in build_sh and 'PRODUCTION_PAYLOAD_QA=PASS' in build_sh)
check('Development provenance excluded from runtime payload', '$APP/SOURCE_PATCHES' not in build_sh and 'QA_EVIDENCE="$DIST/${BUILD_NAME}-QA-Evidence"' in build_sh and 'rm -rf "$APP/lib"' in build_sh)
check('Installer has no embedded PowerShell process helper', 'BridgeX-CloseInstalled.ps1' not in installer and 'powershell.exe' not in installer.lower() and 'executionpolicy bypass' not in installer.lower())
check('Hotfix13 association intent gate retained', 'hotfix13_assoc_upstream_check.py' in build_sh and 'HOTFIX13_ASSOC_UPSTREAM_QA=PASS' in build_sh and 'EDIT_ASSOC_HF15_RECEIVER=' in patch)
check('Hotfix15 SHA-verified native extracted-source gate', 'hotfix15_extracted_upstream_check.py' in build_sh and 'HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS' in build_sh and build_sh.find('HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS') < build_sh.find('Apply TNSuite BridgeX UI patch'))
check('Hotfix14 dependency DB query is single-snapshot and observable', build_sh.count('pacman -Q') == 1 and 'DEPENDENCY_PACKAGE_DB_QA=START' in build_sh and 'DEPENDENCY_PACKAGE_DB_QA=PASS' in build_sh and 'reason=TIMEOUT' in build_sh)
check('Hotfix14 clean-upgrade installer prevents stale development payload', 'RMDir /r "$INSTDIR"' in installer and 'No mixed-version install was created.' in installer and 'install_clean_verified:' in installer)

check('Hotfix15 native association regression gate', 'hotfix15_native_assoc_regression_check.py' in build_sh and 'HOTFIX15_NATIVE_ASSOC_REGRESSION_QA=PASS' in build_sh)
check('Hotfix16 first-restart persistence handoff', all(x in patch for x in ('TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_HANDOFF','TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS','TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF','TNSUITE_BRIDGEX_RESTART_PARENT_PID','WaitForSingleObject','wxSetEnv','wxUnsetEnv')))
check('Hotfix16 first-restart persistence QA gate', 'hotfix16_restart_persistence_check.py' in build_sh and 'HOTFIX16_RESTART_PERSISTENCE_QA=PASS' in build_sh)
check('Hotfix16 Windows restart handoff API probe', 'WX33_HF16_RESTART_HANDOFF_API_COMPILE_QA=PASS' in build_sh and 'WaitForSingleObject' in build_sh and 'wxSetEnv' in build_sh)
if not all(ok for _,ok in checks):
    print('PRODUCT_CONTENT_QA=FAIL'); raise SystemExit(1)
print('PRODUCT_CONTENT_QA=PASS')
