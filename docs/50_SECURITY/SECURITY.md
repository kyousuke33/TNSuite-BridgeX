# Security
Primary boundaries: untrusted remote servers/files, credentials/private keys, update supply chain, installer privilege, public GitHub source and future distribution APIs. No production secret may be committed or embedded in the client.

## Public repository CI boundary
BridgeX is public and consumes the central RCP contract `tnsuite.ci-public-repository-trust.v1`. Public pull requests, fork pull requests and external contributor code must execute on GitHub-hosted runners only. Shared `tn-ci-01` and other trusted TNSuite self-hosted runners are prohibited for BridgeX while the repository remains public.

`pull_request_target` must not checkout or execute untrusted PR-head source, dependency installation, build scripts or executable artifacts. Repository workflows must not expose production/staging/database/signing/release credentials, VPS SSH keys or TNSuite internal tokens.

A future self-hosted exception requires either private-repository re-onboarding or a separately governed dedicated disposable/ephemeral runner isolated from shared trusted infrastructure.
