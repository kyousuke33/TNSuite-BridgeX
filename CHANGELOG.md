# Changelog

## Unreleased — governed roadmap execution and Build12 closure
- Make the accepted `PROJECT_BIG_PICTURE.md` → `ROADMAP.md` → `CURRENT_STATE.md` → `DECISIONS.md` chain the explicit durable execution authority for BridgeX AI/contributors.
- Require every implementation to identify the active release, phase, milestone, current blocker and next acceptance gate before mutating source.
- Record the current Build12 release-closure sequence: Hotfix24 product identity/Windows integration → Build12 Release Candidate lock → exact-hash AV/release-trust validation → code-signing foundation → production distribution → Build12 closure; Build13 remains blocked until those required Build12 gates close.
- Record active PR #28 evidence as coordination state only, not canonical-main acceptance: Hotfix24 full Windows source build passes, while the WiX build remains blocked by the generated PowerShell wrapper parser error observed in workflow run `32448690449`, job `96672917931`.
- Lock release-engineering decisions around WiX 6/Burn+MSI, bounded BridgeX process closure, preservation of user profile/settings, direct canonical multi-resolution icon use, exact-hash AV evidence and build-once/promote-same-bytes semantics.
- Preserve the RCP-managed public-repository trust boundary and existing canonical Big Picture; this governance change does not modify BridgeX runtime, transfer protocols, credentials, installer bytes or production systems.

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
