#!/usr/bin/env python3
"""Fail closed if BridgeX build-time Python QA/scripts import third-party modules."""
from pathlib import Path
import ast
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: hotfix9_qa_dependency_check.py <kit-root>')
root = Path(sys.argv[1]).resolve()
allowed = {
    '__future__', 'ast', 'os', 'pathlib', 're', 'struct', 'subprocess', 'sys', 'tempfile'
}
failures = []
scanned = 0
for dirname in ('qa', 'scripts'):
    for path in sorted((root / dirname).rglob('*.py')):
        scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f'{path.relative_to(root)}: parse error: {exc}')
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                top = name.split('.', 1)[0]
                if top not in allowed:
                    failures.append(f'{path.relative_to(root)}: non-stdlib import {name!r}')

if scanned == 0:
    failures.append('no Python QA/scripts found')
for failure in failures:
    print('FAIL  ' + failure)
if failures:
    print('HOTFIX9_QA_DEPENDENCY_QA=FAIL')
    raise SystemExit(1)
print(f'PASS  scanned Python files: {scanned}')
print('PASS  all build-time Python imports are explicitly stdlib-only')
print('PASS  Pillow/PIL is not required by the build kit')
print('HOTFIX9_QA_DEPENDENCY_QA=PASS')
