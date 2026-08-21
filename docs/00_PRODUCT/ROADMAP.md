# TNSuite BridgeX — Roadmap

Stable product direction is defined by [`PROJECT_BIG_PICTURE.md`](PROJECT_BIG_PICTURE.md). This roadmap orders durable desktop/release/update maturity. Exact current branch, PR, source SHA, CI run, blocker and artifact state belong in `docs/90_GOVERNANCE/CURRENT_STATE.md`, evidence and live Work Items.

## Roadmap execution rule

The roadmap is sequential unless an explicit governed decision changes it. An AI or contributor must not open a later product phase merely because it is technically convenient.

For every implementation task, determine first:

```text
ACTIVE_RELEASE
ACTIVE_PHASE
ACTIVE_MILESTONE
CURRENT_BLOCKER
NEXT_ACCEPTANCE_GATE
```

Then work only on the first unmet acceptance criterion that advances the active milestone. Actual repository/CI/runtime evidence overrides stale prose; reconcile `CURRENT_STATE.md` when they disagree.

---

## P0 — Secure desktop baseline and Build12 release closure

**Goal:** turn the accepted Build12 product baseline into a governed, reproducible, production-distributable Windows x64 desktop artifact while preserving public-repository trust and desktop security boundaries.

### P0.A — Canonical source and governance

**Status:** DONE on `main`.

Required outcomes:
- GitHub `main` is canonical source authority;
- public/untrusted PR execution stays GitHub-hosted only;
- no private/self-hosted TNSuite runtime privilege leaks into public PRs;
- source governance and baseline regression checks remain required.

### P0.B — Build12 product baseline

**Status:** DONE as historical accepted baseline; later installer distribution was withdrawn after AV heuristic findings.

Required outcomes retained from the accepted baseline:
- secure connection/file-transfer/CLI paths remain functional;
- bilingual Light/Dark/product behavior remains coherent;
- user settings/profile remain outside managed program files and survive normal installer maintenance unless a separately governed remove-data feature exists.

### P0.C — Reproducible Windows build and installer lifecycle remediation

**Status:** EVIDENCED IN ACTIVE IMPLEMENTATION PR; NOT ACCEPTED ON `main` UNTIL MERGED.

Implementation workstream: PR #28 (`fix/native-installer-av-20260820`).

Required outcomes:
- full Windows runtime is rebuilt from canonical source rather than relying on an opaque prior EXE;
- installer architecture is standard WiX Toolset 6 / Burn + MSI;
- fresh install, older-version update, same-version repair/uninstall and managed cleanup have exact Windows runtime evidence;
- custom install locations remain stable across maintenance;
- normal BridgeX-owned file locks do not create Files In Use/reboot UX;
- no custom SFX, packer/obfuscation or installer-side PowerShell runtime is introduced.

Historical active-PR evidence may be recorded in `CURRENT_STATE.md`, but it does not become canonical-main acceptance merely by existing in a PR.

### P0.D — Product identity and Windows integration

**Status:** ACTIVE.

**Active milestone:** `Build12-Hotfix24`.

Objective: restore coherent BridgeX product identity after the installer architecture remediation without regressing the accepted maintenance behavior.

Acceptance criteria:
- full Windows source compile passes with the Hotfix24 runtime patch;
- Setup/MSI use the canonical multi-resolution `assets/branding/BridgeX-AppIcon.ico` directly;
- no `ExtractAssociatedIcon` regeneration is used for the final installer icon;
- running BridgeX exposes a valid Windows main-window/taskbar icon from the canonical icon bundle;
- installer visual identity remains consistent with the accepted Hotfix16 BuildKit direction while using WiX/Burn + MSI;
- Desktop shortcut and launch-after-install options work;
- Install / Update / Repair / Uninstall, custom-location preservation and BridgeX process-close behavior do not regress;
- `WIX1150=NONE` for the accepted candidate.

**Exit gate:** `HOTFIX24_GREEN` with exact source/run/artifact evidence.

### P0.E — Build12 Release Candidate lock

**Status:** BLOCKED BY P0.D.

Objective: stop the indefinite Hotfix loop and bind one candidate to an exact evidence chain.

Required evidence:

```text
SOURCE_SHA
→ WINDOWS_BUILD_EVIDENCE
→ RUNTIME_ARTIFACT_SHA256
→ MSI_SHA256
→ SETUP_EXE_SHA256
→ INSTALL/UPDATE/REPAIR/UNINSTALL_ACCEPTANCE
→ ICON/TASKBAR_ACCEPTANCE
```

The resulting bytes are the Build12 Release Candidate. Any byte change after lock creates a new candidate and invalidates downstream exact-hash evidence.

### P0.F — AV / release trust validation

**Status:** BLOCKED BY P0.E.

Required outcomes:
- VirusTotal or equivalent approved evidence resolves to the exact final Setup SHA-256;
- prior clean/scanned hashes do not transfer to changed bytes;
- no AV-evasion, packing, obfuscation or heuristic-bypass technique is introduced;
- failed validation returns the workstream to the earliest owning acceptance criterion rather than spawning unrelated installer architectures.

### P0.G — Code-signing foundation

**Status:** NOT VERIFIED / BLOCKED BY RC TRUST VALIDATION.

Required outcomes before production-grade update automation:
- approved publisher/signing identity;
- Authenticode signing policy for app and installer artifacts;
- trusted timestamping policy;
- signing evidence bound to the exact promoted artifact;
- signing secrets remain outside public PR CI.

### P0.H — Production distribution

**Status:** NOT CONNECTED.

Required outcomes:
- approved desktop distribution channel/profile;
- publication promotes the exact verified artifact rather than rebuilding it;
- release metadata binds source SHA, artifact hashes, version and evidence;
- publication/revocation semantics are governed and auditable.

### P0 exit — Build12 CLOSED

Build12 is closed only when the required P0 gates above are accepted. Until then:

```text
BUILD13=BLOCKED_UNTIL_BUILD12_CLOSED
```

No Build13 feature work may be silently mixed into Build12 release hardening.

---

## P1 — Governed desktop update foundation

**Status:** NOT STARTED.

Goal: make updates an exact artifact-governed flow rather than an unverified version download.

Target flow:

```text
canonical GitHub source/CI
→ immutable Windows artifact
→ code signing / release trust verification
→ central release verification
→ Portal/admin publication
→ signed/verified update manifest + artifact distribution
→ BridgeX update UX
```

Required outcomes:
- update identity binds exact source/artifact;
- client verifies publication/artifact trust before install;
- no arbitrary caller-supplied update executable/path;
- failure leaves the existing install recoverable;
- secure auto-update is not implemented ahead of the signing/release-trust/distribution foundation.

---

## P2 — Rollout and recovery controls

**Status:** NOT STARTED.

Goal: operate desktop updates safely.

Required outcomes:
- staged rollout cohorts where needed;
- pause/supersede/revoke semantics;
- retry/failure/recovery state;
- rollback or safe previous-version recovery policy;
- release/update evidence and audit.

---

## P3 — Product/operational maturity and future feature builds

**Status:** NOT STARTED.

Goal: improve the desktop product from real usage after the Build12 release foundation is closed.

Potential work:
- Build13 product capabilities under a separately approved work item;
- transfer reliability/performance metrics;
- accessibility and UX refinement;
- installer/update analytics with privacy-safe semantics;
- additional bounded CLI/SFTP capability only when product need is proven.

Build13 is not automatically authorized merely because P3 exists. Its scope must be defined after Build12 closure and must not weaken the accepted Big Picture or locked architecture decisions.

---

## Completion rule

A build/version string, passing source test, or previous artifact scan does not prove release eligibility. Exact source/artifact identity plus the evidence required by the active exit gate govern all PASS, RC, release and update claims.
