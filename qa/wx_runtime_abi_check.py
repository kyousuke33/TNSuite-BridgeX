#!/usr/bin/env python3
"""Fail-closed wxWidgets runtime DLL ABI check for Build12 Windows packaging."""
import sys
import tempfile
from pathlib import Path

SUPPORTED = frozenset(("3.3.3", "3.3.4"))


def check(version: str, directory: Path) -> None:
    if version not in SUPPORTED:
        raise ValueError(f"WX_RUNTIME_UNREVIEWED_VERSION={version}")
    if not directory.is_dir():
        raise ValueError(f"WX_RUNTIME_DIRECTORY_MISSING={directory}")
    abi = version.replace(".", "")
    dlls = [p.name.lower() for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() == ".dll"]
    for prefix in ("wxbase", "wxmsw"):
        if not any(name.startswith(f"{prefix}{abi}") for name in dlls):
            raise ValueError(f"WX_RUNTIME_MISSING_{prefix.upper()}_ABI={abi}")
    foreign = sorted(name for name in dlls
                     if name.startswith(("wxbase", "wxmsw"))
                     and not name.startswith((f"wxbase{abi}", f"wxmsw{abi}")))
    if foreign:
        raise ValueError("WX_RUNTIME_MIXED_ABI=" + ",".join(foreign))
    print(f"WX_RUNTIME_ABI_QA=PASS version={version} abi={abi}")


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="bridgex-wx-abi-") as tmp:
        root = Path(tmp)
        for version, abi in (("3.3.3", "333"), ("3.3.4", "334")):
            for prefix in ("wxbase", "wxmsw"):
                (root / f"{prefix}{abi}u_gcc_custom.dll").touch()
            check(version, root)
            for unreviewed in ("3.3.2", "3.3.5", "4.0.0"):
                try:
                    check(unreviewed, root)
                except ValueError:
                    pass
                else:
                    raise AssertionError(f"Unreviewed wxWidgets accepted: {unreviewed}")
            foreign = root / f"wxbase{'334' if abi == '333' else '333'}u_gcc_custom.dll"
            foreign.touch()
            try:
                check(version, root)
            except ValueError:
                pass
            else:
                raise AssertionError("Mixed wxWidgets ABI accepted")
            foreign.unlink()
            for path in root.iterdir():
                path.unlink()
        try:
            check("3.3.4", root)
        except ValueError:
            pass
        else:
            raise AssertionError("Missing wxWidgets DLLs accepted")
    print("WX_RUNTIME_ABI_SELFTEST=PASS")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 3:
        try:
            check(sys.argv[1], Path(sys.argv[2]))
        except ValueError as exc:
            sys.exit(str(exc))
    else:
        sys.exit("Usage: wx_runtime_abi_check.py --self-test | VERSION APP_BIN")
