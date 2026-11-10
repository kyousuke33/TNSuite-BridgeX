#!/usr/bin/env python3
"""Verify About/Welcome version overlay is wired into every source-built Hotfix25."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
baseline = (root / "scripts/patch_tnsuite_bridgex.py").read_text(encoding="utf-8")
overlay = root / "scripts/patch_tnsuite_bridgex_hotfix25_version.py"
prepare = (root / ".release/prepare-hotfix24-build-hooks.ps1").read_text(encoding="utf-8")
native = (root / ".github/workflows/native-installer-candidate.yml").read_text(encoding="utf-8")
release = (root / ".github/workflows/windows-release.yml").read_text(encoding="utf-8")

checks = {
    "historical_baseline_preserved": baseline.count('TNSuite BridgeX 0.5 Build12-Hotfix16') == 2,
    "overlay_exists": overlay.is_file(),
    "about_welcome_overlay_injected": 'python "$KIT/scripts/patch_tnsuite_bridgex_hotfix25_version.py" "$SRC"' in prepare,
    "correct_patch_order": prepare.index("patch_tnsuite_bridgex_hotfix24.py") < prepare.index("patch_tnsuite_bridgex_hotfix25_version.py"),
    "native_uses_shared_preparer": ".release\\prepare-hotfix24-build-hooks.ps1" in native,
    "release_uses_shared_preparer": ".release\\prepare-hotfix24-build-hooks.ps1" in release,
    "binary_runtime_checker_wired": "verify_hotfix25_runtime_binary.py" in native and "verify_hotfix25_runtime_binary.py" in release,
}
for name, valid in checks.items():
    print(f"HF25_VERSION_{name.upper()}={'PASS' if valid else 'FAIL'}")
if not all(checks.values()):
    raise SystemExit("HF25_RUNTIME_VERSION_SOURCE_QA=FAIL")
r = subprocess.run(
    [sys.executable, str(overlay), "--self-test"],
    cwd=root,
    check=False,
)
if r.returncode:
    raise SystemExit("HF25_RUNTIME_VERSION_SOURCE_QA=FAIL_SELFTEST")
r = subprocess.run([sys.executable, str(root / "qa/verify_hotfix25_runtime_binary.py"), "--self-test"], cwd=root, check=False)
if r.returncode:
    raise SystemExit("HF25_RUNTIME_BINARY_CHECK_SELFTEST=FAIL")
print("HF25_RUNTIME_VERSION_SOURCE_QA=PASS")
