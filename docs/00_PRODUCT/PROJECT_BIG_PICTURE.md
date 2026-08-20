# TNSuite BridgeX — Project Big Picture

This file is the stable product-direction authority for BridgeX. Moving build/PR/CI/update-rollout state belongs in `CURRENT_STATE.md`, evidence and live Work Items.

## Product goal

Build a secure, dependable **Windows x64 file-transfer desktop application** with TNSuite branding, bilingual UI, Light/Dark appearance, installer/update lifecycle and bounded CLI/SFTP capability while preserving the trust boundaries required by a public repository.

## User outcome

Users should be able to install BridgeX, connect to permitted file-transfer endpoints, transfer/manage files reliably, use the supported desktop/CLI surfaces and receive governed updates without weakening upstream security or repository trust.

## Security invariant

BridgeX must preserve secure transport/authentication behavior and fail closed on unsafe update/artifact trust. Public/untrusted pull requests must never gain privileged self-hosted runner or TNSuite private runtime authority.

## Public-repository invariant

```text
PUBLIC_REPOSITORY=true
UNTRUSTED_PR_RUNNER=GITHUB_HOSTED_ONLY
SHARED_PRIVATE_SELF_HOSTED_EXECUTION=PROHIBITED
```

Public CI trust rules are part of product delivery safety and must not be weakened to accelerate builds.

## Desktop/update invariant

Installer/update artifacts must be bound to exact canonical source and governed release identity. Update UX may consume signed/verified publication state; it must not download/execute an unverifiable replacement merely because a newer version string exists.

## Product boundary

BridgeX owns its Windows desktop/file-transfer behavior and updater UX. RCP/Portal may provide governed release/publication authority, but BridgeX does not become a central release server or receive private-project runtime privilege.

## Definition of DONE

BridgeX is mature when the desktop application is stable and secure, bilingual/theme/installer behavior is coherent, file-transfer/CLI paths are accepted, update delivery is artifact-verified and staged/rollback-capable, and public-repository CI/release boundaries remain proven.

## Roadmap relationship

`ROADMAP.md` orders the desktop/update foundation and later rollout hardening toward this Big Picture. `docs/90_GOVERNANCE/CURRENT_STATE.md` records the moving baseline/CI/release checkpoint. Actual signed artifact/runtime evidence wins over stale prose.
