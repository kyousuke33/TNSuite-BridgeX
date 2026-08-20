#!/usr/bin/env python3
from pathlib import Path
import sys
import struct

if len(sys.argv) != 2:
    raise SystemExit('Usage: hotfix8_runtime_product_check.py <kit-root>')
root=Path(sys.argv[1]).resolve()
patch=(root/'scripts/patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
build=(root/'scripts/build-filezilla-dark.sh').read_text(encoding='utf-8')
installer=(root/'installer/TNSuiteBridgeXInstaller.nsi').read_text(encoding='utf-8')
po=(root/'locales/bridgex_vi_VN.po').read_text(encoding='utf-8')
checks=[]
def check(label, ok):
    ok=bool(ok); checks.append(ok); print(('PASS  ' if ok else 'FAIL  ')+label)

check('Current Hotfix16 identity carrying Hotfix8 runtime fixes', '0.5-Build12-Hotfix16' in installer and '0.5.12.16' in installer)
check('Restart CTA marker', 'TNSUITE_BRIDGEX_BUILD12_HF8_RESTART_CTA' in patch)
check('Restart CTA compares language and theme', all(x in patch for x in ('oldLanguage','newLanguage','oldTheme','newTheme','restartRequired')))
check('Restart CTA labels', 'SetYesNoLabels(_("Restart now"), _("Later"))' in patch)
check('Restart CTA direct wx headers', all(x in patch for x in ('#include <wx/app.h>','#include <wx/msgdlg.h>','#include <wx/stdpaths.h>','#include <wx/utils.h>')))
check('Duplicate upstream restart popup ownership', 'TNSUITE_BRIDGEX_BUILD12_HF8_RESTART_CTA_OWNS_NOTIFICATION' in patch and 'needs to be restarted for the language change to take effect' in patch)
check('Vietnamese restart prompt translation', 'msgstr "Thay đổi ngôn ngữ hoặc chủ đề yêu cầu khởi động lại TNSuite BridgeX."' in po)
check('Vietnamese Restart now CTA', 'msgid "Restart now"' in po and 'msgstr "Khởi động ngay"' in po)
check('Vietnamese Later CTA', 'msgid "Later"' in po and 'msgstr "Để sau"' in po)

check('Hotfix11 SetBitmap guard marker', 'TNSUITE_BRIDGEX_BUILD12_HF11_SAFE_BITMAP_BUNDLE' in patch)
check('Disproven wxNullBitmap constructor blocker removed', 'staticbitmap_pattern' not in patch and 'no wxStaticBitmap constructor using wxNullBitmap' not in patch)
check('SetBitmap guard validates bitmap/bundle before use', 'bundle.IsOk()' in patch and 'bitmap.IsOk()' in patch and 'BridgeXSafeStaticBitmap' in patch)
check('No global wx assert suppression in patcher', not any(x in patch for x in ('wxDisableAsserts','SetAssertHandler','wxSetAssertHandler')))

check('Install marker defined', '!define BRIDGEX_INSTALL_MARKER ".tnsuite-bridgex-install"' in installer)
check('Install marker written', 'FileOpen $0 "$INSTDIR\\${BRIDGEX_INSTALL_MARKER}" w' in installer)
check('Uninstall marker guard', 'IfFileExists "$INSTDIR\\${BRIDGEX_INSTALL_MARKER}" uninstall_marker_ok' in installer)
check('Uninstall full tree with reboot fallback', 'SetOutPath "$TEMP"' in installer and 'RMDir /r /REBOOTOK "$INSTDIR"' in installer)
check('Uninstall keeps AppData', 'Preserve user settings/site profiles under %APPDATA%' in installer)
check('Installer has no embedded close helper', 'BridgeX-CloseInstalled.ps1' not in installer)
check('Installer has no PowerShell execution or policy bypass', 'powershell.exe' not in installer.lower() and 'executionpolicy bypass' not in installer.lower())
check('Installer avoids solid LZMA packing', 'SetCompressor zlib' in installer and 'SetCompressor /SOLID lzma' not in installer)
check('Locked upgrade fails closed instead of terminating processes', 'Close BridgeX and any process using its files' in installer and 'No mixed-version install was created.' in installer and 'Abort' in installer)

check('Branded installer/uninstaller MUI art wired', all(x in installer for x in ('MUI_WELCOMEFINISHPAGE_BITMAP','MUI_UNWELCOMEFINISHPAGE_BITMAP','MUI_HEADERIMAGE_BITMAP','MUI_HEADERIMAGE_UNBITMAP')))
check('Installer/uninstaller details hidden', 'ShowInstDetails hide' in installer and 'ShowUninstDetails hide' in installer)
check('Uninstaller welcome/finish pages', 'MUI_UNPAGE_WELCOME' in installer and 'MUI_UNPAGE_FINISH' in installer)
def read_windows_bmp24(path: Path):
    # Dependency-free BITMAPFILEHEADER + BITMAPINFOHEADER validation.
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b'BM':
        return None
    declared_size = struct.unpack_from('<I', data, 2)[0]
    pixel_offset = struct.unpack_from('<I', data, 10)[0]
    dib_size = struct.unpack_from('<I', data, 14)[0]
    if dib_size < 40 or len(data) < 14 + dib_size:
        return None
    width, height, planes, bpp, compression = struct.unpack_from('<iiHHI', data, 18)
    if declared_size not in (0, len(data)):
        return None
    if pixel_offset < 14 + dib_size or pixel_offset >= len(data):
        return None
    return width, abs(height), planes, bpp, compression

for name,size in [('BridgeX-Setup-Sidebar.bmp',(164,314)),('BridgeX-Setup-Header.bmp',(150,57))]:
    path=root/'installer'/name
    try:
        info=read_windows_bmp24(path)
        ok=info == (size[0], size[1], 1, 24, 0)
    except (OSError, struct.error):
        ok=False
    check(f'{name} is {size[0]}x{size[1]} 24-bit uncompressed Windows BMP', ok)

check('Hotfix8 QA gate wired before source download', 'hotfix8_runtime_product_check.py' in build and 'HOTFIX8_RUNTIME_PRODUCT_QA=PASS' in build and build.find('Hotfix8 runtime/product regression QA') < build.find('Download FileZilla ${FZ_VERSION} source'))
check('Hotfix11 wx safe-bitmap API probe wired', 'WX33_HF11_SAFE_BITMAP_API_COMPILE_QA=PASS' in build and '<wx/statbmp.h>' in build and '<wx/bmpbndl.h>' in build)
check('Hotfix8 wx restart CTA API probe wired', 'WX33_HF8_RESTART_CTA_API_COMPILE_QA=PASS' in build and 'SetYesNoLabels' in build)
check('Hotfix16 restart persistence API probe wired', 'WX33_HF16_RESTART_HANDOFF_API_COMPILE_QA=PASS' in build and 'WaitForSingleObject' in build and 'wxSetEnv' in build and 'wxUnsetEnv' in build)
check('Hotfix16 restart handoff preserves Hotfix8 CTA ownership', all(x in patch for x in ('TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_HANDOFF','TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS','TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF')))
check('Hotfix11 dynamic touched-TU compile gate wired', 'HF11_STATICBITMAP_PATCHED_TUS=' in build and 'HF11_STATICBITMAP_PATCHED_TU_COMPILE_QA=PASS' in build)
check('Interface settings remains in patched TU preflight', 'settings/filezilla-optionspage_interface.o' in build)

if not all(checks):
    print('HOTFIX8_RUNTIME_PRODUCT_QA=FAIL'); raise SystemExit(1)
print('HOTFIX8_RUNTIME_PRODUCT_QA=PASS')
