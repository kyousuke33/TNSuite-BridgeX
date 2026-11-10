[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
# Disposable CI checkout only; historical Build12 source manifest remains byte-exact.
$ErrorActionPreference = 'Stop'
$buildPath = '.\scripts\build-filezilla-dark.sh'
$build = Get-Content -LiteralPath $buildPath -Raw -Encoding UTF8

# The old BuildKit checked three large design/reference exports that were
# deliberately removed from canonical source. Match the governed release
# adapter: validate the current shipped branding contract instead.
$brandingOld = @'
log "Branding/UI asset QA - fail closed"
python "$QA/branding_asset_check.py" "$KIT" | tee "$WORK/branding-asset-report.txt"
grep -q '^BRANDING_ASSET_QA=PASS$' "$WORK/branding-asset-report.txt"
'@
$brandingNew = @'
log "Canonical branding contract QA - fail closed"
python "$KIT/scripts/qa/branding_contract_check.py" "$KIT" | tee "$WORK/branding-contract-report.txt"
grep -q '^BRANDING_CONTRACT_QA=PASS$' "$WORK/branding-contract-report.txt"
'@
$brandingOld = $brandingOld -replace "`r`n", "`n"
$brandingNew = $brandingNew -replace "`r`n", "`n"
if (-not $build.Contains($brandingOld.Trim())) { throw 'HF24_BRANDING_CONTRACT_ADAPTER_ANCHOR_MISSING' }
$build = $build.Replace($brandingOld.Trim(), $brandingNew.Trim())

$patchNeedle = 'python "$KIT/scripts/patch_tnsuite_bridgex.py" "$SRC"'
$patchReplacement = $patchNeedle + "`n" + 'python "$KIT/scripts/patch_tnsuite_bridgex_hotfix24.py" "$SRC"'
if (-not $build.Contains($patchNeedle)) { throw 'HF24_RUNTIME_PATCH_HOOK_ANCHOR_MISSING' }
$build = $build.Replace($patchNeedle, $patchReplacement)

$exeNeedle = '[[ -s "$APP/bin/BridgeX.exe" ]] || { echo "ERROR: BridgeX.exe branding rename failed." >&2; exit 36; }'
$exeReplacement = $exeNeedle + "`n" + @'
BRIDGEX_APP_ICON_SOURCE="$KIT/assets/branding/BridgeX-AppIcon.ico"
BRIDGEX_APP_ICON_RUNTIME="$APP/bin/BridgeX-AppIcon.ico"
cp -f "$BRIDGEX_APP_ICON_SOURCE" "$BRIDGEX_APP_ICON_RUNTIME"
[[ -s "$BRIDGEX_APP_ICON_RUNTIME" ]] || { echo "ERROR: BridgeX runtime icon missing." >&2; exit 47; }
[[ "$(sha256sum "$BRIDGEX_APP_ICON_SOURCE" | awk '{print $1}')" == "$(sha256sum "$BRIDGEX_APP_ICON_RUNTIME" | awk '{print $1}')" ]] || { echo "ERROR: BridgeX runtime icon hash mismatch." >&2; exit 48; }
echo "BRIDGEX_APP_ICON_RUNTIME_QA=PASS"
'@
if (-not $build.Contains($exeNeedle)) { throw 'HF24_RUNTIME_ICON_PACKAGE_ANCHOR_MISSING' }
$build = $build.Replace($exeNeedle, $exeReplacement)
[IO.File]::WriteAllText((Resolve-Path $buildPath), $build, [Text.UTF8Encoding]::new($false))
# Hotfix24's disposable runner checkout receives the same guarded ABI
# fix as the release adapter; canonical source remains byte-exact.
& python.exe .\qa\patch_wx_build_runtime.py $buildPath
if ($LASTEXITCODE -ne 0) { throw "HF24_WX_ABI_PATCH_FAILED=$LASTEXITCODE" }

$icon = '.\assets\branding\BridgeX-AppIcon.ico'
$sidebar = '.\installer\BridgeX-Setup-Sidebar.bmp'
if ((Get-FileHash -Algorithm SHA256 $icon).Hash.ToLowerInvariant() -ne $env:ICON_SHA256) { throw 'HF24_CANONICAL_ICON_HASH_FAIL' }
if ((Get-FileHash -Algorithm SHA256 $sidebar).Hash.ToLowerInvariant() -ne $env:SIDEBAR_SHA256) { throw 'HF24_CLASSIC_SIDEBAR_HASH_FAIL' }
Write-Host 'HF24_BUILD_HOOKS=PASS'
Write-Host 'HF24_CANONICAL_BRANDING_ASSETS=PASS'
