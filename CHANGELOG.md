# Changelog

## Unreleased — Build12 Hotfix25 no-reboot installer regression (QA-only, not released)
- Source-built Hotfix24 runtime is now compiled with wxWidgets 3.3.4; WiX base builder had obsolete libfilezilla-58/libfzssh-13 hardcoded while current imported DLLs are libfilezilla-60/libfzssh-16. Preserve exact two BridgeX-private DLL guards and accept only reviewed legacy 58/13 or current 60/16 pairs. Mixed, duplicated or unknown library ABI fails closed; no release authority implied.
- Windows dry-run found wxWidgets 3.3.4 DLLs (wxbase334/wxmsw334) but a hardcoded 333 static QA check. Keep the historical Build12-Hotfix16 source/manifest byte-exact: apply reviewed 3.3.3/3.3.4 ABI checks only to disposable Windows build copies via the existing release adapter and Hotfix24 QA workflow. Source-gate selftests reject unreviewed/mixed/missing wx DLLs. Windows compile success is not Owner UAT or publication authority.
- Office 2026-11-09 exact RC1 MSI log: first-time MSI registration with existing `BridgeX.exe` PID 51540 holding two `libfzclient-*.dll` files; `ForceCloseBridgeX` was skipped because its action condition required `Installed OR WIX_UPGRADE_DETECTED`.
- Correct the WiX pre-`InstallValidate` close to run for first install and maintenance; verify GUI/CLI processes are absent and fail closed rather than silently ignoring errors.
- Re-enable standard Windows Installer Restart Manager (`MSIRESTARTMANAGERCONTROL=0`); retain `MSIDISABLERMRESTART=1` to avoid auto-relaunching the application.
- Exit code `3010` is a QA failure; add Windows scenarios for fresh install over running legacy BridgeX, update, repair and uninstall, rejecting MSI reboot-scheduling evidence.
- The Hotfix25 installer QA job uses the immutable public RC1 portable ZIP as a SHA-256-pinned **test-only runtime input** to bypass expired Actions artifacts and intermittent MSYS2 downloads; this does NOT prove a fresh exact-main runtime compilation and must never be promoted as the final release artifact.
- Historical Hotfix21/22/23 installer QA now consumes the same SHA256-verified public RC1 portable input instead of expired GitHub Actions canonical-main artifacts, with explicit `QA_ONLY` provenance and unchanged functional test coverage; these are not source-build evidence.
- Windows full-build jobs prefetch pinned MSYS2 2026-06-11 installer from the official MSYS2 repository mirror with verification of the existing toolchain SHA256; release adapter and canonical build manifest remain untouched.
- These changes are source/QA only until tested on exact Windows build bytes. Do not alter public RC1 assets or publish replacement bytes using the RC1 identity.
- Scope: Build12 installer only; no product runtime, RCP, production, signing, database or Build13 changes.

## Unreleased — governed roadmap execution and Build12 closure
- Make the accepted `PROJECT_BIG_PICTURE.md` → `ROADMAP.md` → `CURRENT_STATE.md` → `DECISIONS.md` chain the explicit durable execution authority for BridgeX AI/contributors.
- Require every implementation to identify the active release, phase, milestone, current blocker and next acceptance gate before mutating source.
- Record the current Build12 release-closure sequence: Hotfix24 product identity/Windows integration → Build12 Release Candidate lock → exact-hash AV/release-trust validation → code-signing foundation → production distribution → Build12 closure; Build13 remains blocked until those required Build12 gates close.
- Record active PR #28 evidence as coordination state only, not canonical-main acceptance: Hotfix24 full Windows source build passes, while the WiX build remains blocked by the generated PowerShell wrapper parser error observed in workflow run `32448690449`, job `96672917931`.
- Lock release-engineering decisions around WiX 6/Burn+MSI, bounded BridgeX process closure, preservation of user profile/settings, direct canonical multi-resolution icon use, exact-hash AV evidence and build-once/promote-same-bytes semantics.
- Preserve the RCP-managed public-repository trust boundary and existing canonical Big Picture; this governance change does not modify BridgeX runtime, transfer protocols, credentials, installer bytes or production systems.

## Unreleased — Build12-Hotfix23 state-aware maintenance + locked update location
- Detect the highest installed BridgeX MSI version by the stable product UpgradeCode before rendering WixStdBA maintenance UX.
- First install remains **Install**; launching a newer Setup over an older BridgeX installation presents **Update**; launching the same installed Setup uses the standard **Repair / Uninstall** Modify page.
- Recover the exact existing BridgeX installation directory from Windows Installer component registration using the stable root `COPYING` component GUID `{492A8EAC-6707-51E3-9723-967A6E4A94D9}`. Updates and repairs pass that directory directly as `INSTALLFOLDER`, preventing custom D:/E: installations from falling back to C:.
- Hide the location Options control while a lower installed version is being updated. Location selection remains available for fresh installs, where the selected base still automatically creates `TNSuite\BridgeX`.
- Disable Windows Installer Restart Manager for BridgeX maintenance and run a hidden pre-`InstallValidate` WixQuietExec command that force-closes only `BridgeX.exe` and `BridgeX-CLI.exe`. No external helper executable or PowerShell runtime is shipped for process termination.
- Remove the unsupported Burn-level `util:CloseApplication` approach after WiX 6 emitted `WIX1150` binder warnings for those Bundle symbols; Hotfix23 CI now fails if any `WIX1150` warning returns.
- Add passive-mode timeout acceptance so any interactive **Files In Use** dialog becomes an automatic CI failure instead of being masked by `/quiet` execution.
- Add runtime acceptance for Hotfix22 → Hotfix23 update while BridgeX is running, custom-location preservation, same-version repair while running, same-version uninstall while running, forced process exit, managed-file cleanup and zero reboot-required exit codes.
- Preserve the canonical BridgeX runtime SHA-256, WiX Burn/MSI architecture, fresh-install location selector, automatic `TNSuite\BridgeX` subfolder, Desktop shortcut option, installer icon/branding and finish-launch option.
- User profile/settings data remains outside managed uninstall cleanup and is intentionally preserved.
- Treat Hotfix23 as new bytes; the exact Hotfix23 Setup SHA-256 must independently pass VirusTotal before promotion.
- Keep Build13 out of scope.

## Unreleased — Build12-Hotfix22 auto-close + clean uninstall
- When install, upgrade or uninstall detects `BridgeX.exe` or `BridgeX-CLI.exe` still running, use the standard WiX Util `CloseApplication` action instead of a project-specific process-kill helper.
- Send a graceful close message first and wait up to 4 seconds; if the BridgeX process is still running, terminate only that exact executable so managed files can be replaced or removed without a reboot prompt.
- Set `MSIDISABLERMRESTART=1` so Windows Installer does not independently relaunch an app it closed; the existing **Open TNSuite BridgeX when setup finishes** checkbox remains the only post-install launch authority.
- Keep `RebootPrompt=no` for BridgeX-owned process locks and add CI acceptance that installs BridgeX, leaves it running, uninstalls it, and requires the process to exit automatically without user interaction.
- Require clean uninstall of managed application files, Desktop shortcut, Start Menu entry and installer-owned `HKLM\Software\TNSuite\BridgeX` registry values. User profile/settings data is intentionally preserved.
- Re-run the same auto-close/uninstall acceptance from a custom install location to prevent regression of the Hotfix21 drive/folder selection behavior.
- Preserve the canonical BridgeX runtime hash, WiX Burn/MSI architecture, installer icon/branding, Desktop shortcut option and finish-launch option.
- Treat Hotfix22 as new bytes; the exact Hotfix22 Setup SHA-256 must independently pass VirusTotal before promotion.
- Keep Build13 out of scope.

## Unreleased — Build12-Hotfix21 installer relocation + finish options
- Fix the interactive location selector so the UI uses WixStdBA's first-class `InstallFolder` variable rather than a custom variable that did not reliably propagate the user's Browse selection during real installs/upgrades.
- Keep `InstallFolder` semantics as a **base/parent location** and pass it to MSI `INSTALLBASE`; the final product folder remains automatically authored as `TNSuite\BridgeX` below that base.
- Default remains `C:\Program Files\TNSuite\BridgeX`; selecting `D:\` resolves to `D:\TNSuite\BridgeX`, selecting `E:\` resolves to `E:\TNSuite\BridgeX`, and selecting `D:\Apps` resolves to `D:\Apps\TNSuite\BridgeX`.
- Add a default-on **Create a Desktop shortcut** checkbox in installer Options, propagated to MSI as `CREATE_DESKTOP_SHORTCUT`; when unchecked the Desktop shortcut component is not installed.
- Add a default-on **Open TNSuite BridgeX when setup finishes** checkbox on the success page. When checked, the Finish action uses WixStdBA's standard `LaunchButton`/`LaunchTarget`; when unchecked, Finish closes without launching.
- Add upgrade-relocation QA: install Hotfix20 at the default C: location, then upgrade with Hotfix21 targeting a different base folder and require the managed BridgeX executable to move to the new location instead of remaining under C:.
- Add shortcut-on / shortcut-off / uninstall cleanup QA and retain canonical BridgeX runtime SHA-256 enforcement, icon/branding, markerless legacy migration, WiX Burn/MSI architecture and no custom self-extractor/packer/obfuscation.
- Treat Hotfix21 as new bytes; prior VirusTotal 0/70 evidence does not transfer. The exact Hotfix21 Setup SHA-256 must independently reach 0 malicious / 0 suspicious before promotion.
- Keep Build13 out of scope.

## Unreleased — Build12-Hotfix20 base-location installer UX
- Change installer location semantics from selecting the complete product directory to selecting only a **drive or parent folder**.
- Add a dedicated Burn `InstallBaseFolder` variable and bind the Options edit box / Browse action to that base location.
- Add MSI `INSTALLBASE` as a public directory property above the authored `TNSuite\BridgeX` directory tree so the installer automatically creates the product subfolder instead of requiring users to type it.
- Default behavior remains `C:\Program Files\TNSuite\BridgeX`.
- Required examples: selecting `D:\` resolves to `D:\TNSuite\BridgeX`; selecting `E:\` resolves to `E:\TNSuite\BridgeX`; selecting `D:\Apps` resolves to `D:\Apps\TNSuite\BridgeX`.
- Add a custom WiX Standard BA theme that labels the field as a drive/parent-folder selector and explicitly states that `TNSuite\BridgeX` is created automatically.
- Add CI acceptance for drive-root and nested parent-folder selections, including guards that fail if payload files are installed directly into the selected base folder.
- Preserve BridgeX Setup EXE icon/branding, canonical BridgeX runtime SHA-256 enforcement, markerless legacy migration behavior and the WiX/Burn + MSI architecture.
- Treat Hotfix20 as new bytes. Previous VirusTotal results, including Hotfix18 0/70, do not transfer; the exact Hotfix20 Setup SHA-256 must independently reach 0 malicious / 0 suspicious before promotion.
- Keep Build13 out of scope.

## Unreleased — Build12-Hotfix19 WiX installer UX
- Keep the WiX Toolset 6 / Burn + MSI installer architecture after the exact Build12-Hotfix18 Setup SHA-256 `63de8ee9bd53c8e215e45599b52703df4dfde839efdfc3f7c0aef868ebbedb2b` was user-verified at VirusTotal with 0/70 detections.
- Add the BridgeX application icon to the final Setup EXE and Windows installer product identity, derived from the canonical BridgeX executable rather than introducing unrelated branding assets.
- Enable WiX Standard Bootstrapper Options UI so users can browse and choose the install location; propagate the selected Burn `InstallFolder` variable into the MSI `INSTALLFOLDER` property.
- Add BridgeX logo treatment, visible version information, and post-install launch target while retaining the standard WiX/Burn execution model.
- Add CI acceptance for both the default Program Files location and an explicit custom install location, including installed BridgeX SHA-256 verification, runtime launch, uninstall and legacy-file preservation.
- Retain markerless legacy-folder migration and never recursively delete an unverified existing BridgeX directory.
- Keep no custom self-extractor, no packer, no obfuscation, no installer-side PowerShell runtime and no installer-side process-kill behavior.
- Treat Hotfix19 as new bytes: the Hotfix18 0/70 VirusTotal evidence does not transfer to Hotfix19. The exact Hotfix19 Setup SHA-256 must independently reach 0 malicious / 0 suspicious before promotion.
- Keep Build13 out of scope.

## Unreleased — Build12-Hotfix17 security release remediation
- Revoke acceptance of the published Build12-Hotfix16 Windows release after VirusTotal reported heuristic detections on the installer artifact.
- Withdraw the flagged Hotfix16 GitHub Release and its release tag without mutating or replacing the published artifact bytes.
- Move the corrected distribution identity to **v0.5 Build12-Hotfix17**; the withdrawn Hotfix16 tag and artifact names must never be reused for changed bytes.
- Remove the installer/uninstaller PowerShell helper, `ExecutionPolicy Bypass` invocation and automatic process termination behavior.
- Replace solid LZMA NSIS packing with standard zlib compression to reduce heuristic-sensitive installer behavior while keeping marker-verified, fail-closed upgrade/uninstall handling.
- Build Hotfix17 as `TNSuiteBridgeX_260820_v0.5-Build12-Hotfix17-Full` while preserving the accepted Build12-Hotfix16 product-source lineage and regression coverage.
- Keep automatic GitHub Release publication paused. Protected `main` first produces immutable build evidence; publication is a separate promotion step that reuses those exact bytes.
- Require SHA-256 and a VirusTotal URL that resolves to the exact SHA-256 for both installer and portable artifacts before promotion; malicious and suspicious counts must both be zero.
- Verify the source SHA belongs to protected `main`, the supplying Actions run is a successful `push` run on `main`, and the published assets hash-identically match the scanned canonical-main artifacts.
- Clarify README wording for SHA-256 verification, exact-artifact VirusTotal reports and optional portable downloads.
- Keep Build13 out of scope.

## Unreleased — governed repository bootstrap
- Establish desktop-specific Governed Agentic Engineering structure.
- Audit Build12-Hotfix16 BuildKit and exclude obsolete/generated audit evidence, checksum manifests and unused design exports.
- Record Hotfix16 as accepted product baseline before the later distribution withdrawal.
- Define Build13 governed optional-update work without claiming it implemented.

## v0.5 Build12-Hotfix16 — withdrawn
- Fixed first-restart theme/language persistence race.
- Retained association repair, installer clean-upgrade, payload hygiene, localization and CLI/SFTP foundations.
- Distribution status: **withdrawn** after VirusTotal heuristic detections were reported on the published installer artifact. Do not redistribute the withdrawn installer.
