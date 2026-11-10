#!/usr/bin/env python3
"""Fail-closed Hotfix25 runtime About/Welcome identity patch for disposable upstream source.

The historical Build12-Hotfix16 canonical patch and source manifest remain immutable.
"""
from pathlib import Path
import sys
import tempfile

OLD = "TNSuite BridgeX 0.5 Build12-Hotfix16"
NEW = "TNSuite BridgeX 0.5 Build12-Hotfix25"
TARGETS = (
    Path("src/interface/aboutdialog.cpp"),
    Path("src/interface/welcome_dialog.cpp"),
)


def apply(root: Path) -> None:
    updates = []
    for name in TARGETS:
        path = root / name
        if not path.is_file():
            raise ValueError(f"HF25_VERSION_FAIL missing={name}")
        text = path.read_text(encoding="utf-8")
        count = text.count(OLD)
        if count != 1 or NEW in text:
            raise ValueError(f"HF25_VERSION_FAIL anchor_count={count} unexpected_new={NEW in text} file={name}")
        updates.append((path, text.replace(OLD, NEW, 1)))

    # Validate every source before mutating any file.
    for path, updated in updates:
        path.write_text(updated, encoding="utf-8", newline="\n")
    for path, _ in updates:
        if path.read_text(encoding="utf-8").count(NEW) != 1:
            raise ValueError(f"HF25_VERSION_FAIL postcheck={path}")
    print("HF25_ABOUT_WELCOME_RUNTIME_VERSION=PASS version=0.5-Build12-Hotfix25")


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="bridgex-hf25-version-") as tmp:
        root = Path(tmp)
        for name in TARGETS:
            f = root / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("const char* text = \"" + OLD + "\";\n", encoding="utf-8")
        apply(root)
        assert all((root / f).read_text().count(NEW) == 1 for f in TARGETS)
        try:
            apply(root)
        except ValueError:
            pass
        else:
            raise AssertionError("Reapplying Hotfix25 branding must fail closed")
        (root / TARGETS[0]).write_text(OLD + " " + OLD, encoding="utf-8")
        try:
            apply(root)
        except ValueError:
            pass
        else:
            raise AssertionError("Duplicate old version must fail closed")
    print("HF25_RUNTIME_VERSION_PATCH_SELFTEST=PASS")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
    elif len(sys.argv) == 2:
        apply(Path(sys.argv[1]).resolve())
    else:
        raise SystemExit("Usage: patch_tnsuite_bridgex_hotfix25_version.py <source-root>|--self-test")
