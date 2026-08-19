#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: bridgex_locale_source_check.py <bridgex_vi_VN.po>')

p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')
lines = text.splitlines()

checks = []
def check(label, ok):
    ok = bool(ok)
    checks.append((label, ok))
    print(('PASS  ' if ok else 'FAIL  ') + label)

header = '\n'.join(lines[:16])
required = [
    r'"Project-Id-Version: TNSuite BridgeX 0.5 Build12-Hotfix16\n"',
    r'"PO-Revision-Date: 2026-08-18 00:00+0700\n"',
    r'"Last-Translator: TNSuite\n"',
    r'"Language-Team: Vietnamese\n"',
    r'"Language: vi_VN\n"',
    r'"MIME-Version: 1.0\n"',
    r'"Content-Type: text/plain; charset=UTF-8\n"',
    r'"Content-Transfer-Encoding: 8bit\n"',
    r'"Plural-Forms: nplurals=1; plural=0;\n"',
]

check('PO starts with empty msgid/msgstr header', lines[:2] == ['msgid ""', 'msgstr ""'])
check('No double-escaped newline in PO header', r'\\n' not in header)
for expected in required:
    check(f'Header field {expected[1:expected.find(":")]}', expected in header)
check('UTF-8 charset token is not contaminated by another header field',
      'charset=UTF-8\\nContent-Transfer-Encoding:' not in header)

if not all(ok for _, ok in checks):
    print('BRIDGEX_VI_LOCALE_SOURCE_QA=FAIL')
    raise SystemExit(1)

print('BRIDGEX_VI_LOCALE_SOURCE_QA=PASS')
