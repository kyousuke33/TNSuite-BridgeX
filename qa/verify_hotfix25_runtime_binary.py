#!/usr/bin/env python3
"""Reject source-built BridgeX.exe whose actual About/Welcome version is stale.

Inspects UTF-16LE literals in the shipped PE rather than trusting source comments,
WiX metadata or the name of the installer.
"""
from pathlib import Path
import sys
import tempfile

EXPECTED = "TNSuite BridgeX 0.5 Build12-Hotfix25".encode("utf-16-le")
STALE = "TNSuite BridgeX 0.5 Build12-Hotfix16".encode("utf-16-le")


def check(path: Path) -> None:
    contents = path.read_bytes()
    expected_count = contents.count(EXPECTED)
    stale_count = contents.count(STALE)
    if not expected_count or stale_count:
        raise ValueError(
            f"HF25_COMPILED_RUNTIME_VERSION_FAIL expected={expected_count} stale={stale_count} file={path}"
        )
    print(f"HF25_COMPILED_RUNTIME_VERSION=PASS hotfix25_literals={expected_count} legacy_hotfix16_literals=0")


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="bridgex-version-binary-") as folder:
        f = Path(folder) / "BridgeX.exe"
        f.write_bytes(b"EXE" + EXPECTED + b"OTHER")
        check(f)
        f.write_bytes(b"EXE" + STALE + b"OTHER")
        try:
            check(f)
        except ValueError:
            pass
        else:
            raise AssertionError("stale runtime was incorrectly accepted")
        f.write_bytes(b"EXE" + EXPECTED + STALE)
        try:
            check(f)
        except ValueError:
            pass
        else:
            raise AssertionError("mixed runtime was incorrectly accepted")
        print("HF25_COMPILED_RUNTIME_VERSION_SELFTEST=PASS")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_hotfix25_runtime_binary.py <BridgeX.exe>|--self-test")
    if sys.argv[1] == "--self-test":
        self_test()
    else:
        check(Path(sys.argv[1]))
