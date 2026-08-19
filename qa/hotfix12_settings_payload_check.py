#!/usr/bin/env python3
"""Regression QA for Hotfix12 settings repair and clean production payload."""
from pathlib import Path
import subprocess, sys, tempfile

if len(sys.argv) != 2:
    raise SystemExit('Usage: hotfix12_settings_payload_check.py <kit-root>')
root=Path(sys.argv[1]).resolve()
patch=(root/'scripts/patch_tnsuite_bridgex.py').read_text(encoding='utf-8')
build=(root/'scripts/build-filezilla-dark.sh').read_text(encoding='utf-8')
installer=(root/'installer/TNSuiteBridgeXInstaller.nsi').read_text(encoding='utf-8')
payload_qa=root/'qa/production_payload_check.py'
checks=[]
def check(label, ok):
    ok=bool(ok); checks.append((label,ok)); print(('PASS  ' if ok else 'FAIL  ')+label)

check('Hotfix12 value-repair marker', 'TNSUITE_BRIDGEX_BUILD12_HF12_STORE_NOTEPAD_VALUE_REPAIR' in patch)
check('repair discovers native association receiver', 'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_ASSOC_RECEIVER_DISCOVERY' in patch and 'native_load_pattern = re.compile' in patch and 'native_save_pattern = re.compile' in patch and 'OPTION_EDIT_CUSTOMASSOCIATIONS' in patch)
check('repair covers native Load Validate and SavePage paths', all(x in patch for x in ('HF15_NATIVE_LOAD_REPAIR','HF13_VALIDATE_REPAIRED_ASSOCIATIONS','HF15_NATIVE_VALIDATE_REPAIR','HF13_PERSIST_REPAIRED_ASSOCIATIONS','HF15_NATIVE_PERSIST_REPAIR')))
check('obsolete FindWindow repair removed', 'RepairStaleStoreNotepadAssociation(wxWindow* page)' not in patch and 'auto* editor = wxDynamicCast' not in patch)
check('repair remains Store-Notepad-specific', 'microsoft.windowsnotepad_' in patch.lower() and r'\\notepad\\notepad.exe' in patch)
check('stable system Notepad target remains fail-closed', r'System32\\notepad.exe' in patch and 'stableNotepad.FileExists()' in patch)

check('SOURCE_PATCHES no longer copied into runtime payload', '$APP/SOURCE_PATCHES' not in build)
check('QA reports no longer copied into runtime payload', '"$APP/HOTFIX' not in build and '"$APP/PRODUCT_CONTENT_QA_REPORT.txt"' not in build)
check('production lib tree pruned', 'rm -rf "$APP/lib"' in build)
check('non-Windows share metadata pruned', all(x in build for x in ('$APP/share/applications','$APP/share/appdata','$APP/share/man','$APP/share/doc')))
check('production payload QA wired before portable ZIP', 'production_payload_check.py' in build and build.find('PRODUCTION_PAYLOAD_QA=PASS') < build.find('log "Create portable ZIP"'))
check('QA evidence moved outside payload', 'QA_EVIDENCE="$DIST/${BUILD_NAME}-QA-Evidence"' in build)
check('close helper not persisted in Program Files', '"$INSTDIR\\BridgeX-CloseInstalled.ps1"' not in installer)
check('uninstaller extracts close helper to TEMP', 'File /oname=BridgeX-CloseInstalled.ps1' in installer and '"$TEMP\\BridgeX-CloseInstalled.ps1"' in installer)
check('upgrade cleans marker-verified Program Files tree before payload copy', 'install_clean_verified:' in installer and 'RMDir /r "$INSTDIR"' in installer and installer.find('RMDir /r "$INSTDIR"') < installer.find('File /r "${PAYLOAD_DIR}\\*"'))
check('upgrade cleanup fails closed for unverified or mixed-version tree', 'IfFileExists "$INSTDIR\\${BRIDGEX_INSTALL_MARKER}" install_clean_verified 0' in installer and 'No mixed-version install was created.' in installer)

# Model the exact runtime association supplied by the user.
def repair_line(line, stable=r'C:\WINDOWS\System32\notepad.exe'):
    lower=line.lower(); sm=r'\windowsapps\microsoft.windowsnotepad_'; suf=r'\notepad\notepad.exe'
    marker=lower.find(sm); suffix=lower.find(suf, marker if marker >= 0 else 0)
    if marker < 0 or suffix < 0: return line
    quote=line.rfind('"',0,marker+1)
    if quote >= 0: start=quote+1
    else:
        space=line.rfind(' ',0,marker+1); tab=line.rfind('\t',0,marker+1)
        start=max(space+1 if space>=0 else 0, tab+1 if tab>=0 else 0)
    return line[:start]+stable+line[suffix+len(suf):]
raw_lines = [
    r'. "C:\Users\admin\AppData\Local\Programs\Microsoft VS Code\Code.exe"',
    r'conf "C:\Users\admin\AppData\Local\Programs\Microsoft VS Code\Code.exe"',
    r'css C:\WINDOWS\system32\NOTEPAD.EXE %f',
    r'env "C:\Users\admin\AppData\Local\Programs\Microsoft VS Code\Code.exe"',
    r'example C:\WINDOWS\system32\OpenWith.exe %f',
    r'html "C:\Program Files\Google\Chrome\Application\chrome.exe" --single-argument %f',
    r'js C:\WINDOWS\system32\OpenWith.exe %f',
    r'json "C:\Users\admin\AppData\Local\Programs\Microsoft VS Code\Code.exe" %f',
    r'log "C:\Users\admin\AppData\Local\Programs\Microsoft VS Code\Code.exe"',
    r'md "C:\Users\admin\AppData\Local\Programs\Microsoft VS Code\Code.exe" %f',
    r'path C:\WINDOWS\system32\OpenWith.exe %f',
    r'php "C:\Users\admin\AppData\Local\Programs\Microsoft VS Code\Code.exe"',
    r'txt "C:\Program Files\WindowsApps\Microsoft.WindowsNotepad_11.2604.5.0_x64__8wekyb3d8bbwe\Notepad\Notepad.exe" %f',
]
repaired_lines=[repair_line(x) for x in raw_lines]
check('runtime stale txt association repairs to stable System32 Notepad', repaired_lines[-1] == r'txt "C:\WINDOWS\System32\notepad.exe" %f')
check('all unrelated association lines are byte-for-byte preserved', repaired_lines[:-1] == raw_lines[:-1])
check('exactly one user association line is migrated', sum(a != b for a,b in zip(raw_lines,repaired_lines)) == 1)

# Exercise the actual payload validator with a valid synthetic runtime and a
# deliberate source leak. This ensures the checker itself is fail-closed.
with tempfile.TemporaryDirectory(prefix='bridgex-hf12-payload-') as td:
    p=Path(td)
    for d in ['bin/docs','share/filezilla/resources','share/locale/vi_VN/LC_MESSAGES']:
        (p/d).mkdir(parents=True,exist_ok=True)
    for rel in ['bin/BridgeX.exe','bin/BridgeX-CLI.exe','bin/BridgeX-CLI-Shell.cmd','bin/docs/BridgeX-Help.html','bin/docs/BridgeX-Report-Bug.html','COPYING','share/locale/vi_VN/LC_MESSAGES/filezilla.mo','share/locale/vi_VN/LC_MESSAGES/bridgex.mo']:
        (p/rel).write_bytes(b'x')
    (p/'share/filezilla/resources/sentinel.dat').write_bytes(b'x')
    good=subprocess.run([sys.executable,str(payload_qa),str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    check('synthetic clean runtime passes production payload QA', good.returncode == 0 and 'PRODUCTION_PAYLOAD_QA=PASS' in good.stdout)
    (p/'SOURCE_PATCHES').mkdir(); (p/'SOURCE_PATCHES/leak.py').write_text('x=1',encoding='utf-8')
    bad=subprocess.run([sys.executable,str(payload_qa),str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    check('synthetic development leak is rejected', bad.returncode != 0 and 'PRODUCTION_PAYLOAD_QA=FAIL' in bad.stdout)

if not all(ok for _,ok in checks):
    print('HOTFIX12_SETTINGS_PAYLOAD_QA=FAIL'); raise SystemExit(1)
print('HOTFIX12_SETTINGS_PAYLOAD_QA=PASS')
