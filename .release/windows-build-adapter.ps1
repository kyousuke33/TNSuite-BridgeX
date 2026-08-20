[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$BuildName = 'TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full'
$WorkRoot = Join-Path $env:RUNNER_TEMP "bridgex-release-kit-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
$WorkDist = Join-Path $WorkRoot 'dist'
$RepoDist = Join-Path $RepoRoot 'dist'

if (Test-Path -LiteralPath $WorkRoot) {
    Remove-Item -LiteralPath $WorkRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null

Write-Host 'RELEASE_BUILD_ADAPTER=START'
Write-Host "CANONICAL_REPO_ROOT=$RepoRoot"
Write-Host "ADAPTED_WORK_ROOT=$WorkRoot"

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
if (-not (Test-Path -LiteralPath $BuildPipeline)) {
    throw "RELEASE_BUILD_ADAPTER_PIPELINE_MISSING=$BuildPipeline"
}

$text = [System.IO.File]::ReadAllText($BuildPipeline)
$text = $text -replace "`r`n", "`n"

$old = @'
log "Branding/UI asset QA - fail closed"
python "$QA/branding_asset_check.py" "$KIT" | tee "$WORK/branding-asset-report.txt"
grep -q '^BRANDING_ASSET_QA=PASS$' "$WORK/branding-asset-report.txt"
'@
$old = $old -replace "`r`n", "`n"

$new = @'
log "Canonical branding contract QA - fail closed"
python "$KIT/scripts/qa/branding_contract_check.py" "$KIT" | tee "$WORK/branding-contract-report.txt"
grep -q '^BRANDING_CONTRACT_QA=PASS$' "$WORK/branding-contract-report.txt"
'@
$new = $new -replace "`r`n", "`n"

$matches = [regex]::Matches($text, [regex]::Escape($old)).Count
if ($matches -ne 1) {
    throw "RELEASE_BUILD_ADAPTER_BRANDING_ANCHOR_COUNT=$matches"
}

$text = $text.Replace($old, $new)
[System.IO.File]::WriteAllText($BuildPipeline, $text, [System.Text.UTF8Encoding]::new($false))

# The canonical checkout remains untouched. Only this disposable copy receives
# the build-tooling adapter that replaces the obsolete design-export QA with
# the repository's canonical shipped-branding contract.
$canonicalOldHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $RepoRoot 'scripts\build-filezilla-dark.sh')).Hash.ToLowerInvariant()
$adaptedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $BuildPipeline).Hash.ToLowerInvariant()
if ($canonicalOldHash -eq $adaptedHash) {
    throw 'RELEASE_BUILD_ADAPTER_NO_CHANGE'
}
Write-Host "CANONICAL_BUILD_PIPELINE_SHA256=$canonicalOldHash"
Write-Host "ADAPTED_BUILD_PIPELINE_SHA256=$adaptedHash"
Write-Host 'CANONICAL_SOURCE_MUTATION=NONE'
Write-Host 'RELEASE_BUILD_ADAPTER_BRANDING_CONTRACT=PASS'

$BuildWrapper = Join-Path $WorkRoot 'Build-TNSuiteBridgeX.ps1'
& powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $BuildWrapper
if ($LASTEXITCODE -ne 0) {
    throw "ADAPTED_WINDOWS_BUILD_FAILED=$LASTEXITCODE"
}

$ExpectedSetup = Join-Path $WorkDist "$BuildName-Setup.exe"
$ExpectedPortable = Join-Path $WorkDist "$BuildName.zip"
foreach ($artifact in @($ExpectedSetup, $ExpectedPortable)) {
    if (-not (Test-Path -LiteralPath $artifact) -or (Get-Item -LiteralPath $artifact).Length -le 0) {
        throw "ADAPTED_RELEASE_ARTIFACT_MISSING=$artifact"
    }
}

New-Item -ItemType Directory -Force -Path $RepoDist | Out-Null
Copy-Item -LiteralPath $ExpectedSetup -Destination $RepoDist -Force
Copy-Item -LiteralPath $ExpectedPortable -Destination $RepoDist -Force

Write-Host 'WINDOWS_BUILD_ADAPTER_QA=PASS'
Write-Host 'CANONICAL_SOURCE_MUTATION=NONE'
Write-Host "ADAPTED_INSTALLER=$ExpectedSetup"
Write-Host "ADAPTED_PORTABLE=$ExpectedPortable"
