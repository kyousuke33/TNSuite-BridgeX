# Bootstrap Audit

## Remove / do not import from Build12-Hotfix16 BuildKit
- `AUDIT_HOTFIX14.md`, `AUDIT_HOTFIX15.md`, `AUDIT_HOTFIX16.md`: one-off historical audit evidence; conclusions move into canonical governance/ADR/current state.
- `qa/STATIC_QA_EXECUTION.log`, `qa/STATIC_QA_REPORT.md`, `qa/STATIC_QA_RESULTS.txt`: generated evidence, not source authority.
- `KIT_SHA256SUMS.txt`: BuildKit package checksum manifest, not canonical source.
- old `docs/RELEASE_AUTHORITY_SETUP.md`, `docs/UI_ACCEPTANCE.md`, `docs/UPDATE_FEED_SPEC.md`: superseded by canonical docs.
- `assets/branding/BridgeX-AppIcon.png`, `BridgeX-Logo.png`, `BridgeX-UI-Reference.png`: large design/reference exports not consumed by build/patch/installer; active binary icon sizes and installer art must remain.

## Retain
Active `qa/hotfix4...hotfix16` regression scripts are referenced by the proven build pipeline and cross-check one another. They are not unused; semantic renaming is deferred.

`docs/BridgeX-Help.html` and `docs/BridgeX-Report-Bug.html` are active product-help inputs and must remain at proven build paths after source materialization.
