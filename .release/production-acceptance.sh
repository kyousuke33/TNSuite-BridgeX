#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "BRIDGEX_PRODUCTION_ACCEPTANCE=BLOCKED reason=$1" >&2
  exit 42
}

[[ "${GITHUB_EVENT_NAME:-}" == "push" ]] || fail "EVENT_NOT_PUSH"
[[ "${GITHUB_REF_NAME:-}" == "main" ]] || fail "SOURCE_BRANCH_NOT_MAIN"
[[ "${BRIDGEX_TRIGGER_EVENT:-}" == "push" ]] || fail "SOURCE_EVENT_NOT_PUSH"
[[ "${BRIDGEX_TRIGGER_BRANCH:-}" == "main" ]] || fail "SOURCE_BRANCH_CONTEXT_MISMATCH"
[[ "${BRIDGEX_SOURCE_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || fail "SOURCE_SHA_INVALID"
[[ "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || fail "GITHUB_SHA_INVALID"
[[ "${BRIDGEX_SOURCE_SHA:-}" == "${GITHUB_SHA:-}" ]] || fail "SOURCE_SHA_MISMATCH"
[[ "${RCP_RELEASE_PROFILE:-}" == "tnsuite.public-desktop-github-release.v1" ]] || fail "RCP_RELEASE_PROFILE_MISMATCH"
[[ "${RCP_AUTHORITY_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || fail "RCP_AUTHORITY_SHA_INVALID"
[[ "${BRIDGEX_RELEASE_TAG:-}" == "v0.5-Build12-Hotfix17" ]] || fail "RELEASE_TAG_MISMATCH"

for file in "${BRIDGEX_SETUP:-}" "${BRIDGEX_PORTABLE:-}" "${BRIDGEX_SHA256_FILE:-}"; do
  [[ -n "$file" && -s "$file" ]] || fail "RELEASE_ASSET_MISSING"
done

(
  cd "$(dirname "$BRIDGEX_SHA256_FILE")"
  sha256sum --check --strict "$(basename "$BRIDGEX_SHA256_FILE")"
) || fail "RELEASE_ASSET_SHA256_MISMATCH"

echo "PUBLIC_DESKTOP_RELEASE_PROFILE=PASS"
echo "CANONICAL_MAIN_SOURCE=PASS"
echo "RELEASE_ASSET_SHA256=PASS"
echo "GUI_RUNTIME=NOT_VERIFIED_BY_RELEASE_WORKFLOW"
echo "PRODUCTION_HOST_ACCESS=NONE"
echo "DATABASE_EXECUTION=NOT_PERFORMED"
echo "BRIDGEX_PRODUCTION_ACCEPTANCE=PASS"
