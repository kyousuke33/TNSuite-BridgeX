[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][ValidatePattern('^[0-9A-Fa-f]{64}$')][string]$ExpectedBridgeXSha256
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$hotfix24 = Join-Path $PSScriptRoot 'build-wix-installer-hotfix24.ps1'
if (-not (Test-Path -LiteralPath $hotfix24)) { throw "HOTFIX25_BASE_BUILDER_MISSING=$hotfix24" }

# Hotfix25 deliberately reuses the proven Hotfix24 WiX implementation and
# changes only product identity/version. The classic theme stays byte-for-byte
# the same; the runtime difference is supplied by the source overlay.
$driver = Get-Content -LiteralPath $hotfix24 -Raw -Encoding UTF8
$driver = $driver.Replace('Hotfix24', 'Hotfix25')
$driver = $driver.Replace('HOTFIX24', 'HOTFIX25')
$driver = $driver.Replace('0.5.1224', '0.5.1225')
$driver = $driver.Replace('0.5.12.24', '0.5.12.25')
$driver = $driver.Replace('260821', '260822')

# Keep using the proven Hotfix24 theme/localization assets instead of creating
# cosmetic duplicates solely for a runtime startup correction.
$driver = $driver.Replace("'BridgeX.Hotfix25.Theme.xml'", "'BridgeX.Hotfix24.Theme.xml'")
$driver = $driver.Replace("'BridgeX.Hotfix25.Theme.wxl'", "'BridgeX.Hotfix24.Theme.wxl'")

$themeAnchor = '$script = $script.Replace(''Hotfix23'', ''Hotfix25'')'
if (-not $driver.Contains($themeAnchor)) { throw 'HOTFIX25_THEME_REUSE_ANCHOR_MISSING' }
$themeInjection = $themeAnchor + "`n" +
    '$script = $script.Replace(''BridgeX.Hotfix25.Theme.xml'', ''BridgeX.Hotfix24.Theme.xml'')' + "`n" +
    '$script = $script.Replace(''BridgeX.Hotfix25.Theme.wxl'', ''BridgeX.Hotfix24.Theme.wxl'')'
$driver = $driver.Replace($themeAnchor, $themeInjection)

$temp = Join-Path $PSScriptRoot ".BridgeX-Hotfix25-Adapter-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"
try {
    [IO.File]::WriteAllText($temp, $driver, [Text.UTF8Encoding]::new($false))
    & pwsh.exe -NoLogo -NoProfile -File $temp `
        -PortableZip $PortableZip `
        -OutputDirectory $OutputDirectory `
        -ExpectedBridgeXSha256 $ExpectedBridgeXSha256
    if ($LASTEXITCODE -ne 0) { throw "HOTFIX25_WIX_BUILD_FAILED=$LASTEXITCODE" }
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
