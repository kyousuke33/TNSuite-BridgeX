[CmdletBinding()]
param(
    [string[]]$OutputDirectories = @('dist')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tag = 'v0.5.0-build12-hotfix25-rc1'
$asset = 'TNSuiteBridgeX_260822_v0.5-Build12-Hotfix25-Portable.zip'
$expectedZip = '1a2a752e21d8e698c0d1fe7839f94bfc2c0012451ba10a4b111d9bb8045d9299'
$expectedExe = '5ec55edad4b44dec1e9419776d9b892384c008458fc8f96c3183df8e41e4a640'
$legacyQaName = 'TNSuiteBridgeX_260820_v0.5-Build12-Hotfix17-Full.zip'
$workspace = Join-Path $env:RUNNER_TEMP 'BridgeX-Verified-RC1-LegacyQA'
if (Test-Path -LiteralPath $workspace) { Remove-Item -LiteralPath $workspace -Recurse -Force }
New-Item -ItemType Directory -Path $workspace -Force | Out-Null
$archive = Join-Path $workspace $asset

& gh release download $tag -R $env:GITHUB_REPOSITORY -p $asset -D $workspace --clobber
if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $archive -PathType Leaf)) {
    throw 'LEGACY_QA_VERIFIED_RC1_DOWNLOAD_FAILED'
}
$zipSha = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($zipSha -ne $expectedZip) {
    throw "LEGACY_QA_VERIFIED_RC1_ZIP_SHA256_FAIL actual=$zipSha"
}
$extracted = Join-Path $workspace 'unpacked'
Expand-Archive -LiteralPath $archive -DestinationPath $extracted -Force
$exe = Join-Path $extracted 'bin\BridgeX.exe'
if (!(Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'LEGACY_QA_RUNTIME_EXE_MISSING' }
$exeSha = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
if ($exeSha -ne $expectedExe) { throw "LEGACY_QA_RUNTIME_SHA256_FAIL actual=$exeSha" }
if (!$OutputDirectories -or $OutputDirectories.Count -lt 1) { throw 'LEGACY_QA_OUTPUT_DIRS_MISSING' }
foreach($dir in $OutputDirectories) {
    $targetDir = Join-Path $PWD $dir
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item -LiteralPath $archive -Destination (Join-Path $targetDir $legacyQaName) -Force
}
# GitHub Actions job environment binding is tested against the exact archive bytes above.
if (![string]::IsNullOrEmpty($env:GITHUB_ENV)) {
    [IO.File]::AppendAllText($env:GITHUB_ENV, "EXPECTED_BRIDGEX_SHA256=$exeSha`n", [Text.UTF8Encoding]::new($false))
}
Write-Host 'LEGACY_QA_RUNTIME_SOURCE=PINNED_PUBLIC_RC1'
Write-Host 'LEGACY_QA_RUNTIME_IS_MAIN_BUILD_AUTHORITY=NO'
Write-Host "LEGACY_QA_PORTABLE_SHA256=$zipSha"
Write-Host "EXPECTED_BRIDGEX_SHA256=$exeSha"
Write-Host 'LEGACY_QA_RUNTIME_PROVENANCE=PASS_EXACT_HASH'
