#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f scripts/build-filezilla-dark.sh || ! -d qa || ! -f scripts/patch_tnsuite_bridgex.py ]]; then
  echo 'SOURCE_BASELINE_IMPORT_PENDING: Build12-Hotfix16 canonical source has not been fully materialized.' >&2
  exit 42
fi
echo 'SOURCE_BASELINE_PRESENT=PASS'
# Full Hotfix16 source regression suite is restored with the exact baseline import.
