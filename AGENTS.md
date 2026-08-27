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
ACTIVE_PROJECT_SCOPE_LOCK=REQUIRED
PROJECT_CHAT_MUTATION_SCOPE=ACTIVE_PROJECT_ONLY
PROJECT_MUTATION_SCOPE=SELF_ONLY
CROSS_PROJECT_MUTATION=PROHIBITED
CROSS_PROJECT_READ_FOR_DIAGNOSIS=ALLOWED
CROSS_PROJECT_FIX_FROM_FOREIGN_WORKSTREAM=PROHIBITED
EXTERNAL_DEFECT_ROUTE_TO_OWNER_WORK_ITEM=REQUIRED
EXTERNAL_DEPENDENCY_HANDOFF=REQUIRED
RCP_MUTATION_FROM_CHILD_PROJECT_WORKSTREAM=PROHIBITED
CHILD_PROJECT_MUTATION_FROM_RCP_TRIAGE=PROHIBITED
SCOPE_EXPANSION_REQUIRES_EXPLICIT_USER_SWITCH=REQUIRED
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
PROJECT_CI_WORKFLOW_GOVERNANCE=tnsuite.project-ci-workflow-governance.v1
PROJECT_CI_WORKFLOW_HARD_MAX=5
DUPLICATE_VERSIONED_DEBUG_WORKFLOWS=PROHIBITED
CI_COVERAGE_REDUCTION_FOR_FILE_COUNT=PROHIBITED
STAGING_ACTIVE_RELEASE_GATE=RETIRED
STAGING_PASS_ACTIVE_PREREQUISITE=NONE
NEW_STAGING_PROVISIONING=PROHIBITED
DIRECT_TARGET_POST_BUILD_FLOW=REQUIRED
PROJECT_BIG_PICTURE_DISCOVERY=REQUIRED
PROJECT_ROADMAP_DISCOVERY=REQUIRED
PROJECT_CURRENT_STATE_DISCOVERY=REQUIRED
ROADMAP_ACTUAL_STATE_WINS=REQUIRED
ROADMAP_CHAT_MEMORY_AUTHORITY=NONE
ROADMAP_ENABLED_AUTO_RESUME=REQUIRED
USER_REQUEST_TO_UAT_LOOP=REQUIRED
OPERATOR_COMMAND_HOST_LABEL=REQUIRED
OPERATOR_COMMAND_ONE_BLOCK_PER_HOST_STEP=REQUIRED
CROSS_HOST_COMMAND_BLOCK_MERGE=PROHIBITED
SSH_SESSION_SELF_TERMINATION=PROHIBITED
OPERATOR_SCRIPT_FAIL_CLOSED_SESSION_PRESERVING=REQUIRED
PRODUCTION_BACKUP_BEFORE_RISKY_MUTATION=REQUIRED
ROLLBACK_PATH_REQUIRED=REQUIRED
DATABASE_DATA_LOSS_GUARD=REQUIRED
VPS_TEMP_ARTIFACT_CLEANUP=REQUIRED
UNMANAGED_VPS_GARBAGE=PROHIBITED
COMMAND_HANDOFF_IS_NOT_DONE=REQUIRED
USER_OUTPUT_REVALIDATION=REQUIRED
DEPLOYMENT_CLOSURE_AUTO_CONTINUE=REQUIRED
LIVE_CHECK_BEFORE_UAT=REQUIRED
OWNER_UAT_FINAL_ACCEPTANCE=REQUIRED
UAT_DEFECT_REENTERS_ENGINEERING_LOOP=REQUIRED
TNSUITE_AGENTS_SYNC=RCP_MANAGED
TNSUITE_AGENTS_POLICY_REVISION=2026-08-27.1

Central managed execution rules:
1. The project is product/source authority for its own repository. Ordinary requirement implementation, source edits, branches, Pull Requests, project CI, safe merge, exact-SHA build/artifact creation and local/dev validation do not require separate RCP release approval.
2. Before managed implementation, load project-local authority and run the centrally versioned TNSuite Authority Preflight only for declared shared-authority subscriptions that the affected scope actually consumes; an unavailable unrelated central capability must not block independent source/CI/build work.
3. The active project for a conversation/workstream is the only mutation scope. Autonomous execution, auto-resume and blocker repair are permitted only inside that active project scope and may not expand it for convenience.
4. A project workstream may inspect other projects, but it may never implement, deploy, or mutate them. Cross-project problems are routed to their owner; they are not fixed from the foreign workstream.
5. Before every mutation, ask whether the mutation belongs to the active project. If the answer is NO or UNKNOWN, mutation is prohibited and the action is limited to read-only diagnosis or governed handoff metadata.
6. Cross-project read-only inspection is allowed only as needed to verify a dependency, compare a contract/policy, establish defect ownership or collect evidence for the active project. Creating or updating a governed dependency/request Work Item at the proven owner is routing metadata, not permission to implement there.
7. When the active project detects an external problem: diagnose read-only, establish ownership, create or reuse the governed owner request, record exact evidence plus affected scope and resume condition, block only the dependent scope, continue unrelated active-project work, and stop cross-project implementation.
8. A child-project workstream must not mutate RCP source/runtime, and an RCP diagnostic/triage workstream must not mutate child-project source/runtime. Runtime restart/deploy/service mutation is implementation and follows the same active-project scope lock.
9. Mutation scope changes only when the user explicitly switches project, a new project workstream is explicitly started, or a canonical handoff explicitly rebinds the active project. After a scope switch, load the new project's AGENTS.md and current authority before mutation; never infer a switch merely because a dependency blocks progress.
10. If active-project scope lock conflicts with auto-resume or autonomous convenience, the priority is ACTIVE_PROJECT_SCOPE_LOCK over AUTO_RESUME over CONVENIENCE.
11. A compliant dedicated CI runner is project CI infrastructure. It may be provisioned or maintained without RCP release registration, target registration or Production approval when it conforms to the central CI host contract and has no Production authority.
12. Project CI workflow topology must conform to tnsuite.project-ci-workflow-governance.v1: responsibility-driven consolidation, normally 2-5 active workflow files according to real responsibilities, hard maximum 5 unless an explicit architecture exception exists, no duplicate/versioned/debug workflow owners, always-present required PR checks, and no coverage reduction merely to lower workflow count. A simpler project may remain at 1-2 workflows when all required coverage is preserved.
13. Staging is retired from the active TNSuite release architecture. Do not provision, onboard, enable or require a Staging environment or STAGING_PASS for new releases. Preserve historical staging evidence as historical evidence only. After exact-SHA build/artifact, continue to the separately authorized target deployment/publication and target runtime/live acceptance while preserving all Production, DB, destructive-operation, secret/root and security gates.
14. For an owner request to fix or build the active project, continue the governed lane from authority recovery through scoped GitHub implementation, source QA, Pull Request, exact-head required CI, safe merge, exact-SHA immutable artifact, authorized direct-target runtime verification, live acceptance and owner UAT without waiting for repetitive continue prompts when the next action is machine-authorized.
15. When a protected host action requires the owner to run commands, identify the exact VPS/host in the command block. Commands for one same-host step must be grouped into one copyable block; commands for different hosts must be separated and must never be merged into one ambiguous block.
16. Owner-run command blocks must fail closed while preserving the SSH session: do not intentionally exit/logout the shell, do not hide failed checks behind unconditional PASS output, do not expose secrets, and do not perform unrelated project or host mutation.
17. Risky Production/runtime mutation must be backup-aware and rollback-aware before mutation. Database/destructive operations require explicit authority, data-loss guards and a recovery path; ordinary deployment authority never implicitly grants DB, destructive or root authority.
18. Operator scripts and host commands must use bounded project-authorized paths and clean up temporary candidates, downloads and transient artifacts they create when safe to do so. Unmanaged persistent garbage on shared VPS/CI hosts is prohibited; cleanup must never recurse into sibling project, protected runtime, backup, database or user-data roots.
19. Providing an operator command block is a handoff, not task completion. After the owner returns command output, revalidate the exact evidence, repair the active-project source or release lane when needed, and continue until the required deploy/runtime/live acceptance is proven or a genuine protected human decision remains.
20. Owner UAT is the final product acceptance layer when applicable. A reported UAT defect re-enters the same active-project governed engineering loop; do not mark DONE until the required source/build/deploy/live evidence and owner acceptance are satisfied.
21. Create or reuse a governed cross-project defect request only when evidence proves the defect is owned by the target project. The request must identify the requester, exact dependent work item/capability/release/Production scope, observed and expected behavior, exact evidence/source references, ownership rationale and required outcome.
22. When ownership is UNKNOWN or only suspected, do not assign blame or request a fix from another project. Escalate a diagnostic request to RCP. RCP may investigate across relevant projects and central authorities read-only, establish ownership, coalesce related failures and recommend routing, but must not mutate child-project source during triage.
23. A project receiving a valid external request must independently review the evidence and classify it as ACCEPTED, REJECTED_NOT_OWNED, NEEDS_MORE_EVIDENCE, DUPLICATE or SUPERSEDED. An accepted request is tracked through the receiver's own governed work item, source QA, PR, required CI and safe merge.
24. A proven central capability gap blocks only the minimum affected scope. Create or reuse the central dependency, mark the exact dependent work item/capability/release/Production scope blocked, release that active lane if appropriate, and keep unrelated workstreams schedulable. Do not normalize a scoped dependency into a project-wide block unless whole-project impact is separately proven.
25. Do not build a project-local shadow control plane, duplicated central protocol or competing multi-project release/artifact/approval/scheduler authority. Safe project-local build, test and deploy hooks remain allowed inside project and environment authority.
26. After an accepted external request is resolved, publish a resolution callback containing the request id, receiver project, resolution work item/PR, exact resolution source SHA, capability or fix identity and revalidation requirement. The requester must revalidate only the affected scope before marking the dependency resolved; independent scopes never wait for this callback.
27. For every repository classified roadmap_enabled=true, recover project intent in this order: AGENTS.md, PROJECT_BIG_PICTURE.md, ROADMAP.md, CURRENT_STATE.md, relevant evidence, live Work Item, then actual GitHub/CI/runtime state. Reconcile stale prose before mutation; actual state wins and chat memory is not authority.
28. PROJECT_BIG_PICTURE.md is stable product-direction authority and must not become a moving PR/SHA/CI/blocker cursor. ROADMAP.md is ordered durable planning authority and must not replace CURRENT_STATE.md or the live Work Item.
29. Do not fabricate PROJECT_BIG_PICTURE.md or ROADMAP.md for a repository classified DEFERRED because source/product authority is not established. Keep the repo explicitly deferred until evidence supports roadmap enablement.
30. When the repository has a deterministic canonical roadmap/current-state chain, continue ordinary roadmap work autonomously through source QA, PR, required CI, safe merge and the next independent phase/workstream without waiting for a new user prompt, but only inside the active project mutation scope.
31. Human approval remains required only where canonical policy requires a real privileged or risk decision, including Production deployment/promotion, Production database mutation, destructive operations, unavailable real-host secret/root access, material security/architecture decisions, or unresolved product decisions.
32. Platform Contract incompatibility blocks only scopes that consume the incompatible contract. A project may pin a compatible immutable contract version/SHA and continue independent engineering work.
33. Never claim SOURCE_PASS, ARTIFACT_READY, LIVE_PASS, DONE or equivalent without the evidence level required by project and central authority. Historical STAGING_PASS evidence remains historical and is not an active release prerequisite.
<!-- TNSUITE:RCP-MANAGED-AGENTS:END -->
