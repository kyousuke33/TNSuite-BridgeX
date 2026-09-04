# TNSuite BridgeX Build12-Hotfix24 — Changelog

## P0 changes
- Restore the installer visual identity from the accepted Build12-Hotfix16 BuildKit while retaining the WiX/Burn + MSI maintenance engine introduced by the AV remediation work.
- Use the original `assets/branding/BridgeX-AppIcon.ico` directly for Setup/MSI product branding; do not regenerate the ICO with `ExtractAssociatedIcon`.
- Use the original `installer/BridgeX-Setup-Sidebar.bmp` as the WixStdBA sidebar visual and restore Welcome / install options / progress / Finish wording closer to the original installer flow.
- Add `scripts/patch_tnsuite_bridgex_hotfix24.py` to load the original multi-resolution `BridgeX-AppIcon.ico` into a `wxIconBundle` and call `SetIcons()` on the main BridgeX frame under Windows.
- Package `BridgeX-AppIcon.ico` beside `BridgeX.exe` with exact SHA-256 preservation so the runtime window/taskbar icon does not depend only on the PE resource.
- Preserve Hotfix23 behavior: fresh Install, older-version Update, same-version Repair/Uninstall, custom-drive preservation, Desktop shortcut option, finish-launch option, automatic closure of BridgeX-owned processes, no normal Files In Use/reboot path, and managed uninstall cleanup.

## QA gates
- Full Windows source compile must pass after the Hotfix24 runtime patch.
- Installed runtime icon SHA-256 must equal `06266307acb6a92aca9742dac59dd053029075256a30eec50a37a71e08296328`.
- Setup EXE icon at 32x32 must pixel-match the canonical multi-resolution ICO representation.
- Running BridgeX must expose a non-null Windows window icon handle (`WM_GETICON` / class icon fallback).
- Exact Hotfix24 Setup SHA-256 requires a new VirusTotal scan before promotion; prior 0/70 results do not transfer.

## Scope
- Build13 remains out of scope.
- No authentication, transfer protocol, SFTP credential, DB, or server behavior is changed.
