# Dependencies
Build dependency checks must be deterministic and bounded. Avoid broad environment upgrades when only missing dependencies are required.

BridgeX is public, so PR/fork dependency resolution and source/build checks use GitHub-hosted runners under central RCP contract `tnsuite.ci-public-repository-trust.v1`. Shared self-hosted host layout/cleanup/resource rules remain centrally owned by `tnsuite.ci-runner-host-layout.v1` but do not grant BridgeX access to `tn-ci-01` while the repository is public.
