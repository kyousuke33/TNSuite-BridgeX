#!/usr/bin/env python3
"""Fail-closed validation for the install/portable runtime payload."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: production_payload_check.py <payload-root>")
root = Path(sys.argv[1]).resolve()
checks=[]
def check(label, ok):
    ok=bool(ok); checks.append((label,ok)); print(("PASS  " if ok else "FAIL  ")+label)

required_files = [
    'bin/BridgeX.exe',
    'bin/BridgeX-CLI.exe',
    'bin/BridgeX-CLI-Shell.cmd',
    'bin/docs/BridgeX-Help.html',
    'bin/docs/BridgeX-Report-Bug.html',
    'COPYING',
    'share/locale/vi_VN/LC_MESSAGES/filezilla.mo',
    'share/locale/vi_VN/LC_MESSAGES/bridgex.mo',
]
for rel in required_files:
    check(f"required runtime file: {rel}", (root/rel).is_file())
check('FileZilla runtime resources retained', (root/'share/filezilla/resources').is_dir())

forbidden_roots = ['SOURCE_PATCHES','lib','BridgeX-CloseInstalled.ps1','BUILD_INFO.md','BUILD_SCHEDULER_REPORT.txt','CHANGELOG.md',
                   'CLI_SOURCE_QA_REPORT.txt','CONTRAST_REPORT.txt','INSTALLER_SOURCE_QA_REPORT.txt',
                   'PRODUCT_CONTENT_QA_REPORT.txt','README.md','README_FIRST.txt','SOURCE_COMPAT_REPORT.txt','SOURCE_MANIFEST.txt',
                   'KIT_SHA256SUMS.txt','STATIC_QA_REPORT.md','STATIC_QA_RESULTS.txt']
for name in forbidden_roots:
    check(f"production root excludes {name}", not (root/name).exists())
check('production root excludes all QA reports', not any(root.glob('*_QA_REPORT.txt')))
for rel in ['share/applications','share/appdata','share/metainfo','share/man','share/doc']:
    check(f"Windows payload excludes non-runtime {rel}", not (root/rel).exists())

forbidden_suffixes={'.cpp','.cc','.cxx','.h','.hpp','.py','.patch','.po','.a','.la','.pc'}
leaks=[]
for p in root.rglob('*'):
    if p.is_file() and p.suffix.lower() in forbidden_suffixes:
        leaks.append(str(p.relative_to(root)))
check('no source/build-development files in runtime payload', not leaks)
if leaks:
    for x in leaks[:20]: print('LEAK  '+x)

root_dirs=sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
root_files=sorted(p.name for p in root.iterdir() if p.is_file()) if root.is_dir() else []
check('runtime root directories are only bin/share', all(x in {'bin','share'} for x in root_dirs))
check('runtime root files are license-only before installer metadata', all(x == 'COPYING' for x in root_files))

if not all(ok for _,ok in checks):
    print('PRODUCTION_PAYLOAD_QA=FAIL'); raise SystemExit(1)
print('PRODUCTION_PAYLOAD_QA=PASS')
