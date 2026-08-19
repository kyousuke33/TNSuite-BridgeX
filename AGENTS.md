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
