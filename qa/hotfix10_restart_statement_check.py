#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) != 2: raise SystemExit("Usage: hotfix10_restart_statement_check.py <kit-root>")
root=Path(sys.argv[1]).resolve()
patch=(root/"scripts/patch_tnsuite_bridgex.py").read_text(encoding="utf-8")
fixture=(root/"qa/patch_fixture_check.py").read_text(encoding="utf-8")
build=(root/"scripts/build-filezilla-dark.sh").read_text(encoding="utf-8")
checks=[]
def check(label, ok):
    ok=bool(ok); checks.append(ok); print(("PASS  " if ok else "FAIL  ")+label)
check("Hotfix10 structural restart marker", "TNSUITE_BRIDGEX_BUILD12_HF10_RESTART_STRUCTURAL_STATEMENT" in patch)
check("No exact wxMessageBox ownership matcher", 'rfind("wxMessageBox("' not in patch)
check("Structural helper accepts qualified callees", "_restart_call_statement_bounds" in patch and "restart_callee" in patch and "re.fullmatch" in patch)
check("Structural helper tolerates qualification whitespace", "callee_raw" in patch and "re.sub" in patch and "prefix_start" in patch)
check("Replacement preserves statement grammar", '"(void)0; /* BridgeX Hotfix10:' in patch)
check("Matcher fails closed", "containing call statement could not be structurally bounded" in patch)
check("Fixture uses whitespace-qualified upstream helper", "wxMsg :: Message(" in fixture)
check("Fixture uses unbraced if", "if (language_changed)" in fixture)
check("Fixture requires phrase removal", "upstream language-only restart popup remains" in fixture)
check("Fixture requires control-flow preservation", "unbraced-if statement shape was not preserved" in fixture)
check("Hotfix10 QA report retained in external evidence", "hotfix10-restart-statement-report.txt" in build and 'QA_EVIDENCE="$DIST/${BUILD_NAME}-QA-Evidence"' in build)
if not all(checks): print("HOTFIX10_RESTART_STATEMENT_QA=FAIL"); raise SystemExit(1)
print("HOTFIX10_RESTART_STATEMENT_QA=PASS")
