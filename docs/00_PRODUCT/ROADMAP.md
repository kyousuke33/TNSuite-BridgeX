# TNSuite BridgeX — Roadmap

Stable product direction is defined by [`PROJECT_BIG_PICTURE.md`](PROJECT_BIG_PICTURE.md). This roadmap orders durable desktop/update maturity. Current release/build, exact artifact/CI and rollout status belong in `docs/90_GOVERNANCE/CURRENT_STATE.md`, evidence and live Work Items.

## P0 — Secure desktop baseline

Goal: preserve the accepted Windows x64 file-transfer product baseline while keeping public-repository trust and desktop security boundaries intact.

Required outcomes:
- secure connection/file-transfer/CLI paths remain functional;
- bilingual Light/Dark/installer lifecycle remains coherent;
- public/untrusted PR execution stays GitHub-hosted only;
- no private/self-hosted TNSuite runtime privilege leaks into public PRs;
- source/build evidence is exact and reproducible.

## P1 — Governed desktop update foundation

Goal: make updates an exact artifact-governed flow rather than an unverified version download.

Target flow:
```text
canonical GitHub source/CI
→ immutable Windows artifact
→ central release verification
→ Portal/admin publication
→ signed/verified update manifest + artifact distribution
→ BridgeX update UX
```

Required outcomes:
- update identity binds exact source/artifact;
- client verifies publication/artifact trust before install;
- no arbitrary caller-supplied update executable/path;
- failure leaves the existing install recoverable.

## P2 — Rollout and recovery controls

Goal: operate desktop updates safely.

Required outcomes:
- staged rollout cohorts where needed;
- pause/supersede/revoke semantics;
- retry/failure/recovery state;
- rollback or safe previous-version recovery policy;
- release/update evidence and audit.

## P3 — Product/operational maturity

Goal: improve the desktop product from real usage.

Potential work:
- transfer reliability/performance metrics;
- accessibility and UX refinement;
- installer/update analytics with privacy-safe semantics;
- signing/trust hardening;
- additional bounded CLI/SFTP capability only when product need is proven.

## Completion rule

A build/version string does not prove update eligibility. Exact source/artifact trust and the required runtime/user evidence govern release/update claims.
