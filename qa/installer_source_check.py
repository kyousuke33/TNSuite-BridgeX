from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
checks = {
    'admin install': 'RequestExecutionLevel admin' in s,
    'program files install': '$PROGRAMFILES64\\TNSuite\\BridgeX' in s,
    'welcome page': 'MUI_PAGE_WELCOME' in s,
    'desktop shortcut option': 'Create a desktop shortcut' in s,
    'finish launch': 'MUI_FINISHPAGE_RUN' in s and 'BridgeX.exe' in s,
    'brand icon': 'BRAND_ICON' in s and 'MUI_ICON' in s,
    'branded MUI side art': 'MUI_WELCOMEFINISHPAGE_BITMAP' in s and 'MUI_UNWELCOMEFINISHPAGE_BITMAP' in s,
    'branded MUI header art': 'MUI_HEADERIMAGE_BITMAP' in s and 'MUI_HEADERIMAGE_UNBITMAP' in s,
    'simplified detail panes': 'ShowInstDetails hide' in s and 'ShowUninstDetails hide' in s,
    'uninstall welcome finish': 'MUI_UNPAGE_WELCOME' in s and 'MUI_UNPAGE_FINISH' in s,
    'start menu shortcut': 'TNSuite BridgeX.lnk' in s,
    'cli shortcut': 'BridgeX CLI.lnk' in s and 'BridgeX-CLI-Shell.cmd' in s,
    'uninstaller': 'WriteUninstaller' in s and 'UninstallString' in s,
    'preserve appdata': 'Preserve user settings/site profiles under %APPDATA%' in s,
    'app paths aliases': 'App Paths\\BridgeX.exe' in s and 'App Paths\\BridgeX-CLI.exe' in s,
    'install marker created': 'BRIDGEX_INSTALL_MARKER' in s and 'FileOpen $0 "$INSTDIR\\${BRIDGEX_INSTALL_MARKER}" w' in s,
    'uninstall marker fail closed': 'IfFileExists "$INSTDIR\\${BRIDGEX_INSTALL_MARKER}" uninstall_marker_ok' in s and 'Program files were not removed' in s,
    'full verified tree removal': 'SetOutPath "$TEMP"' in s and 'RMDir /r /REBOOTOK "$INSTDIR"' in s,
    'tnsuite parent only-if-empty removal': 'RMDir "$PROGRAMFILES64\\TNSuite"' in s,
    'standard zlib compressor': 'SetCompressor zlib' in s,
    'solid lzma disabled': 'SetCompressor /SOLID lzma' not in s,
    'no powershell execution': 'powershell.exe' not in s.lower(),
    'no execution-policy bypass': 'executionpolicy bypass' not in s.lower(),
    'no embedded process helper': 'BridgeX-CloseInstalled.ps1' not in s,
    'no process-kill primitives': 'taskkill' not in s.lower() and 'Stop-Process' not in s and '.Kill()' not in s,
    'clean upgrade requires verified install marker': r'IfFileExists "$INSTDIR\${BRIDGEX_INSTALL_MARKER}" install_clean_verified' in s and 'without the TNSuite install marker' in s,
    'clean upgrade removes old install tree before payload copy': 'install_clean_verified:' in s and 'RMDir /r "$INSTDIR"' in s and s.find('RMDir /r "$INSTDIR"') < s.find(r'File /r "${PAYLOAD_DIR}\*"'),
    'locked upgrade fails closed': 'Close BridgeX and any process using its files' in s and 'No mixed-version install was created.' in s and 'Abort' in s,
}
for k, v in checks.items():
    print(('PASS' if v else 'FAIL'), k)
if not all(checks.values()):
    raise SystemExit(1)
print('INSTALLER_SOURCE_QA=PASS')
