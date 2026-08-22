# TNSuite BridgeX — Governed Agentic Engineering Authority

## Authority order
1. TNSuite Release Control Plane normative contracts/policies.
2. TNSuite Platform Contracts when applicable.
3. This repository `main` after the governed bootstrap source import is merged.
4. Runtime/build evidence bound to exact source/artifact identity.
5. Chat is execution context, never durable authority.

## Product boundary
BridgeX is an independent Windows x64 desktop application derived from FileZilla Client 3.70.6. It is not an official FileZilla product and must not be represented as one.

## Engineering flow
Work item → short-lived branch → source/local QA → PR → required CI → merge exact green head → immutable artifact → RCP verification → governed publication.

## Desktop truth model
Do not invent web health semantics. Source QA proves source only. Windows compile/link/package proves build only. Installer acceptance proves install/upgrade/uninstall only. GUI, Light/Dark, EN/VI and SFTP acceptance require real Windows runtime evidence. Production means publication of an exact verified desktop artifact through an approved distribution channel, not a long-running VPS process.

## Central CI authority
BridgeX is a public repository and MUST consume the central RCP trust boundary `tnsuite.ci-public-repository-trust.v1` together with `tnsuite.ci-runner-host-layout.v1` where applicable. Project-local docs/workflows MUST NOT redefine or weaken those central rules.

Current mandatory posture:

```text
PUBLIC_REPOSITORY=true
SHARED_SELF_HOSTED_CI=PROHIBITED
UNTRUSTED_PR_RUNNER=GITHUB_HOSTED_ONLY
TN_CI_01_ACCESS=NONE
PRODUCTION_ACCESS=NONE
DATABASE_EXECUTION=NOT_PERFORMED
```

BridgeX pull requests, fork pull requests and external contributor code run only on GitHub-hosted infrastructure. `pull_request_target` must not checkout or execute untrusted PR-head code. A future self-hosted runner is allowed only if BridgeX becomes private and is re-onboarded, or if a separately governed dedicated disposable/ephemeral public runner is isolated from `tn-ci-01` and all trusted TNSuite runners.

## Safety
Never commit generated installers/portable archives, build caches, local MSYS2/wxWidgets trees, runtime logs, tokens, signing keys or generated QA evidence. Public CI must not receive production/staging/database/signing/release credentials or TNSuite internal tokens. Build once and publish the exact verified artifact. Update checks may fail open for normal app use, but artifact verification must fail closed before execution.

## Repository-specific roadmap execution contract

This section operationalizes the project roadmap without weakening any centrally managed rule below.

### Mandatory discovery before implementation

Before making or proposing a source/build/release mutation, read and reconcile in this order:

1. `docs/00_PRODUCT/PROJECT_BIG_PICTURE.md` — stable product North Star and phase model.
2. `docs/00_PRODUCT/ROADMAP.md` — durable ordered milestones and exit gates.
3. `docs/90_GOVERNANCE/CURRENT_STATE.md` — live execution cursor, exact blocker and next gate.
4. `docs/90_GOVERNANCE/DECISIONS.md` — durable LOCKED decisions that must not be silently reopened.
5. relevant `CHANGELOG.md`, work-item/PR evidence and actual GitHub/CI/runtime state.

Chat memory may help locate evidence but must never replace this chain.

### Required execution cursor

Before changing code, explicitly determine:

```text
ACTIVE_RELEASE
ACTIVE_PHASE
ACTIVE_MILESTONE
CURRENT_BLOCKER
NEXT_ACCEPTANCE_GATE
```

If these cannot be determined from canonical authority plus actual repository/CI state, reconcile `CURRENT_STATE.md` before opening unrelated implementation work.

### Scope discipline

Every implementation must answer all three questions:

1. Which active roadmap milestone does this advance?
2. Which acceptance criterion or blocker does it satisfy?
3. What exact evidence will prove it?

If the change does not advance the active milestone, do not silently add it to the current workstream. Create/route a separate governed work item or leave it deferred.

Do not:
- start a later roadmap phase while an earlier required exit gate is unmet;
- mix Build13 features into Build12 release hardening;
- opportunistically refactor unrelated code while fixing a bounded blocker;
- reopen a decision marked `LOCKED` without an explicit governed proposal;
- replace exact evidence with assumptions from a previous build/hash;
- mark active-PR evidence as canonical-main acceptance before the relevant source is safely merged.

### Actual-state reconciliation

Repository, CI and runtime evidence win over stale coordination prose. If actual state contradicts `CURRENT_STATE.md`:

1. capture the exact source/PR/run/job/artifact evidence;
2. update the live execution cursor to reflect reality;
3. continue from the first unmet acceptance gate;
4. do not replay already evidenced work merely because an older document is stale.

### State maintenance

After a meaningful state transition:
- update `CURRENT_STATE.md` when the active cursor, blocker, evidence or next gate changes;
- update `CHANGELOG.md` when product/source/release behavior changes materially;
- update `ROADMAP.md` only when durable ordering, scope or exit criteria change;
- update `DECISIONS.md` only for durable accepted decisions, not transient debugging notes;
- keep `PROJECT_BIG_PICTURE.md` stable unless product purpose/direction materially changes through governance.

<!-- TNSUITE:RCP-MANAGED-AGENTS:BEGIN -->
TNSUITE_CENTRAL_AUTHORITY_PREFLIGHT=REQUIRED
USER_PROMPT_GOVERNANCE_DEPENDENCY=NONE
PROJECT_LOCAL_CENTRAL_AUTHORITY_WEAKENING=PROHIBITED
GITHUB_MAIN_CANONICAL_SOURCE=REQUIRED
PROJECT_MUTATION_SCOPE=SELF_ONLY
CROSS_PROJECT_MUTATION=PROHIBITED
CROSS_PROJECT_DEFECT_REQUEST_REQUIRES_PROVEN_OWNERSHIP=REQUIRED
UNKNOWN_DEFECT_RCP_TRIAGE=REQUIRED
VALID_EXTERNAL_REQUEST_MUST_BE_REVIEWED=REQUIRED
RESOLUTION_CALLBACK_TO_REQUESTER=REQUIRED
REQUESTER_REVALIDATION_AND_AUTO_RESUME=REQUIRED
CENTRAL_CAPABILITY_GAP_PROJECT_WORKAROUND=PROHIBITED
CI_HOST_RUNTIME_AUTHORITY=NONE
BUILD_ONCE_PROMOTE_SAME_ARTIFACT=REQUIRED
PASS_WITHOUT_REQUIRED_EVIDENCE=PROHIBITED
PROJECT_ROADMAP_GOVERNANCE=tnsuite.project-roadmap-governance.v1
PROJECT_DEVELOPMENT_AUTHORITY=PROJECT
PROJECT_DEVELOPMENT_LANE_AUTONOMY=REQUIRED
CENTRAL_BLOCK_SCOPE=DEPENDENT_SCOPE_ONLY
CENTRAL_DEPENDENCY_BLOCK_SCOPE=AFFECTED_SCOPE_ONLY
UNRELATED_PROJECT_WORK_MUST_CONTINUE=REQUIRED
UNRELATED_WORKSTREAM_AUTO_CONTINUE=REQUIRED
CI_RUNNER_CONTRACT_SELF_SERVICE=ALLOWED
CI_RUNNER_PROVISIONING_RELEASE_APPROVAL=NOT_REQUIRED
PROJECT_SOURCE_BUILD_RCP_GATE=NONE
PROJECT_BUILD_RCP_APPROVAL=NOT_REQUIRED
PROJECT_MERGE_RCP_APPROVAL=NOT_REQUIRED
PROJECT_BIG_PICTURE_DISCOVERY=REQUIRED
PROJECT_ROADMAP_DISCOVERY=REQUIRED
PROJECT_CURRENT_STATE_DISCOVERY=REQUIRED
ROADMAP_ACTUAL_STATE_WINS=REQUIRED
ROADMAP_CHAT_MEMORY_AUTHORITY=NONE
ROADMAP_ENABLED_AUTO_RESUME=REQUIRED
TNSUITE_AGENTS_SYNC=RCP_MANAGED
TNSUITE_AGENTS_POLICY_REVISION=2026-08-22.1

Central managed execution rules:
1. The project is product/source authority for its own repository. Ordinary requirement implementation, source edits, branches, Pull Requests, project CI, safe merge, exact-SHA build/artifact creation and local/dev validation do not require separate RCP release approval.
2. Before managed implementation, load project-local authority and run the centrally versioned TNSuite Authority Preflight only for declared shared-authority subscriptions that the affected scope actually consumes; an unavailable unrelated central capability must not block independent source/CI/build work.
3. An agent may mutate only its own repository/project scope. It may inspect other governed repositories read-only when necessary for diagnosis, but must not edit another project to unblock itself.
4. A compliant dedicated CI runner is project CI infrastructure. It may be provisioned or maintained without RCP release registration, staging-target registration or Production approval when it conforms to the central CI host contract and has no Production authority.
5. Create or reuse a governed cross-project defect request only when evidence proves the defect is owned by the target project. The request must identify the requester, exact dependent work item/capability/release/Production scope, observed and expected behavior, exact evidence/source references, ownership rationale and required outcome.
6. When ownership is UNKNOWN or only suspected, do not assign blame or request a fix from another project. Escalate a diagnostic request to RCP. RCP may investigate across relevant projects and central authorities read-only, establish ownership, coalesce related failures and recommend routing, but must not mutate child-project source during triage.
7. A project receiving a valid external request must independently review the evidence and classify it as ACCEPTED, REJECTED_NOT_OWNED, NEEDS_MORE_EVIDENCE, DUPLICATE or SUPERSEDED. An accepted request is tracked through the receiver's own governed work item, source QA, PR, required CI and safe merge.
8. A proven central capability gap blocks only the minimum affected scope. Create or reuse the central dependency, mark the exact dependent work item/capability/release/Production scope blocked, release that active lane if appropriate, and keep unrelated workstreams schedulable. Do not normalize a scoped dependency into a project-wide block unless whole-project impact is separately proven.
9. Do not build a project-local shadow control plane, duplicated central protocol or competing multi-project release/artifact/approval/scheduler authority. Safe project-local build, test and deploy hooks remain allowed inside project and environment authority.
10. After an accepted external request is resolved, publish a resolution callback containing the request id, receiver project, resolution work item/PR, exact resolution source SHA, capability or fix identity and revalidation requirement. The requester must revalidate only the affected scope before marking the dependency resolved; independent scopes never wait for this callback.
11. For every repository classified roadmap_enabled=true, recover project intent in this order: AGENTS.md, PROJECT_BIG_PICTURE.md, ROADMAP.md, CURRENT_STATE.md, relevant evidence, live Work Item, then actual GitHub/CI/runtime state. Reconcile stale prose before mutation; actual state wins and chat memory is not authority.
12. PROJECT_BIG_PICTURE.md is stable product-direction authority and must not become a moving PR/SHA/CI/blocker cursor. ROADMAP.md is ordered durable planning authority and must not replace CURRENT_STATE.md or the live Work Item.
13. Do not fabricate PROJECT_BIG_PICTURE.md or ROADMAP.md for a repository classified DEFERRED because source/product authority is not established. Keep the repo explicitly deferred until evidence supports roadmap enablement.
14. When the repository has a deterministic canonical roadmap/current-state chain, continue ordinary roadmap work autonomously through source QA, PR, required CI, safe merge and the next independent phase/workstream without waiting for a new user prompt.
15. Human approval remains required only where canonical policy requires a real privileged or risk decision, including Production promotion, Production database mutation, destructive operations, unavailable real-host secret/root access, material security/architecture decisions, or unresolved product decisions.
16. Platform Contract incompatibility blocks only scopes that consume the incompatible contract. A project may pin a compatible immutable contract version/SHA and continue independent engineering work.
17. Never claim SOURCE_PASS, ARTIFACT_READY, STAGING_PASS, LIVE_PASS, DONE or equivalent without the evidence level required by project and central authority.
<!-- TNSUITE:RCP-MANAGED-AGENTS:END -->
