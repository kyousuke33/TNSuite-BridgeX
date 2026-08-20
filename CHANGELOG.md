# Changelog

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