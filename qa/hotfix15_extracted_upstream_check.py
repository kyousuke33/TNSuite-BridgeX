#!/usr/bin/env python3
"""Validate SHA-verified FileZilla 3.70.6 native custom-association data path."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: hotfix15_extracted_upstream_check.py <extracted-filezilla-root>')
root = Path(sys.argv[1]).resolve()
p = root / 'src/interface/settings/optionspage_edit_associations.cpp'
if not p.is_file():
    raise SystemExit(f'FAIL  upstream association source missing: {p}')
text = p.read_text(encoding='utf-8')
checks = []

def check(label, ok):
    ok = bool(ok)
    checks.append((label, ok))
    print(('PASS  ' if ok else 'FAIL  ') + label)

def find_method_span(source, method_name):
    signature = re.search(
        rf'bool\s+COptionsPageEditAssociations::{re.escape(method_name)}\s*\(\s*\)\s*\{{', source)
    if not signature:
        return None
    open_brace = source.find('{', signature.start())
    depth = 0
    i = open_brace
    state = 'code'
    while i < len(source):
        c = source[i]
        n = source[i + 1] if i + 1 < len(source) else ''
        if state == 'code':
            if c == '/' and n == '/': state = 'line_comment'; i += 2; continue
            if c == '/' and n == '*': state = 'block_comment'; i += 2; continue
            if c == '"': state = 'string'; i += 1; continue
            if c == "'": state = 'char'; i += 1; continue
            if c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: return (signature.start(), open_brace, i + 1)
        elif state == 'line_comment':
            if c == '\n': state = 'code'
        elif state == 'block_comment':
            if c == '*' and n == '/': state = 'code'; i += 2; continue
        elif state in ('string', 'char'):
            quote = '"' if state == 'string' else "'"
            if c == '\\': i += 2; continue
            if c == quote: state = 'code'
        i += 1
    return None

def inventory():
    print('HOTFIX15_ASSOC_SOURCE_INVENTORY=START')
    for no, line in enumerate(text.splitlines(), 1):
        if any(token in line for token in (
            'COptionsPageEditAssociations::LoadPage',
            'COptionsPageEditAssociations::Validate',
            'COptionsPageEditAssociations::SavePage',
            'OPTION_EDIT_CUSTOMASSOCIATIONS', 'ChangeValue', 'GetValue')):
            print(f'SOURCE_LINE={no}:{line.strip()}')
    print('HOTFIX15_ASSOC_SOURCE_INVENTORY=END')

load_pattern = re.compile(
    r'(?P<receiver>[A-Za-z_][A-Za-z0-9_]*)\s*->\s*ChangeValue\s*\(\s*'
    r'm_pOptions\s*->\s*get_string\s*\(\s*OPTION_EDIT_CUSTOMASSOCIATIONS\s*\)\s*\)\s*;', re.S)
save_pattern = re.compile(
    r'm_pOptions\s*->\s*set\s*\(\s*OPTION_EDIT_CUSTOMASSOCIATIONS\s*,\s*'
    r'(?P<receiver>[A-Za-z_][A-Za-z0-9_]*)\s*->\s*GetValue\s*\(\s*\)\s*\.\s*ToStdWstring\s*\(\s*\)\s*\)\s*;', re.S)
load_matches = list(load_pattern.finditer(text))
save_matches = list(save_pattern.finditer(text))
check('Exactly one native custom-association load binding exists', len(load_matches) == 1)
check('Exactly one native custom-association save binding exists', len(save_matches) == 1)

receiver = None
if len(load_matches) == 1 and len(save_matches) == 1:
    load_receiver = load_matches[0].group('receiver')
    save_receiver = save_matches[0].group('receiver')
    check('Load and Save use the same native association receiver', load_receiver == save_receiver)
    if load_receiver == save_receiver:
        receiver = load_receiver
else:
    check('Load and Save use the same native association receiver', False)

spans = {name: find_method_span(text, name) for name in ('LoadPage', 'Validate', 'SavePage')}
for name in ('LoadPage', 'Validate', 'SavePage'):
    check(f'{name} method body can be resolved', spans[name] is not None)

if receiver and all(spans.values()):
    check('Native load binding belongs to LoadPage', spans['LoadPage'][0] <= load_matches[0].start() < spans['LoadPage'][2])
    check('Validate is structurally available for pre-validation native repair', spans['Validate'] is not None)
    check('Native save binding belongs to SavePage', spans['SavePage'][0] <= save_matches[0].start() < spans['SavePage'][2])
    check('Native receiver is not obsolete Hotfix12 ID assumption', receiver != 'ID_EDIT_ASSOCIATIONS')
else:
    check('Native load binding belongs to LoadPage', False)
    check('Validate is structurally available for pre-validation native repair', False)
    check('Native save binding belongs to SavePage', False)
    check('Native receiver is not obsolete Hotfix12 ID assumption', False)

if not all(ok for _, ok in checks):
    inventory()
    print('HOTFIX15_EXTRACTED_UPSTREAM_QA=FAIL')
    raise SystemExit(1)
print(f'HOTFIX15_EXTRACTED_ASSOC_RECEIVER={receiver}')
print('HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS')
