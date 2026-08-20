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
TNSUITE_AGENTS_SYNC=RCP_MANAGED
TNSUITE_AGENTS_POLICY_REVISION=2026-08-20.1

Central managed execution rules:
1. Before managed implementation, load project-local authority and run the centrally versioned TNSuite Authority Preflight for declared subscriptions.
2. An agent may mutate only its own repository/project scope. It may inspect other governed repositories read-only when necessary for diagnosis, but must not edit another project to unblock itself.
3. Create or reuse a governed cross-project defect request only when evidence proves the defect is owned by the target project. The request must identify the requester, blocked work item, observed and expected behavior, exact evidence/source references, ownership rationale, blocking status and required outcome.
4. When ownership is UNKNOWN or only suspected, do not assign blame or request a fix from another project. Escalate a diagnostic request to RCP. RCP may investigate across relevant projects and central authorities read-only, establish ownership, coalesce related failures and recommend routing, but must not mutate child-project source during triage.
5. A project receiving a valid external request must independently review the evidence and classify it as ACCEPTED, REJECTED_NOT_OWNED, NEEDS_MORE_EVIDENCE, DUPLICATE or SUPERSEDED. An accepted request that blocks another managed project must be tracked through the receiver's own governed work item, source QA, PR, required CI and safe merge.
6. After an accepted external request is resolved, publish a resolution callback containing the request id, receiver project, resolution work item/PR, exact resolution source SHA, capability or fix identity and revalidation requirement. The requester must revalidate the original blocked condition before marking the dependency resolved and automatically resume only after that revalidation passes.
7. When a proven central capability is missing, record or reuse the central dependency and park the child work item without consuming an active lane. Do not build a project-local shadow control plane, duplicated central protocol or workaround that bypasses central authority.
8. When the repository has a deterministic canonical roadmap/current-state chain, continue ordinary roadmap work autonomously through source QA, PR, required CI, safe merge and the next phase without waiting for a new user prompt.
9. Human approval remains required where canonical policy explicitly requires it, including Production promotion, Production database mutation, destructive operations, unavailable real-host secret/root access, material security/architecture decisions, or unresolved product decisions.
10. Never claim SOURCE_PASS, ARTIFACT_READY, STAGING_PASS, LIVE_PASS, DONE or equivalent without the evidence level required by project and central authority.
<!-- TNSUITE:RCP-MANAGED-AGENTS:END -->
