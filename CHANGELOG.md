# Changelog

## Unreleased — security release remediation
- Revoke acceptance of the published Build12-Hotfix16 Windows release after VirusTotal reported heuristic detections on the installer artifact.
- Pause automatic GitHub Release publication while installer packaging is remediated and re-verified.
- Withdraw the flagged Hotfix16 GitHub Release and its release tag without mutating or replacing the published artifact bytes.
- Clarify README wording for SHA-256 verification, exact-artifact VirusTotal reports and optional portable downloads.
- Keep Build13 out of scope; the corrected installer must use a new immutable Build12 hotfix release identity.

## Unreleased — governed repository bootstrap
- Establish desktop-specific Governed Agentic Engineering structure.
- Audit Build12-Hotfix16 BuildKit and exclude obsolete/generated audit evidence, checksum manifests and unused design exports.
- Record Hotfix16 as accepted product baseline.
- Define Build13 governed optional-update work without claiming it implemented.

## v0.5 Build12-Hotfix16
- Fixed first-restart theme/language persistence race.
- Retained association repair, installer clean-upgrade, payload hygiene, localization and CLI/SFTP foundations.