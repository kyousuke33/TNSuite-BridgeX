#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MANIFEST='.release/build12-hotfix16-source-manifest.sha256'

if [[ ! -f "$MANIFEST" ]]; then
  echo 'SOURCE_BASELINE_MANIFEST=FAIL reason=MANIFEST_MISSING' >&2
  exit 42
fi

if ! sha256sum --check --strict "$MANIFEST"; then
  echo 'SOURCE_BASELINE_MANIFEST=FAIL reason=CONTENT_MISMATCH' >&2
  python3 - "$MANIFEST" <<'PY'
from pathlib import Path
import hashlib
import sys

manifest = Path(sys.argv[1])
for raw in manifest.read_text(encoding='utf-8').splitlines():
    raw = raw.strip()
    if not raw:
        continue
    expected, path_text = raw.split(None, 1)
    path_text = path_text.lstrip('* ')
    path = Path(path_text)
    if not path.is_file():
        print(f'SOURCE_MANIFEST_DIFF path={path_text} expected={expected} actual=MISSING')
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected.lower():
        print(f'SOURCE_MANIFEST_DIFF path={path_text} expected={expected.lower()} actual={actual}')
PY
  echo 'SOURCE_BASELINE_IMPORT_PENDING: Build12-Hotfix16 canonical source is incomplete or does not match the pinned manifest.' >&2
  exit 42
fi

echo 'SOURCE_BASELINE_MANIFEST=PASS'

python3 qa/hotfix9_qa_dependency_check.py .
python3 qa/bridgex_locale_source_check.py locales/bridgex_vi_VN.po
python3 qa/build_scheduler_check.py scripts/build-filezilla-dark.sh
# qa/branding_asset_check.py is preserved byte-exact in the Hotfix16 source
# manifest, but its pre-governance expectation includes three audited-out
# design/reference exports. Run the governance branding contract instead.
python3 scripts/qa/branding_contract_check.py .
python3 qa/product_content_check.py .
python3 qa/hotfix4_runtime_regression_check.py .
python3 qa/hotfix5_patch_anchor_check.py .
python3 qa/hotfix6_staticbox_compile_check.py .
python3 qa/hotfix7_staticbox_header_check.py .
python3 qa/hotfix8_runtime_product_check.py .
python3 qa/hotfix10_restart_statement_check.py .
python3 qa/hotfix11_bitmap_setbitmap_check.py .
python3 qa/hotfix12_settings_payload_check.py .
python3 qa/hotfix13_assoc_upstream_check.py .
python3 qa/hotfix14_pipeline_regression_check.py .
python3 qa/hotfix15_native_assoc_regression_check.py .
python3 qa/hotfix16_restart_persistence_check.py .
python3 qa/installer_source_check.py installer/TNSuiteBridgeXInstaller.nsi
python3 qa/cli_source_check.py cli/bridgex-cli.cpp
python3 qa/patch_fixture_check.py
python3 qa/locale_helper_check.py
python3 qa/fresh_env_dependency_check.py scripts/build-filezilla-dark.sh
python3 qa/contrast_check.py

artifact_workflow='.github/workflows/native-installer-candidate.yml'
if grep -Fq 'CANONICAL_ARTIFACT_ID:' "$artifact_workflow"; then
  echo 'PR_CANONICAL_ARTIFACT_RESOLUTION_QA=FAIL reason=HARD_CODED_ACTIONS_ARTIFACT_ID' >&2
  exit 43
fi
[[ "$(grep -Fc 'CANONICAL_SOURCE_SHA: ${{ github.event.pull_request.base.sha }}' "$artifact_workflow")" -eq 3 ]] || {
  echo 'PR_CANONICAL_ARTIFACT_RESOLUTION_QA=FAIL reason=PR_BASE_SHA_BINDING_COUNT' >&2
  exit 43
}
[[ "$(grep -Fc 'CANONICAL_ARTIFACT_NAME: bridgex-release-${{ github.event.pull_request.base.sha }}' "$artifact_workflow")" -eq 3 ]] || {
  echo 'PR_CANONICAL_ARTIFACT_RESOLUTION_QA=FAIL reason=GOVERNED_ARTIFACT_NAME_BINDING_COUNT' >&2
  exit 43
}
[[ "$(grep -Fc 'CANONICAL_ARTIFACT_RESOLUTION_FAIL' "$artifact_workflow")" -eq 3 ]] || {
  echo 'PR_CANONICAL_ARTIFACT_RESOLUTION_QA=FAIL reason=FAIL_CLOSED_RESOLUTION_COUNT' >&2
  exit 43
}
echo 'PR_CANONICAL_ARTIFACT_RESOLUTION_QA=PASS'

[[ "$(grep -Fc 'CANONICAL_RUNTIME_HASH_AUTHORITY=EXACT_BASE_ARTIFACT' "$artifact_workflow")" -eq 3 ]] || {
  echo 'PR_CANONICAL_RUNTIME_HASH_QA=FAIL reason=ARTIFACT_DERIVATION_COUNT' >&2
  exit 44
}
[[ "$(grep -Fc '"EXPECTED_BRIDGEX_SHA256=$runtimeSha"' "$artifact_workflow")" -eq 3 ]] || {
  echo 'PR_CANONICAL_RUNTIME_HASH_QA=FAIL reason=GITHUB_ENV_BINDING_COUNT' >&2
  exit 44
}
[[ "$(grep -Fc -- '-ExpectedBridgeXSha256 $env:EXPECTED_BRIDGEX_SHA256' "$artifact_workflow")" -eq 5 ]] || {
  echo 'PR_CANONICAL_RUNTIME_HASH_QA=FAIL reason=LEGACY_BUILDER_PROPAGATION_COUNT' >&2
  exit 44
}
if grep -Fq 'EXPECTED_BRIDGEX_SHA256: '''9d528d211950f3df0609c05a8c1e01725927ae76b70bed2ad0fe9b97c53504d6'''' "$artifact_workflow"; then
  echo 'PR_CANONICAL_RUNTIME_HASH_QA=FAIL reason=HISTORICAL_RUNTIME_HASH_PIN_IN_WORKFLOW' >&2
  exit 44
fi
for builder in   .release/build-wix-installer-hotfix20.ps1   .release/build-wix-installer-hotfix21.ps1   .release/build-wix-installer-hotfix22.ps1   .release/build-wix-installer-hotfix23.ps1; do
  grep -Fq 'ExpectedBridgeXSha256' "$builder" || {
    echo "PR_CANONICAL_RUNTIME_HASH_QA=FAIL reason=BUILDER_PARAMETER_MISSING file=$builder" >&2
    exit 44
  }
done
grep -Fq -- '-ExpectedBridgeXSha256 $ExpectedBridgeXSha256' .release/build-wix-installer-hotfix24.ps1 || {
  echo 'PR_CANONICAL_RUNTIME_HASH_QA=FAIL reason=HOTFIX24_PROPAGATION_MISSING' >&2
  exit 44
}
echo 'PR_CANONICAL_RUNTIME_HASH_QA=PASS'

[[ "$(grep -Fc 'ExpectedBridgeXSha256' .release/build-wix-installer-hotfix20.ps1)" -ge 3 ]] || {
  echo 'PR_LEGACY_HOTFIX20_RUNTIME_HASH_QA=FAIL reason=EXACT_HASH_PARAMETER_NOT_PROPAGATED' >&2
  exit 43
}
if grep -Fq 'HOTFIX24_RUNTIME_HASH_OVERRIDE_ANCHOR_MISSING' .release/build-wix-installer-hotfix24.ps1; then
  echo 'PR_HOTFIX24_RUNTIME_HASH_QA=FAIL reason=OBSOLETE_PRE_REWRITE_PRESENT' >&2
  exit 43
fi
echo 'PR_LEGACY_HOTFIX20_RUNTIME_HASH_QA=PASS'
echo 'PR_HOTFIX24_RUNTIME_HASH_QA=PASS'

echo 'SOURCE_REGRESSION_QA=PASS'
