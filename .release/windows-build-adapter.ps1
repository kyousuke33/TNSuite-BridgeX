[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$LegacyBuildName = 'TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full'
$ReleaseBuildName = 'TNSuiteBridgeX_260820_v0.5-Build12-Hotfix17-Full'
$ReleaseProductVersion = '0.5-Build12-Hotfix17'
$ReleaseFileVersion = '0.5.12.17'
$WorkRoot = Join-Path $env:RUNNER_TEMP "bridgex-release-kit-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
$WorkDist = Join-Path $WorkRoot 'dist'
$RepoDist = Join-Path $RepoRoot 'dist'

function Set-ExactReplacement {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Old,
        [Parameter(Mandatory = $true)][string]$New,
        [Parameter(Mandatory = $true)][int]$ExpectedCount,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    $text = [System.IO.File]::ReadAllText($Path)
    $text = $text -replace "`r`n", "`n"
    $count = [regex]::Matches($text, [regex]::Escape($Old)).Count
    if ($count -ne $ExpectedCount) {
        throw "$Marker`_ANCHOR_COUNT=$count expected=$ExpectedCount path=$Path"
    }
    $text = $text.Replace($Old, $New)
    [System.IO.File]::WriteAllText($Path, $text, [System.Text.UTF8Encoding]::new($false))
    Write-Host "$Marker=PASS count=$count"
}

if (Test-Path -LiteralPath $WorkRoot) {
    Remove-Item -LiteralPath $WorkRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null

Write-Host 'RELEASE_BUILD_ADAPTER=START'
Write-Host "CANONICAL_REPO_ROOT=$RepoRoot"
Write-Host "ADAPTED_WORK_ROOT=$WorkRoot"
Write-Host "REMEDIATION_RELEASE_BUILD_NAME=$ReleaseBuildName"
Write-Host "REMEDIATION_RELEASE_PRODUCT_VERSION=$ReleaseProductVersion"

$robocopyArgs = @(
    $RepoRoot,
    $WorkRoot,
    '/MIR',
    '/XD', '.git', 'dist', 'release-assets',
    '/R:2', '/W:1',
    '/NFL', '/NDL', '/NJH', '/NJS', '/NP'
)
& robocopy.exe @robocopyArgs | Out-Null
$copyExit = $LASTEXITCODE
if ($copyExit -gt 7) {
    throw "RELEASE_BUILD_ADAPTER_COPY_FAILED=$copyExit"
}

$BuildPipeline = Join-Path $WorkRoot 'scripts\build-filezilla-dark.sh'
$BuildWrapper = Join-Path $WorkRoot 'Build-TNSuiteBridgeX.ps1'
$InstallerSource = Join-Path $WorkRoot 'installer\TNSuiteBridgeXInstaller.nsi'
$ProductContentQa = Join-Path $WorkRoot 'qa\product_content_check.py'
$Hotfix8Qa = Join-Path $WorkRoot 'qa\hotfix8_runtime_product_check.py'
foreach ($path in @($BuildPipeline, $BuildWrapper, $InstallerSource, $ProductContentQa, $Hotfix8Qa)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "RELEASE_BUILD_ADAPTER_REQUIRED_FILE_MISSING=$path"
    }
}

# Replace the obsolete pre-governance branding export check with the canonical
# shipped-branding contract. This remains a disposable build-copy adaptation;
# the protected checkout is never mutated.
$brandingOld = @'
log "Branding/UI asset QA - fail closed"
python "$QA/branding_asset_check.py" "$KIT" | tee "$WORK/branding-asset-report.txt"
grep -q '^BRANDING_ASSET_QA=PASS$' "$WORK/branding-asset-report.txt"
'@
$brandingOld = $brandingOld -replace "`r`n", "`n"
$brandingNew = @'
log "Canonical branding contract QA - fail closed"
python "$KIT/scripts/qa/branding_contract_check.py" "$KIT" | tee "$WORK/branding-contract-report.txt"
grep -q '^BRANDING_CONTRACT_QA=PASS$' "$WORK/branding-contract-report.txt"
'@
$brandingNew = $brandingNew -replace "`r`n", "`n"
Set-ExactReplacement -Path $BuildPipeline -Old $brandingOld -New $brandingNew -ExpectedCount 1 -Marker 'RELEASE_BUILD_ADAPTER_BRANDING_CONTRACT'

# Hotfix16 was withdrawn after the installer artifact received heuristic
# detections. The remediated bytes must never reuse that public identity.
# Stamp the disposable release build as Build12-Hotfix17 while preserving the
# canonical Build12-Hotfix16 source lineage and regression filenames.
Set-ExactReplacement -Path $BuildPipeline `
    -Old 'BUILD_NAME="TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full"' `
    -New 'BUILD_NAME="TNSuiteBridgeX_260820_v0.5-Build12-Hotfix17-Full"' `
    -ExpectedCount 1 -Marker 'REMEDIATION_BUILD_NAME_PIPELINE'
Set-ExactReplacement -Path $BuildPipeline `
    -Old '-DPRODUCT_VERSION="0.5-Build12-Hotfix16"' `
    -New '-DPRODUCT_VERSION="0.5-Build12-Hotfix17"' `
    -ExpectedCount 2 -Marker 'REMEDIATION_PRODUCT_VERSION_PIPELINE'
Set-ExactReplacement -Path $BuildWrapper `
    -Old '$BuildName = ''TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full''' `
    -New '$BuildName = ''TNSuiteBridgeX_260820_v0.5-Build12-Hotfix17-Full''' `
    -ExpectedCount 1 -Marker 'REMEDIATION_BUILD_NAME_WRAPPER'

Set-ExactReplacement -Path $InstallerSource `
    -Old '!define PRODUCT_VERSION "0.5-Build12-Hotfix16"' `
    -New '!define PRODUCT_VERSION "0.5-Build12-Hotfix17"' `
    -ExpectedCount 1 -Marker 'REMEDIATION_INSTALLER_PRODUCT_VERSION'
Set-ExactReplacement -Path $InstallerSource `
    -Old '!define BUILD_NAME "TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full"' `
    -New '!define BUILD_NAME "TNSuiteBridgeX_260820_v0.5-Build12-Hotfix17-Full"' `
    -ExpectedCount 1 -Marker 'REMEDIATION_INSTALLER_BUILD_NAME'
Set-ExactReplacement -Path $InstallerSource `
    -Old 'VIProductVersion "0.5.12.16"' `
    -New 'VIProductVersion "0.5.12.17"' `
    -ExpectedCount 1 -Marker 'REMEDIATION_INSTALLER_PE_PRODUCT_VERSION'
Set-ExactReplacement -Path $InstallerSource `
    -Old 'VIAddVersionKey /LANG=1033 "FileVersion" "0.5.12.16"' `
    -New 'VIAddVersionKey /LANG=1033 "FileVersion" "0.5.12.17"' `
    -ExpectedCount 1 -Marker 'REMEDIATION_INSTALLER_PE_FILE_VERSION'

# The copied QA must validate the release-stamped installer/wrapper, not the
# withdrawn public identity. Historical Hotfix16 regression tests remain intact.
Set-ExactReplacement -Path $ProductContentQa `
    -Old 'check(''Installer Build12-Hotfix16 identity'', ''!define PRODUCT_VERSION "0.5-Build12-Hotfix16"'' in installer and ''VIProductVersion "0.5.12.16"'' in installer)' `
    -New 'check(''Installer Build12-Hotfix17 release identity'', ''!define PRODUCT_VERSION "0.5-Build12-Hotfix17"'' in installer and ''VIProductVersion "0.5.12.17"'' in installer)' `
    -ExpectedCount 1 -Marker 'REMEDIATION_PRODUCT_QA_INSTALLER_IDENTITY'
Set-ExactReplacement -Path $ProductContentQa `
    -Old 'check(''PowerShell wrapper Build12-Hotfix16 identity'', "TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full" in wrapper)' `
    -New 'check(''PowerShell wrapper Build12-Hotfix17 release identity'', "TNSuiteBridgeX_260820_v0.5-Build12-Hotfix17-Full" in wrapper)' `
    -ExpectedCount 1 -Marker 'REMEDIATION_PRODUCT_QA_WRAPPER_IDENTITY'
Set-ExactReplacement -Path $Hotfix8Qa `
    -Old 'check(''Current Hotfix16 identity carrying Hotfix8 runtime fixes'', ''0.5-Build12-Hotfix16'' in installer and ''0.5.12.16'' in installer)' `
    -New 'check(''Current Hotfix17 release identity carrying Hotfix8 runtime fixes'', ''0.5-Build12-Hotfix17'' in installer and ''0.5.12.17'' in installer)' `
    -ExpectedCount 1 -Marker 'REMEDIATION_HOTFIX8_QA_RELEASE_IDENTITY'

# Verify the release-stamped copy contains no withdrawn public artifact name in
# the three files that control produced installer/portable identity.
foreach ($path in @($BuildPipeline, $BuildWrapper, $InstallerSource)) {
    $text = [System.IO.File]::ReadAllText($path)
    if ($text.Contains($LegacyBuildName)) {
        throw "WITHDRAWN_RELEASE_BUILD_NAME_REMAINS=$path"
    }
}
Write-Host 'WITHDRAWN_RELEASE_BUILD_NAME_REUSED=NO'
Write-Host 'REMEDIATION_RELEASE_IDENTITY_QA=PASS'

# The canonical checkout remains untouched. Only this disposable copy receives
# the governed release-build adaptations above.
$canonicalOldHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $RepoRoot 'scripts\build-filezilla-dark.sh')).Hash.ToLowerInvariant()
$adaptedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $BuildPipeline).Hash.ToLowerInvariant()
if ($canonicalOldHash -eq $adaptedHash) {
    throw 'RELEASE_BUILD_ADAPTER_NO_CHANGE'
}
Write-Host "CANONICAL_BUILD_PIPELINE_SHA256=$canonicalOldHash"
Write-Host "ADAPTED_BUILD_PIPELINE_SHA256=$adaptedHash"
Write-Host 'CANONICAL_SOURCE_MUTATION=NONE'

& powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $BuildWrapper
if ($LASTEXITCODE -ne 0) {
    throw "ADAPTED_WINDOWS_BUILD_FAILED=$LASTEXITCODE"
}

$ExpectedSetup = Join-Path $WorkDist "$ReleaseBuildName-Setup.exe"
$ExpectedPortable = Join-Path $WorkDist "$ReleaseBuildName.zip"
foreach ($artifact in @($ExpectedSetup, $ExpectedPortable)) {
    if (-not (Test-Path -LiteralPath $artifact) -or (Get-Item -LiteralPath $artifact).Length -le 0) {
        throw "ADAPTED_RELEASE_ARTIFACT_MISSING=$artifact"
    }
}

# The withdrawn Hotfix16 artifact names must not be copied into the canonical
# dist directory by the release adapter.
$WithdrawnSetup = Join-Path $WorkDist "$LegacyBuildName-Setup.exe"
$WithdrawnPortable = Join-Path $WorkDist "$LegacyBuildName.zip"
if ((Test-Path -LiteralPath $WithdrawnSetup) -or (Test-Path -LiteralPath $WithdrawnPortable)) {
    throw 'WITHDRAWN_RELEASE_ARTIFACT_RECREATED=YES'
}

New-Item -ItemType Directory -Force -Path $RepoDist | Out-Null
Copy-Item -LiteralPath $ExpectedSetup -Destination $RepoDist -Force
Copy-Item -LiteralPath $ExpectedPortable -Destination $RepoDist -Force

Write-Host 'WINDOWS_BUILD_ADAPTER_QA=PASS'
Write-Host 'CANONICAL_SOURCE_MUTATION=NONE'
Write-Host "ADAPTED_INSTALLER=$ExpectedSetup"
Write-Host "ADAPTED_PORTABLE=$ExpectedPortable"
Write-Host "RELEASE_PRODUCT_VERSION=$ReleaseProductVersion"
Write-Host "RELEASE_FILE_VERSION=$ReleaseFileVersion"
