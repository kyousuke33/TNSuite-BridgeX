# TNSuite BridgeX — Decisions

This file records durable decisions that an AI or contributor must not silently reopen while executing the roadmap. A material reversal requires an explicit governed proposal with evidence, impact, migration/rollback plan and approval where policy requires it.

## Historical product/governance decisions

### GOV-001 — Canonical source authority
**Status:** LOCKED

GitHub `main` becomes canonical source only after the exact governed bootstrap import/PR merge. Chat, local build folders and generated BuildKit audit/evidence files are not canonical source authority.

### PRODUCT-001 — Build12 baseline before future feature builds
**Status:** LOCKED

Build12-Hotfix16 is the historical accepted product baseline. Its later installer distribution withdrawal does not erase the accepted product behavior baseline.

Build13 is the next feature-build family, but **Build13 feature implementation is blocked until the Build12 release-closure gates in `docs/00_PRODUCT/ROADMAP.md` are completed**. Release hardening must not silently absorb Build13 features.

### RUNTIME-001 — Desktop truth model
**Status:** LOCKED

Desktop runtime acceptance uses Windows launch/GUI/transfer/installer evidence, not web-health semantics. Source/static QA cannot be promoted to GUI/runtime PASS without the required Windows evidence.

### QA-001 — Historical regression scripts
**Status:** LOCKED UNTIL SEPARATE SEMANTIC-QA REFACTOR

Active historical-named regression scripts remain in place while they still enforce accepted behavior. Do not rename/remove them opportunistically during release hardening.

### UPDATE-001 — Central update authority
**Status:** LOCKED

Optional desktop auto-update is mediated by governed RCP/Portal publication. The client does not treat GitHub or an arbitrary download URL as trusted update authority.

---

## Current release-engineering decisions

### INSTALLER-001 — Standard Windows installer architecture
**Status:** LOCKED

Use **WiX Toolset 6 + Burn + MSI** for the governed Windows installer lifecycle.

Do not reintroduce as a shortcut:
- NSIS for the production remediation line;
- custom self-extracting installers;
- packers or obfuscators;
- AV-evasion/bypass techniques;
- installer-side PowerShell runtime helpers.

Reason: the release-remediation work requires standard Windows installer semantics, evidenceable maintenance behavior and lower heuristic-sensitive custom execution surface.

### INSTALLER-002 — Preserve user profile/settings on managed uninstall
**Status:** LOCKED

Normal Update / Repair / Uninstall owns program files and installer metadata only. BridgeX user profile/settings/credentials/site configuration outside managed program files are preserved unless a future separately governed remove-user-data option explicitly changes that contract.

### INSTALLER-003 — Bounded process closure during maintenance
**Status:** LOCKED

Maintenance may automatically close only the exact BridgeX-owned executable names required by the accepted installer design:

```text
BridgeX.exe
BridgeX-CLI.exe
```

No wildcard process matching. No external custom process-kill helper executable. Any change to this list requires evidence that the additional process is BridgeX-owned and necessary for correct maintenance.

### BRAND-001 — Canonical Windows application icon
**Status:** LOCKED

Canonical icon authority:

```text
assets/branding/BridgeX-AppIcon.ico
```

The multi-resolution ICO must be consumed directly for product/installer/window identity. Do not regenerate the production icon with `ExtractAssociatedIcon(BridgeX.exe)` or another extraction/resave path that collapses the original resolution set.

### BRAND-002 — Installer identity may change implementation, not product identity
**Status:** LOCKED

The production installer may use WiX/Burn + MSI even though the accepted Hotfix16 BuildKit used NSIS. The architecture migration must not unnecessarily discard the accepted BridgeX visual/product identity. Where technically compatible, installer wording/branding should remain recognizably BridgeX while maintenance semantics stay standard and testable.

### TRUST-001 — AV evidence is exact-hash evidence
**Status:** LOCKED

VirusTotal/AV evidence applies only to the exact bytes/SHA-256 scanned. A clean result for an older Setup/MSI/portable artifact does not transfer to a rebuilt or modified candidate.

A failed AV result must not be “fixed” through evasion, packing, obfuscation or disabling security controls.

### RELEASE-001 — Build once, verify, promote the same bytes
**Status:** LOCKED

The release chain is:

```text
canonical source SHA
→ build
→ immutable candidate artifact
→ exact runtime/installer/security evidence
→ promotion of the same artifact bytes
```

Do not rebuild between acceptance and publication and call the rebuilt bytes equivalent.

### RELEASE-002 — Build12 Release Candidate lock precedes production distribution
**Status:** LOCKED

After Hotfix24 satisfies its exit gate, bind one Build12 Release Candidate to exact source/runtime/MSI/Setup hashes and acceptance evidence. Any byte change creates a new candidate and invalidates downstream exact-hash evidence.

This lock exists specifically to stop an indefinite Hotfix loop without a defined release-completion point.

### SIGNING-001 — Code signing precedes production-grade secure auto-update
**Status:** ROADMAP-LOCKED; IMPLEMENTATION NOT YET VERIFIED

Production-grade secure auto-update must not be implemented ahead of the publisher/signing, artifact-trust and governed-distribution foundation. Signing secrets must never be exposed to public PR CI.

### ROADMAP-001 — No phase drift
**Status:** LOCKED

Until Build12 is CLOSED by the roadmap exit gates:

```text
BUILD13=BLOCKED_UNTIL_BUILD12_CLOSED
```

AI/contributors must work on the first unmet acceptance criterion of the active milestone. Unrelated refactors, speculative features and later-phase work require their own governed work item rather than being folded into the current blocker fix.
