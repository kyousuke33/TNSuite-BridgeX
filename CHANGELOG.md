# Changelog

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