#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: build_scheduler_check.py <build-filezilla-dark.sh>')

p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')
checks = [
    ('Default compile concurrency is 2', 'BUILD_JOBS="${FZDARK_JOBS:-2}"' in text),
    ('Compile concurrency is capped 1..4', 'FZDARK_JOBS must be an integer from 1 to 4' in text),
    ('No all-core make fanout', not re.search(r'^\s*make\b.*nproc', text, re.MULTILINE)),
    ('No make keep-going storm', not re.search(r'^\s*make\s+-k\b', text, re.MULTILINE)),
    ('Inherited make flags cleared', 'unset MAKEFLAGS MFLAGS' in text),
    ('Serial recovery exists', 'run_full_compile 1 "serial-recovery"' in text),
    ('Resource pressure detection exists', 'RESOURCE_PRESSURE_DETECTED=YES' in text),
    ('Debug info disabled for full compile', 'SAFE_CXXFLAGS="-O2 -g0 -Wall"' in text),
    ('Full compile artifact gate exists', 'filezilla.exe missing after successful make.' in text),
    ('No shell backtick command substitution in active script lines', not any('`' in line for line in text.splitlines() if not line.lstrip().startswith('#'))),
]

for label, ok in checks:
    print(('PASS  ' if ok else 'FAIL  ') + label)

if not all(ok for _, ok in checks):
    print('SCHEDULER_QA=FAIL')
    raise SystemExit(1)
print('SCHEDULER_QA=PASS')
