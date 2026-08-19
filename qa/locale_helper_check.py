#!/usr/bin/env python3
from pathlib import Path
import os, subprocess, tempfile

kit = Path(__file__).resolve().parents[1]
helper = kit / 'scripts' / 'compile-shipped-locales.sh'

with tempfile.TemporaryDirectory(prefix='fzdark-locale-qa-') as td:
    root = Path(td)
    src = root / 'source'
    loc = src / 'locales'
    out = root / 'out'
    loc.mkdir(parents=True)
    # The helper should treat PO files as opaque input and delegate validation to msgfmt.
    (loc / 'en.po').write_text('fixture-en\n', encoding='utf-8')
    (loc / 'vi_VN.po').write_text('fixture-vi\n', encoding='utf-8')
    # A broken symlink-like/non-file entry must not be treated as a catalog.
    try:
        (loc / 'broken.po').symlink_to(loc / 'missing-target.po')
    except OSError:
        pass

    fake = root / 'msgfmt'
    fake.write_text('''#!/usr/bin/env bash\nset -euo pipefail\nout=\"\"\nin=\"\"\nwhile (( $# )); do\n  case \"$1\" in\n    -c) shift ;;\n    -o) out=\"$2\"; shift 2 ;;\n    *) in=\"$1\"; shift ;;\n  esac\ndone\n[[ -n \"$out\" && -n \"$in\" ]]\ncp \"$in\" \"$out\"\n''', encoding='utf-8', newline='\n')
    fake.chmod(0o755)

    env = os.environ.copy()
    env['MSGFMT_BIN'] = str(fake)
    cp = subprocess.run(['bash', str(helper), str(src), str(out)], env=env, text=True, capture_output=True)
    if cp.returncode != 0:
        raise SystemExit(f'LOCALE_HELPER_QA=FAIL rc={cp.returncode}\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}')
    if 'FILEZILLA_LOCALES_COMPILED=2' not in cp.stdout:
        raise SystemExit(f'LOCALE_HELPER_QA=FAIL unexpected count\n{cp.stdout}')
    for lang in ('en', 'vi_VN'):
        f = out / lang / 'LC_MESSAGES' / 'filezilla.mo'
        if not f.is_file() or f.stat().st_size == 0:
            raise SystemExit(f'LOCALE_HELPER_QA=FAIL missing output {f}')
    if (out / 'broken' / 'LC_MESSAGES' / 'filezilla.mo').exists():
        raise SystemExit('LOCALE_HELPER_QA=FAIL broken/non-file catalog was packaged')

print('LOCALE_HELPER_QA=PASS')
