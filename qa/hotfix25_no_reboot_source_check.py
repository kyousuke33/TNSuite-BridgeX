#!/usr/bin/env python3
"""Regression guard for Office 2026-11-09 Burn/MSI reboot root cause."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
builder = (root / ".release/build-wix-installer-hotfix23.ps1").read_text(encoding="utf-8")
workflow = (root / ".github/workflows/native-installer-candidate.yml").read_text(encoding="utf-8")
windows = (root / "qa/hotfix25_no_reboot_windows.ps1").read_text(encoding="utf-8")
checks = {
    "fresh_install_prevalidate_close": 'Condition=`"1`"' in builder and 'Before=`"InstallValidate`"' in builder,
    "fail_closed_close_action": 'Execute=`"immediate`" Return=`"check`"' in builder,
    "no_silent_process_close": 'Return=`"ignore`"' not in builder,
    "restart_manager_enabled": 'MSIRESTARTMANAGERCONTROL`" Value=`"0`"' in builder and 'MSIRESTARTMANAGERCONTROL`" Value=`"Disable`"' not in builder,
    "process_targets": all(x in builder for x in ("taskkill.exe", "BridgeX.exe", "BridgeX-CLI.exe", "tasklist.exe")),
    "process_postchecks": all(x in builder for x in ('/I "BridgeX.exe" >nul && exit /b 32', '/I "BridgeX-CLI.exe" >nul && exit /b 33')),
    "workflow_zero_only": "-notin @(0,3010)" not in workflow and "-notin @(0, 3010)" not in workflow,
    "windows_all_scenarios": all(x in windows for x in ("Run-Setup 'FRESH_INSTALL'", "Run-Setup 'UPGRADE'", "Run-Setup 'REPAIR'", "Run-Setup 'UNINSTALL'")),
    "windows_no_3010": '$p.ExitCode -ne 0' in windows and "Info 1903.Scheduling reboot operation" in windows,
    "wired_qa": "hotfix25_no_reboot_windows.ps1" in workflow,
    "diagnostic_logs_uploaded": "Upload Hotfix25 Windows E2E diagnostics" in workflow
        and "windows-qa-failure-summary.txt" in workflow
        and "Write-FailureEvidence" in windows,
    "legacy_qa_runtime_pin": workflow.count("fetch_pinned_rc1_qa_runtime.ps1 -OutputDirectories") == 3 and "RESTART_MANAGER=DISABLED" not in workflow
       and 'CANONICAL_ARTIFACT_RESOLUTION_FAIL' not in workflow,
    "msys2_official_pinned_mirror": (
        'https://repo.msys2.org/distrib/x86_64/msys2-x86_64-20260611.exe'
        in (root / "qa/prefetch_pinned_msys2.ps1").read_text(encoding="utf-8")
        and '3150D7D9AA5DEDD900A7F52300D4D918271E3A8FC47DE94848818FD5A430E6B0'
        in (root / "qa/prefetch_pinned_msys2.ps1").read_text(encoding="utf-8")
        and 'prefetch_pinned_msys2.ps1' in workflow
        and 'prefetch_pinned_msys2.ps1' in (root / ".github/workflows/windows-release.yml").read_text(encoding="utf-8")
    ),
}
for label, passed in checks.items():
    print(f"HF25_NO_REBOOT_{label.upper()}={'PASS' if passed else 'FAIL'}")
if not all(checks.values()):
    raise SystemExit("HF25_NO_REBOOT_SOURCE_QA=FAIL")
print("HF25_NO_REBOOT_SOURCE_QA=PASS")
