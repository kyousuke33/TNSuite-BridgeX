#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: cli_source_check.py <bridgex-cli.cpp>")

p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
checks = [
    ("Commercial FileZilla CLI is explicitly disclaimed", "not the official/commercial filezilla cli" in text.lower()),
    ("Uses Windows OpenSSH sftp backend", 'find_exe(L"sftp.exe")' in text),
    ("BatchMode enforced", 'BatchMode=yes' in text),
    ("Strict host-key checking is default", 'StrictHostKeyChecking=yes' in text),
    ("accept-new is explicit opt-in", 'StrictHostKeyChecking=accept-new' in text),
    ("No password flag", '--password' not in text and '--pass ' not in text),
    ("No private-key copy logic", 'CopyFile' not in text and 'copy_file' not in text),
    ("Site config excludes password", 'ini_set(p, L"password"' not in text),
    ("JSON output exists", 'backend_exit_code' in text),
    ("Stable exit codes exist", 'EXIT_BACKEND = 10' in text and 'EXIT_PROCESS = 11' in text),
    ("Local shell in scripts is opt-in", '--allow-local-shell' in text and "Local shell commands (!)" in text),
    ("Selftest exists", 'CLI_SELFTEST=' in text and 'selftest(bool json)' in text),
    ("No system() shell execution", not re.search(r'\bsystem\s*\(', text)),
    ("CreateProcessW used", 'CreateProcessW(' in text),
    ("Child backend hidden", 'CREATE_NO_WINDOW' in text),
]
for label, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + label)
if not all(ok for _, ok in checks):
    print("CLI_SOURCE_QA=FAIL")
    raise SystemExit(1)
print("CLI_SOURCE_QA=PASS")
