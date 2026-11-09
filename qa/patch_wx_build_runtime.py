#!/usr/bin/env python3
"""Apply reviewed wxWidgets ABI build fix only to a disposable build copy.

The historical Build12-Hotfix16 canonical source manifest must stay byte-exact.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

OLD_VERSION = "case \"$WXVER\" in\n  3.3.*) ;;\n  *) echo \"ERROR: Expected wxWidgets 3.3.x, got $WXVER\" >&2; exit 12 ;;\nesac"
NEW_VERSION = "# Rolling MSYS2 patch upgrades must receive explicit review and Windows QA.\ncase \"$WXVER\" in\n  3.3.3|3.3.4) ;;\n  *) echo \"ERROR: Unreviewed wxWidgets version $WXVER\" >&2; exit 12 ;;\nesac"
OLD_STATIC = "# The bundle must contain wxWidgets 3.3 runtime and must not contain wx 3.2 runtime.\nfind \"$APP/bin\" -maxdepth 1 -type f -iname 'wx*333*.dll' | grep -q . || {\n  echo \"ERROR: wxWidgets 3.3 runtime DLLs not found in bundle.\" >&2; exit 15;\n}\nif find \"$APP/bin\" -maxdepth 1 -type f -iname 'wx*32*.dll' | grep -q .; then\n  echo \"ERROR: wxWidgets 3.2 runtime leaked into bundle.\" >&2\n  exit 16\nfi"
NEW_STATIC = "# Check ABI against the actual reviewed wx-config version, not historical 333.\npython \"$QA/wx_runtime_abi_check.py\" \"$WXVER\" \"$APP/bin\""


def transform(text: str) -> str:
    for old, new in ((OLD_VERSION, NEW_VERSION), (OLD_STATIC, NEW_STATIC)):
        matches = text.count(old)
        if matches != 1:
            raise ValueError(f"WX_BUILD_COPY_PATCH_ANCHOR_COUNT={matches}")
        text = text.replace(old, new, 1)
    return text


def self_test() -> None:
    source = Path(__file__).resolve().parents[1] / "scripts/build-filezilla-dark.sh"
    before = source.read_text(encoding="utf-8")
    after = transform(before)
    assert after != before and OLD_STATIC not in after and OLD_VERSION not in after
    with tempfile.TemporaryDirectory(prefix="bridgex-wx-patch-") as temp:
        target = Path(temp) / source.name
        target.write_text(after, encoding="utf-8")
        subprocess.run(("bash", "-n", str(target)), check=True)
    assert source.read_text(encoding="utf-8") == before
    print("WX_DISPOSABLE_BUILD_PATCH_SELFTEST=PASS")
    print("BASELINE_MANIFEST_SOURCE_MUTATION=NONE")


def main() -> None:
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        return
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_wx_build_runtime.py --self-test | DISPOSABLE_SCRIPT")
    file = Path(sys.argv[1])
    if not file.is_file():
        raise SystemExit(f"WX_DISPOSABLE_BUILD_SCRIPT_MISSING={file}")
    file.write_text(transform(file.read_text(encoding="utf-8")), encoding="utf-8")
    print("WX_DISPOSABLE_BUILD_PATCH=PASS")


if __name__ == "__main__":
    main()
