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
  echo 'SOURCE_BASELINE_IMPORT_PENDING: Build12-Hotfix16 canonical source is incomplete or does not match the pinned manifest.' >&2
  exit 42
fi

echo 'SOURCE_BASELINE_MANIFEST=PASS'

python3 qa/hotfix9_qa_dependency_check.py .
python3 qa/bridgex_locale_source_check.py locales/bridgex_vi_VN.po
python3 qa/build_scheduler_check.py scripts/build-filezilla-dark.sh
python3 qa/branding_asset_check.py .
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

echo 'SOURCE_REGRESSION_QA=PASS'
