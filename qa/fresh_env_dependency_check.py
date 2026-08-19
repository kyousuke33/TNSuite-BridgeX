from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
download_pos=s.find('log "Download FileZilla ${FZ_VERSION} source"')
dependency_pos=s.find('log "Hotfix9 Python QA dependency audit - fail closed"')
hotfix10_pos=s.find('log "Hotfix10 restart statement structural QA - fail closed"')
hotfix11_pos=s.find('log "Hotfix11 bitmap SetBitmap guard QA - fail closed"')
hotfix12_pos=s.find('log "Hotfix12 settings/payload regression QA - fail closed"')
hotfix13_pos=s.find('log "Hotfix13 upstream association anchor QA - fail closed"')
hotfix15_reg_pos=s.find('log "Hotfix15 native association regression QA - fail closed"')
hotfix15_extracted_pos=s.find('log "Hotfix15 SHA-verified native association QA - fail closed"')
hotfix16_pos=s.find('log "Hotfix16 first-restart settings persistence QA - fail closed"')
patch_pos=s.find('log "Apply TNSuite BridgeX UI patch"')
locale_source_pos=s.find('log "BridgeX Vietnamese locale source QA - fail closed"')
locale_msgfmt_pos=s.find('log "BridgeX Vietnamese locale early msgfmt probe - fail closed"')
checks={
'ucrt gettext tools package':'mingw-w64-ucrt-x86_64-gettext-tools' in s,
'exact ucrt msgfmt gate':'MSGFMT_EXE="/ucrt64/bin/msgfmt.exe"' in s,
'build-wide early log':'BUILD_LOG="$DIST/${BUILD_NAME}-build.log"' in s and 'exec > >(tee -a "$BUILD_LOG") 2>&1' in s,
'no generic gettext fallback':'missing+=(gettext)' not in s,
'Hotfix9 Python dependency audit is earliest QA dependency guard':0 <= dependency_pos < locale_source_pos < download_pos and 'HOTFIX9_QA_DEPENDENCY_QA=PASS' in s,
'Hotfix10 structural restart QA is pre-download':0 <= hotfix10_pos < download_pos and 'HOTFIX10_RESTART_STATEMENT_QA=PASS' in s,
'Hotfix11 bitmap SetBitmap QA is pre-download':0 <= hotfix11_pos < download_pos and 'HOTFIX11_BITMAP_SETBITMAP_QA=PASS' in s,
'Hotfix12 settings/payload QA is pre-download':0 <= hotfix12_pos < download_pos and 'HOTFIX12_SETTINGS_PAYLOAD_QA=PASS' in s,
'Hotfix13 association intent QA is pre-download':0 <= hotfix13_pos < download_pos and 'HOTFIX13_ASSOC_UPSTREAM_QA=PASS' in s,
'Hotfix15 native regression QA is pre-download':0 <= hotfix15_reg_pos < download_pos and 'HOTFIX15_NATIVE_ASSOC_REGRESSION_QA=PASS' in s,
'Hotfix16 restart persistence QA is pre-download':0 <= hotfix16_pos < download_pos and 'HOTFIX16_RESTART_PERSISTENCE_QA=PASS' in s,
'Hotfix15 native extracted QA is post-download/pre-patch':download_pos < hotfix15_extracted_pos < patch_pos and 'HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS' in s,
'dependency package DB is queried once with progress markers':s.count('pacman -Q') == 1 and 'DEPENDENCY_PACKAGE_DB_QA=START' in s and 'DEPENDENCY_PACKAGE_DB_QA=PASS' in s and 'BRIDGEX_PACMAN_DB_TIMEOUT_SECONDS' in s,
'BridgeX locale raw-header QA is early':0 <= locale_source_pos < download_pos,
'BridgeX real msgfmt QA is early':0 <= locale_msgfmt_pos < download_pos and 'BRIDGEX_VI_LOCALE_EARLY_MSGFMT_QA=PASS' in s,
'BridgeX locale early msgfmt is fail closed':'failed early UCRT64 msgfmt validation' in s and 'exit 70' in s,
'Hotfix16 Windows restart handoff API probe is present':'WX33_HF16_RESTART_HANDOFF_API_COMPILE_QA=PASS' in s and 'WaitForSingleObject' in s and 'wxSetEnv' in s,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): raise SystemExit(1)
print('FRESH_ENV_DEPENDENCY_QA=PASS')
